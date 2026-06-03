from scapy.all import IP, ICMP, sr1
import socket
import ipaddress
import json


# [ VARIABLES ]


# -- Almacena Obj de Nodo --
Nodos = []

IDNodoCount = 0 






# OBTENER IP HOST - Se conecta al dns de google y coge la interfaz de red con la que se conecta 
def SelfHost():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]



# Verifica que sea una ip
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

    global IDNodoCount

    NodosX = 0
    NodosY = 0

    for nodo in Nodos:
        NodosX += nodo.x
        NodosY += nodo.y

    if len(Nodos) == 0:
        PromedioX = 20
        PromedioY = 20
    else:
        PromedioX = NodosX / len(Nodos)
        PromedioY = NodosY / len(Nodos)


    NuevoNodo = Nodo(
        NodoID = IDNodoCount,
        NodoIP = data["IP"],
        NodoMAC = data["MAC"],
        NodoMask = data["Mask"],
        NodoPosX = PromedioX,
        NodoPosY = PromedioY
    )

    IDNodoCount += 1 
    Nodos.append(NuevoNodo)

    return NuevoNodo





def ActualizarNodo(ip, data):

    for nodo in Nodos:
        if nodo.NodoIP == ip:

            if "ip" in data: nodo.NodoIP = data["ip"]
            if "mac" in data: nodo.NodoMAC = data["mac"]
            if "mask" in data: nodo.NodoMask = data["mask"]
            if "os" in data: nodo.NodoOS = data["os"]

            return nodo

    return None



with open("config.json") as i:
    CONFIG = json.load(i)



# Realiza un escaneo de Nodo simple a partir de la configuracion
def SimpleNodeScan(DestIP):

    Data=[]
     
    # ICMP
    if CONFIG["scan_options"]["icmp"]:
        ICMPRequest = IP(dst=DestIP) / ICMP()
        response = sr1(ICMPRequest, timeout=2, verbose=0)
        if response:
            Online = True
    

    # ARP 
    if not Online or CONFIG["scan_options"]["arp"] == True:
        # Escaneo ARP
        pass
        
        

    # OS



    # PORTS


    # CONECTIONS


    # MASK


    # MAC


    
    return Data
    

# Realiza un escaneo de Nodo multiple a partir de la configuracion
#  Como este solo se usa en el Scaneo normal esta funcion crea o actualiza ya los nodos 
def NetworkNodeScan(NetworkIp):
    NetworkIp = NetworkIp.split("/")





    

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
    def __init__(self, NodoID, Canvas, NodoPosX, NodoPosY, NodoIP="", NodoMAC="", NodoMask="255.255.255.0"):
        
        # [ DATOS ESENCIALES NODOS ] 
        self.NodoIP = NodoIP
        self.NodoMAC = NodoMAC
        self.NodoMask = NodoMask
        
        # [  DATOS DE DIBUJO NODO ] 
        self.Canvas = Canvas
        
        self.NodoPosX = NodoPosX
        self.NodoPosY = NodoPosY

        self.NodoID = NodoID

        # [ DATOS EXTRA NODOS ] 
        self.NodoIsOnline = False
        self.NodoHostname = ""
        self.NodoOS = ""

        self.NodoServices = []
        self.NodoConnections = [] 

        self.NodoIsHost = (SelfHost() == self.NodoIP)


        # [ DIBUJAR NODO AL INICIO ]        

        if self.NodoIsOnline:
            if self.NodoIsHost:
                self.NodoOvalo = self.Canvas.create_oval(
                    self.NodoPosX-25, self.NodoPosY-25,
                    self.NodoPosX+25, self.NodoPosY+25,
                    fill="#56d054", outline="#1a831c", width=3,
                    tags=(self.NodoID, "nodo")
                )
            else:
                self.NodoOvalo = self.Canvas.create_oval(
                    self.NodoPosX-25, self.NodoPosY-25,
                    self.NodoPosX+25, self.NodoPosY+25,
                    fill="#549cd0", outline="#1a5b83", width=3,
                    tags=(self.NodoID, "nodo")
                )
        else:
            self.NodoOvalo = self.Canvas.create_oval(
                self.NodoPosX-25, self.NodoPosY-25,
                self.NodoPosX+25, self.NodoPosY+25,
                fill="#d05454", outline="#831a1a", width=3,
                tags=(self.NodoID, "nodo")
            )

        self.NodoTexto = self.Canvas.create_text(
            self.NodoPosX,
            self.NodoPosY+30,
            text=self.NodoIP,
            fill="white",
            font=("Arial", 12, "bold"),
            tags=(self.NodoID, "nodo")
        )


    # [ Facil conversion a JSON ]
    def Data(self):
        return {

            "IP": self.NodoIP,
            "MAC": self.NodoMAC,
            "Mask": self.NodoMask,

            "PositionX": self.NodoPosX,
            "PositionY": self.NodoPosY,
            
            "Hostname": self.NodoHostname,
            "OS": self.NodoOS,
            "Services": self.NodoServices,
            "Connections": self.NodoConnections,

            "Online": self.NodoIsOnline,
            "IsHost": self.NodoIsHost

        }

    def MoveNode(self):
        pass








def icmp_scan(ip):
    ICMPRequest = IP(dst=ip) / ICMP()
    response = sr1(ICMPRequest, timeout=2, verbose=0)
    if response: return True
    else: return False


def arp_scan(ip):
    pass


Nodes = []

def update_node(node,data):
    
        


def get_status(ip):
    return icmp_scan(ip) or arp_scan(ip)

def GetMAC(ip):
    pass




def ScanIP(InputedIP):
    if ValidIp(InputedIP):
        if not "/" in InputedIP:
            #ESCANEO DE IP
            
            inputed_ip_online = get_status(InputedIP)

            if inputed_ip_online:
                InputedIP_MAC = GetMAC(InputedIP)
                
                for nodo in Nodos:
                    if nodo.NodoMAC == InputedIP_MAC:
                        update_node(nodo, )



        








        else:
            #ESCANEO DE RED
            pass




    else: 
        print("ERRROR") 
        # MENSAJE DE ERROR DE WINDOW