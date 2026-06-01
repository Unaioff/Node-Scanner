from scapy.all import IP, ICMP, sr1
import socket
import ipaddress
import json


from ui import MapSection



# OBTENER IP HOST - Se conecta al dns de google y coge la interfaz de red con la que se conecta 
def SelfHost():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


# Esto almacenara todos los Obj de clase Nodo
Nodos = []


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
    

# CREAR FUNCION PARA COMPROBAR SI EXISTE
# TENER EN CUENTA LA MAC A LA HORA DE CREAR Y ACTUALIZAR NODOS 
def Existe(ip): 
    pass





# Crea un nuevo Nodo 
def CrearNodo(data):

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
        id=len(Nodos),
        ip=data["ip"],
        mac=data["mac"],
        mask=data["mask"],
        x=PromedioX,
        y=PromedioY
    )

    Nodos.append(NuevoNodo)

    return NuevoNodo






def ActualizarNodo(ip, data):

    for nodo in Nodos:
        if nodo.ip == ip:

            if "ip" in data: nodo.ip = data["ip"]
            if "mac" in data: nodo.mac = data["mac"]
            if "mask" in data: nodo.mask = data["mask"]
            if "x" in data: nodo.x = data["x"]
            if "y" in data: nodo.y = data["y"]

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
    if Online != True and CONFIG["scan_options"]["arp"] == True:
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


# Herramienta para seguir las rutas de conexion 
def TraceRoute(Ip):
    pass



    

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
    def __init__(self, NodoIP="", NodoMAC="", NodoMask="255.255.255.0", NodoPosX=0, NodoPosY=0):
        
        # [ DATOS ESENCIALES NODOS ] 
        self.NodoID = ""
        self.NodoIP = NodoIP
        self.NodoMAC = NodoMAC
        self.NodoMask = NodoMask
        
        # [  DATOS DE DIBUJO NODO ] 
        self.NodoPosX = NodoPosX
        self.NodoPosY = NodoPosY


        # [ DATOS EXTRA NODOS ] 
        self.NodoIsOnline = False
        self.NodoHostname = ""
        self.NodoOS = ""

        self.NodoServices = []
        self.NodoConnections = [] 

        self.NodoIsHost = (SelfHost == self.ip)




    # [ Facil conversion a JSON ]
    def Data(self):
        return {
            "ID": self.NodoID,
            "IP": self.NodoIP,
            "MAC": self.NodoMAC,
            "Mask": self.NodoMask,

            "PositionX": self.NodoX,
            "PositionY": self.NodoY,
            
            "Hostname": self.NodoHostname,
            "OS": self.NodoOS,
            "Services": self.NodoServices,
            "Connections": self.NodoConnections,

            "Online": self.NodoIsOnline,
            "IsHost": self.NodoIsHost

        }

    
    # Esto es lo que dibujara los nodos y las conexiones
    def DrawNode(self):
        x = self.x
        y = self.y
        if self.online: 
            if SelfHost == self.ip:
                MapSection.nodo_canvas.create_oval(x-25, y-25, x+25, y+25, fill="#56d054", outline="#1a831c", width=3)
            else:
                MapSection.nodo_canvas.create_oval(x-25, y-25, x+25, y+25, fill="#549cd0", outline="#1a5b83", width=3)
        else: 
            MapSection.nodo_canvas.create_oval(x-25, y-25, x+25, y+25, fill="#d05454", outline="#831a1a", width=3)
        MapSection.nodo_canvas.create_text(x, y+30, text=self.ip, fill="white", font=("Arial", 12, "bold"))

    


