import customtkinter as ctk
import tkinter as tk
from models import Node


# VARIABLES, MAS BIEN CONSTANTES
ColorEdge    = "#4a4a6a"
ColorEdgeHop = "#7a7aaa"

ColorHost    = {"fill": "#56d054", "outline": "#1a831c"}
ColorOnline  = {"fill": "#549cd0", "outline": "#1a5b83"}
ColorOffline = {"fill": "#d05454", "outline": "#831a1a"}

ColorGridMinor = "#2a2a3e"
ColorGridMajor = "#33334d"
GridStep       = 40
GridMajorEvery = 5

NodeRadius = 25
FontIp     = ("Arial", 11, "bold")

ZoomMin = 0.1
ZoomMax = 5.0


class MapCanvas(ctk.CTkFrame):

    # REGISTROS DE NODES Y EDGES 
    NodeRegistry = {}
    EdgeRegistry = {}   

    def __init__(self, Master, OnNodeClick=None, **Kwargs):
        super().__init__(Master, **Kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.Canvas = tk.Canvas(self, bg="#1e1e2e", highlightthickness=0)
        self.Canvas.grid(row=0, column=0, sticky="nsew")

        # VARIABBLES DE POSICIONAMIENTO
        self.Scale   = 1.0
        self.OffsetX = 0.0
        self.OffsetY = 0.0

        self.PanStartX  = 0
        self.PanStartY  = 0
        self.PanOriginX = 0.0
        self.PanOriginY = 0.0

        self.DragNode     = None
        self.DragStartSx  = 0
        self.DragStartSy  = 0
        self.DragNodeWx0  = 0.0
        self.DragNodeWy0  = 0.0


        # [ INPUT KEYBINDS ]

        self.OnNodeClick = OnNodeClick

        self.Canvas.bind("<ButtonPress-1>",   self.OnPress)
        self.Canvas.bind("<B1-Motion>",       self.OnMotion)
        self.Canvas.bind("<ButtonRelease-1>", self.OnRelease)
        self.Canvas.bind("<MouseWheel>",      self.OnZoom)
        self.Canvas.bind("<Button-4>",        self.OnZoom)
        self.Canvas.bind("<Button-5>",        self.OnZoom)
        self.Canvas.bind("<Configure>",       lambda E: self.RedrawGrid())


    
    def WorldToScreen(self, Wx, Wy):
        return Wx * self.Scale + self.OffsetX, Wy * self.Scale + self.OffsetY

    def ScreenToWorld(self, Sx, Sy):
        return (Sx - self.OffsetX) / self.Scale, (Sy - self.OffsetY) / self.Scale


    # [ GENERAR GRID ]

    def RedrawGrid(self):
        self.Canvas.delete("grid")
        W = self.Canvas.winfo_width()
        H = self.Canvas.winfo_height()
        if W < 2 or H < 2:
            return

        StepS = GridStep * self.Scale
        if StepS < 4:
            return

        X0World = -self.OffsetX / self.Scale
        Y0World = -self.OffsetY / self.Scale

        FirstCol = int(X0World / GridStep)
        FirstRow = int(Y0World / GridStep)

        Col = FirstCol - 1
        while True:
            Sx, _ = self.WorldToScreen(Col * GridStep, 0)
            if Sx > W:
                break
            IsMajor = (Col % GridMajorEvery == 0)
            Color = ColorGridMajor if IsMajor else ColorGridMinor
            self.Canvas.create_line(Sx, 0, Sx, H, fill=Color, tags="grid")
            Col += 1

        Row = FirstRow - 1
        while True:
            _, Sy = self.WorldToScreen(0, Row * GridStep)
            if Sy > H:
                break
            IsMajor = (Row % GridMajorEvery == 0)
            Color = ColorGridMajor if IsMajor else ColorGridMinor
            self.Canvas.create_line(0, Sy, W, Sy, fill=Color, tags="grid")
            Row += 1

        self.Canvas.tag_lower("grid")


    # [ NODE RENDERING ]

    def PlaceNodeItems(self, NodeObj):
        Sx, Sy = self.WorldToScreen(NodeObj.x, NodeObj.y)
        R = NodeRadius * self.Scale

        if NodeObj.canvas_oval_id is not None:
            self.Canvas.coords(NodeObj.canvas_oval_id, Sx - R, Sy - R, Sx + R, Sy + R)
            self.Canvas.coords(NodeObj.canvas_text_id, Sx, Sy + R + 10 * self.Scale)

    def DrawNode(self, NodeObj):
        Colors = self.GetNodeColors(NodeObj)
        Sx, Sy = self.WorldToScreen(NodeObj.x, NodeObj.y)
        R = NodeRadius * self.Scale
        Tag = f"node_{NodeObj.id}"

        OvalId = self.Canvas.create_oval(
            Sx - R, Sy - R, Sx + R, Sy + R,
            fill=Colors["fill"],
            outline=Colors["outline"],
            width=3,
            tags=(Tag, "node"),
        )
        TextId = self.Canvas.create_text(
            Sx, Sy + R + 10 * self.Scale,
            text=NodeObj.ip,
            fill="white",
            font=FontIp,
            tags=(Tag, "node"),
        )

        NodeObj.canvas_oval_id = OvalId
        NodeObj.canvas_text_id = TextId
        MapCanvas.NodeRegistry[Tag] = NodeObj

    def UpdateNode(self, NodeObj):
        if NodeObj.canvas_oval_id is None:
            self.DrawNode(NodeObj)
            return
        Colors = self.GetNodeColors(NodeObj)
        self.Canvas.itemconfig(NodeObj.canvas_oval_id, fill=Colors["fill"], outline=Colors["outline"])

    def RemoveNode(self, NodeObj):
        Tag = f"node_{NodeObj.id}"
        self.Canvas.delete(Tag)

    def RedrawAllNodes(self):
        Seen = set()
        for ItemId in self.Canvas.find_withtag("node"):
            Tags = self.Canvas.gettags(ItemId)
            NodeTag = next((T for T in Tags if T.startswith("node_") and T != "node"), None)
            if NodeTag and NodeTag not in Seen:
                Seen.add(NodeTag)
                NodeObj = self.GetNodeByTag(NodeTag)
                if NodeObj:
                    self.PlaceNodeItems(NodeObj)

    def GetNodeByTag(self, Tag):
        return MapCanvas.NodeRegistry.get(Tag)


    # ===================== [ CONEXIONES ] =====================

    def _EdgeKey(self, NodeA, NodeB):
        return (min(NodeA.id, NodeB.id), max(NodeA.id, NodeB.id))

    # RENDERIZA LA CONEXION ENTRE DOS NODOS | ASEGURARSE QUE NO REPITA
    def DrawEdge(self, NodeA, NodeB, IsHop=True):
        Key = self._EdgeKey(NodeA, NodeB)
        if Key in MapCanvas.EdgeRegistry:
            return

        Ax, Ay = self.WorldToScreen(NodeA.x, NodeA.y)
        Bx, By = self.WorldToScreen(NodeB.x, NodeB.y)
        Color  = ColorEdgeHop if IsHop else ColorEdge

        LineId = self.Canvas.create_line(
            Ax, Ay, Bx, By,
            fill=Color, width=2, dash=(6, 3) if IsHop else None,
            tags=("edge",),
        )
        MapCanvas.EdgeRegistry[Key] = LineId
        
        # LAYERS
        self.Canvas.tag_lower("edge")
        self.Canvas.tag_raise("node")

    # ELIMINAR CONEXIONES
    def RemoveEdge(self, NodeA, NodeB):
        Key = self._EdgeKey(NodeA, NodeB)
        LineId = MapCanvas.EdgeRegistry.pop(Key, None)
        if LineId:
            self.Canvas.delete(LineId)

    # REDIBUJAR LAS CONEXIONES
    def RedrawAllEdges(self):
        for (IdA, IdB), LineId in MapCanvas.EdgeRegistry.items():
            TagA = f"node_{IdA}"
            TagB = f"node_{IdB}"
            NodeA = self.GetNodeByTag(TagA)
            NodeB = self.GetNodeByTag(TagB)
            if NodeA and NodeB:
                Ax, Ay = self.WorldToScreen(NodeA.x, NodeA.y)
                Bx, By = self.WorldToScreen(NodeB.x, NodeB.y)
                self.Canvas.coords(LineId, Ax, Ay, Bx, By)

    # Colores | Si, literalmente solo colores

    @staticmethod
    def GetNodeColors(NodeObj):
        if NodeObj.is_host:
            return ColorHost
        if NodeObj.online:
            return ColorOnline
        return ColorOffline


#                   #
#   INTERACCIONES   #
#                   #



    def OnPress(self, Event):
        Items = self.Canvas.find_overlapping(
            Event.x - 2, Event.y - 2, Event.x + 2, Event.y + 2
        )
        self.DragNode = None
        for ItemId in reversed(Items):
            Tags = self.Canvas.gettags(ItemId)
            NodeTag = next((T for T in Tags if T.startswith("node_") and T != "node"), None)
            if NodeTag:
                NodeObj = self.GetNodeByTag(NodeTag)
                if NodeObj:
                    self.DragNode    = NodeObj
                    self.DragStartSx = Event.x
                    self.DragStartSy = Event.y
                    self.DragNodeWx0 = NodeObj.x
                    self.DragNodeWy0 = NodeObj.y
                    return

        self.PanStartX  = Event.x
        self.PanStartY  = Event.y
        self.PanOriginX = self.OffsetX
        self.PanOriginY = self.OffsetY

    def OnMotion(self, Event):
        if self.DragNode is not None:
            DxS = Event.x - self.DragStartSx
            DyS = Event.y - self.DragStartSy
            DxW = DxS / self.Scale
            DyW = DyS / self.Scale
            self.DragNode.x = self.DragNodeWx0 + DxW
            self.DragNode.y = self.DragNodeWy0 + DyW
            self.PlaceNodeItems(self.DragNode)
            self.RedrawAllEdges()
        else:
            Dx = Event.x - self.PanStartX
            Dy = Event.y - self.PanStartY
            self.OffsetX = self.PanOriginX + Dx
            self.OffsetY = self.PanOriginY + Dy
            self.RedrawGrid()
            self.RedrawAllNodes()
            self.RedrawAllEdges()

    def OnRelease(self, Event):
        if self.DragNode is not None:
            Dx = abs(Event.x - self.DragStartSx)
            Dy = abs(Event.y - self.DragStartSy)
            if Dx < 4 and Dy < 4 and self.OnNodeClick:
                self.OnNodeClick(self.DragNode)
        self.DragNode = None

    def OnZoom(self, Event):
        if Event.num == 4:
            Delta = 1
        elif Event.num == 5:
            Delta = -1
        else:
            Delta = Event.delta

        Factor   = 1.1 if Delta > 0 else 0.9
        NewScale = self.Scale * Factor

        if NewScale < ZoomMin or NewScale > ZoomMax:
            return

        Sx = Event.x
        Sy = Event.y
        Wx = (Sx - self.OffsetX) / self.Scale
        Wy = (Sy - self.OffsetY) / self.Scale

        self.Scale   = NewScale
        self.OffsetX = Sx - Wx * self.Scale
        self.OffsetY = Sy - Wy * self.Scale

        self.RedrawGrid()
        self.RedrawAllNodes()
        self.RedrawAllEdges()