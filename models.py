from network import GetSelfIp
import random


IdCounter = 0
SelfIp = None


def NextId():
    global IdCounter
    IdCounter += 1
    return IdCounter


def GetCachedSelfIp():
    global SelfIp
    if SelfIp is None:
        SelfIp = GetSelfIp()
    return SelfIp


# ================= #
#     CLASE NODO
# ================= #

class Node:

    def __init__(self, Ip, Mac="", Online=False, Hostname="", Os="", X=0, Y=0):

        self.ip       = Ip
        self.mac      = Mac
        self.mask     = "255.255.255.0"
        self.online   = Online
        self.hostname = Hostname
        self.os       = Os
        self.services    = []
        self.connections = []

        self.x = X
        self.y = Y

        self.id = NextId()

        self.canvas_oval_id = None
        self.canvas_text_id = None

    @property
    def is_host(self):
        SelfIp = GetCachedSelfIp()
        return self.ip == SelfIp or self.ip in ("127.0.0.1", "::1")

    def Update(self, Data):
        for Key, Value in Data.items():
            if hasattr(self, Key):
                setattr(self, Key, Value)

    def ToDict(self):
        return {
            "id":          self.id,
            "ip":          self.ip,
            "mac":         self.mac,
            "mask":        self.mask,
            "x":           self.x,
            "y":           self.y,
            "hostname":    self.hostname,
            "os":          self.os,
            "online":      self.online,
            "services":    self.services,
            "connections": self.connections,
            "is_host":     self.is_host,
        }

    @classmethod
    def FromScan(cls, Data, X=0, Y=0):
        return cls(
            Ip       = Data.get("ip", ""),
            Mac      = Data.get("mac") or "",
            Online   = Data.get("online", False),
            Hostname = Data.get("hostname", ""),
            Os       = Data.get("os", ""),
            X        = X,
            Y        = Y,
        )


# ======================== #
#     CLASE NODESTORE
# ======================== #

# Almacena todos los nodos y los gestiona

class NodeStore:

    def __init__(self):
        self.nodes = []

    def GetByIp(self, Ip):
        for Node_ in self.nodes:
            if Node_.ip == Ip:
                return Node_
        return None

    def GetByMac(self, Mac):
        for Node_ in self.nodes:
            if Node_.mac == Mac:
                return Node_
        return None

    def Exists(self, Ip):
        return self.GetByIp(Ip) is not None

    def NextPosition(self):
        if not self.nodes:
            return 300, 300

        AvgX = sum(N.x for N in self.nodes) / len(self.nodes)
        AvgY = sum(N.y for N in self.nodes) / len(self.nodes)

        OffsetX = random.randint(-120, 120)
        OffsetY = random.randint(-120, 120)

        return AvgX + OffsetX, AvgY + OffsetY

    def Add(self, ScanData):
        X, Y = self.NextPosition()
        NewNode = Node.FromScan(ScanData, X=X, Y=Y)
        self.nodes.append(NewNode)
        return NewNode

    def UpdateIp(self, Ip, ScanData):
        Node_ = self.GetByIp(Ip)
        if Node_:
            Node_.Update(ScanData)
        return Node_

    def AddOrUpdate(self, ScanData):
        Ip = ScanData.get("ip", "")
        Existing = self.GetByIp(Ip)

        if Existing:
            Existing.Update(ScanData)
            return Existing, False

        NewNode = self.Add(ScanData)
        return NewNode, True

    def Remove(self, Ip):
        Node_ = self.GetByIp(Ip)
        if Node_:
            self.nodes.remove(Node_)
            return True
        return False