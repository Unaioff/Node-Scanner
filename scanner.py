from scapy.all import IP, ICMP, sr1
import socket
import ipaddress
import json


with open("config.json") as i:
    CONFIG = json.load(i)


# OBTENER IP HOST - Se conecta a google y coge la interfaz de red con la que se conecta 
def SelfHost():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


# Esto almacenara todos los Obj de clase Nodo
Nodos = []


# Verifica que sea un ip
def ValidIp(InputedText):
    try:
        ipaddress.ip_address(InputedText)
        return True
    except ValueError:
        pass

    try:
        ipaddress.ip_network(InputedText, strict=False)
        return True
    except ValueError:
        return False
    

# Crea un nuevo Nodo 
def CrearNodo(data):
    NuevoNodo = Nodo(id=len(Nodos),)
    Nodos.append(NuevoNodo)


# Actualiza un nodo ya existente
def ActualizarNodo(data):
    pass



# Realiza un escaneo de Nodo simple a partir de la configuracion
def SimpleNodeScan(HostIp):
    print("")
    

# Realiza un escaneo de Nodo multiple a partir de la configuracion
def NetworkNodeScan(NetworkIp):
    NetworkIp = NetworkIp.split("/")


# Herramienta para seguir las rutas de conexion 
def TraceRoute(Ip):
    pass


# ONLY ICMP STATUS ( Me da la english vena a veces) Escaneo de nodo simple en pañales (Esta de referencia)
def Ping(DestIP):
    ICMPRequest = IP(dst=DestIP) / ICMP()
    response = sr1(ICMPRequest, timeout=2, verbose=0)
    if response: 
        return True
    else: 
        return False
    

# ONLY ICMP DISCOVER HOST - Escaneo de nodo multiple en pañales (Esta de referencia)
def DiscoverHosts(network):
    #Scans a network for active hosts using ICMP Echo Requests.
    network_obj = ipaddress.ip_network(network)
    active_hosts = []

    for ip_address in network_obj.hosts(): 
        ip_str = str(ip_address)
        icmp_request = IP(dst=ip_str) / ICMP()
        response = sr1(icmp_request, timeout=1, verbose=0)

        if response:
            active_hosts.append(ip_str)
            print(f"Host {ip_str} is up.")
        else:
            print(f"Host {ip_str} is down.")

    return active_hosts





class Nodo():
    def __init__(self, id, hostname="", ip="", mac="", mask="255.255.255.0"):
        
        # [ DATOS NODOS ] 
        self.id = id
        self.hostname = hostname
        self.ip = ip
        self.mac = mac

        self.online = False
        self.mask = mask

        self.os = None,
        self.services = []

        self.connections = [] 

        # [  POSITION NODOS ] 
        self.x = 0
        self.y = 0 


    # [ Facil conversion a JSON ]
    def Data(self):
        return {
            "ID": self.id,
            "IP": self.ip,
            "Hostname": self.hostname,
            "MAC": self.mac,
            "Online": self.online,
            "Mask": self.mask,
            "OS": self.os,
            "Services": self.services,
            "Connections": self.connections,
            "PositionX": self.x,
            "PositionY": self.y
        }

    
    # Esto es lo que dibujara los nodos y las conexiones
    def DrawNode(self):
        x = self.x
        y = self.y
        if self.online: 
            if SelfHost == self.ip:
                self.nodo_canvas.create_oval(x-25, y-25, x+25, y+25, fill="#56d054", outline="#1a831c", width=3)
            else:
                self.nodo_canvas.create_oval(x-25, y-25, x+25, y+25, fill="#549cd0", outline="#1a5b83", width=3)
        else: 
            self.nodo_canvas.create_oval(x-25, y-25, x+25, y+25, fill="#d05454", outline="#831a1a", width=3)
        self.nodo_canvas.create_text(x, y+30, text=self.ip, fill="white", font=("Arial", 12, "bold"))

    


MiPC = Nodo()
print(MiPC.Data())

