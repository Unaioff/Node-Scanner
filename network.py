from scapy.all import IP, ICMP, ARP, Ether, TCP, sr1, srp, sr
import socket
import ipaddress
import sys

# WINDOWS ERROR ( se necesita Npcap instalado )
ArpAvailable = sys.platform != "win32"
try:
    if sys.platform == "win32":
        from scapy.arch.windows import get_windows_if_list
        ArpAvailable = True
except Exception:
    ArpAvailable = False


def GetSelfIp():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as S:
        S.connect(("8.8.8.8", 80))
        return S.getsockname()[0]


def IsValidIp(Text):
    try:
        ipaddress.ip_address(Text)
        return True
    except ValueError:
        pass
    try:
        ipaddress.ip_network(Text, strict=False)
        return True
    except ValueError:
        return False


def IsNetwork(Text):
    return "/" in Text


# ===[ ESCANEO ICMP ] ===

def ScanIcmp(Ip, Timeout=2):
    Pkt = IP(dst=Ip) / ICMP()
    Response = sr1(Pkt, timeout=Timeout, verbose=0)
    return Response is not None


# ===[ ESCANEO ARP ] ===
# Devuelve la mac si Online, si no None

def ScanArpIp(Ip, Timeout=2):
    if not ArpAvailable:
        print("[ARP] No disponible en este sistema (instala Npcap en Windows)")
        return None
    try:
        Pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=Ip)
        Result = srp(Pkt, timeout=Timeout, verbose=0)[0]
        if Result:
            return Result[0][1].hwsrc
    except RuntimeError as E:
        print(f"[ARP] Error: {E}")
    return None

# ===[ ESCANEO ARP NETWORK ] ===
# Devuelve la mac si Online, si no None

def ScanArpNetwork(Network, Timeout=2):
    if not ArpAvailable:
        print("[ARP] No disponible en este sistema (instala Npcap en Windows)")
        return []
    try:
        Pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=Network)
        Answered, _ = srp(Pkt, timeout=Timeout, verbose=0)
        return [{"ip": Rcv.psrc, "mac": Rcv.hwsrc} for _, Rcv in Answered]
    except RuntimeError as E:
        print(f"[ARP] Error: {E}")
        return []


# ===[ ESTADO DEL HOST ] ===

def GetHostStatus(Ip):
    if ScanIcmp(Ip):
        return True
    Mac = ScanArpIp(Ip)
    return Mac is not None


# ===[ PORT SCANNING SYN TCP ] ===
# Servicios comunes

CommonPorts = {
    21:   "FTP",
    22:   "SSH",
    23:   "Telnet",
    25:   "SMTP",
    53:   "DNS",
    80:   "HTTP",
    110:  "POP3",
    135:  "RPC",
    139:  "NetBIOS",
    143:  "IMAP",
    443:  "HTTPS",
    445:  "SMB",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    6379: "Redis",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
    27017:"MongoDB",
}

# ESCANEO SYN TCP 
# devuelve lista con puerto/servicio abiertos 
# Futuro: Gestionar Filtered, Open, Closed

def ScanPorts(Ip, Ports=None, Timeout=2):
    if Ports is None:
        Ports = list(CommonPorts.keys())

    OpenPorts = []

    Pkts = [IP(dst=Ip) / TCP(dport=Port, flags="S") for Port in Ports]
    Answered, _ = sr(Pkts, timeout=Timeout, verbose=0)


    # SYN-ACK (flags=0x12) significa puerto abierto
    for Sent, Received in Answered:
        if Received.haslayer(TCP) and Received[TCP].flags == 0x12:
            Port = Sent[TCP].dport
            # Enviamos RST para no dejar la conexión a medias
            sr1(IP(dst=Ip) / TCP(dport=Port, flags="R"), timeout=1, verbose=0)
            ServiceName = CommonPorts.get(Port, str(Port))
            OpenPorts.append(f"{Port}/{ServiceName}")

    return OpenPorts


# ===[ DETECCIÓN DE SISTEMA OPERATIVO ] ===

# TTL inicial típico por sistema operativo

TtlMap = [
    (64,  "Linux"),
    (128, "Windows"),
    (255, "Cisco IOS / Solaris"),
    (254, "Cisco IOS"),
]

# DETECTAR SISTEMA OPERATIVO
# ESTIMACION!!
def DetectOs(Ip, Timeout=2):
    Pkt = IP(dst=Ip) / ICMP()
    Response = sr1(Pkt, timeout=Timeout, verbose=0)

    if Response is None or not Response.haslayer(IP):
        return ""

    Ttl = Response[IP].ttl

    # El TTL decrece en cada salto y redondeo al valor con mas sentido
    # max 30 saltos de distancia
    BestMatch = ""
    BestDiff  = 999
    for StdTtl, OsName in TtlMap:
        Diff = StdTtl - Ttl
        if 0 <= Diff < BestDiff:
            BestDiff  = Diff
            BestMatch = OsName

    return BestMatch


# ===[ TRACEROUTE ] ===
# No tocar, se rompe facil

def Traceroute(ip, max_hops=20, timeout=2):
    path = []

    for ttl in range(1, max_hops + 1):
        pkt = IP(dst=ip, ttl=ttl) / ICMP()

        try:
            response = sr1(pkt, timeout=timeout, verbose=0)
        except Exception:
            path.append(None)
            continue

        if response is None:
            path.append(None)
            continue

        hop_ip = response.src
        path.append(hop_ip)

        if response.haslayer(ICMP):
            icmp = response.getlayer(ICMP)

            # Destino Alcanzado
            if icmp.type == 0:
                break

            # Destino no se puede alcanzar 
            if icmp.type == 3:
                break
    path.reverse()
    return path


# ===[ ESCANEO COMPLETO DE UNA IP ] ===

def ScanSingleIp(Ip):
    Data = {
        "ip": Ip,
        "mac": None,
        "online": False,
        "hostname": "",
        "os": "",
        "services": [],
        "connections": [],
    }

    # Si es loopback o la propia IP, siempre está online
    SelfIp = GetSelfIp()
    if Ip in ("127.0.0.1", "::1") or Ip == SelfIp:
        Data["online"] = True
    else:
        Online = ScanIcmp(Ip)
        Data["online"] = Online

        Mac = ScanArpIp(Ip)
        if Mac:
            Data["mac"] = Mac
            Data["online"] = True

    # HOSTNAME
    try:
        Data["hostname"] = socket.gethostbyaddr(Ip)[0]
    except (socket.herror, socket.gaierror):
        Data["hostname"] = ""

    # ESCANEAMOS PUERTOS, OS Y CONEXIONES SI ESTA ONLINE ( 2nd scan ) 
    if Data["online"]:
        Data["services"]    = ScanPorts(Ip)
        Data["os"]          = DetectOs(Ip)
        Data["connections"] = [H for H in Traceroute(Ip) if H is not None]

    return Data


# ===[ ESCANEO DE RED COMPLETA ] ===

def ScanNetwork(NetworkCidr):
    Results = []

    ArpHosts = ScanArpNetwork(NetworkCidr)
    FoundIps = {H["ip"] for H in ArpHosts}

    for Host in ArpHosts:
        Entry = {
            "ip": Host["ip"],
            "mac": Host["mac"],
            "online": True,
            "hostname": "",
            "os": "",
            "services": [],
        }
        try:
            Entry["hostname"] = socket.gethostbyaddr(Host["ip"])[0]
        except socket.herror:
            pass
        Results.append(Entry)

    Net = ipaddress.ip_network(NetworkCidr, strict=False)
    for Addr in Net.hosts():
        IpStr = str(Addr)
        if IpStr not in FoundIps:
            if ScanIcmp(IpStr, Timeout=1):
                Entry = {
                    "ip": IpStr,
                    "mac": None,
                    "online": True,
                    "hostname": "",
                    "os": "",
                    "services": [],
                }
                try:
                    Entry["hostname"] = socket.gethostbyaddr(IpStr)[0]
                except socket.herror:
                    pass
                Results.append(Entry)

    return Results




def GetGateway():
    import subprocess
    try:
        output = subprocess.check_output(["ip", "route"], text=True)
        for line in output.splitlines():
            if line.startswith("default"):
                return line.split()[2]
    except Exception:
        return None
    return None