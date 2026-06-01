import customtkinter as ctk
from scanner import ValidIp, NetworkNodeScan, SimpleNodeScan, CrearNodo, ActualizarNodo, Nodos



# ===================== [ TOOLBAR ] =====================
class ToolBar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        # Entry
        self.search_entry = ctk.CTkEntry(self,placeholder_text="Ejemplo: 192.168.0.0")
        self.search_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        # Botón Scan
        self.search_button = ctk.CTkButton(self, text="B", width=40, height=40, command=self.ScanInput)
        self.search_button.grid(row=0, column=1, padx=(0, 10))

        # Botón settings
        self.settings_button = ctk.CTkButton(self, text="⚙", width=40, height=40)
        self.settings_button.grid(row=0, column=2)

        # Configuración de columnas dentro del frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)



    def ScanInput(self):
        InputedIP = self.search_entry.get()
        if ValidIp(InputedIP):
            print("IP Valida")
            Existe = False
        
            for nodo in Nodos:
                if nodo.ip == InputedIP:
                    Existe = True
                    break

            if not "/" in InputedIP:
                if Existe: ActualizarNodo(InputedIP,SimpleNodeScan(InputedIP))
                else: CrearNodo(SimpleNodeScan(InputedIP))
            else:
                NetworkNodeScan(InputedIP)
           
            self.search_entry.set("")   
            
        else:
            print("[ERROR] IP Invalida")



    




# ===================== [ MAP SECTION ] =====================
class MapSection(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.nodo_canvas = ctk.CTkCanvas(self, bg="#2b2b2b", highlightthickness=0)
        self.nodo_canvas.grid(row=0, column=0, sticky="nsew")

        self.CreateNodo("192.168.0.1", 100, 100)

        self.scale = 1.0

        self.nodo_canvas.bind("<MouseWheel>", self.Zoom)
        self.nodo_canvas.bind("<B1-Motion>", self.MoveCamera)
        self.nodo_canvas.bind("<ButtonPress-1>", self.StartMove)

    def StartMove(self, event):
        self.nodo_canvas.scan_mark(event.x, event.y)

    def Zoom(self, event):
        
        factor = 1.1 if event.delta > 0 else 0.9

        x = self.nodo_canvas.canvasx(event.x)
        y = self.nodo_canvas.canvasy(event.y)

        self.nodo_canvas.scale("all", x, y, factor, factor)

        self.scale *= factor  
        self.nodo_canvas.configure(scrollregion=self.nodo_canvas.bbox("all"))

    def MoveCamera(self, event):
        self.nodo_canvas.scan_dragto(event.x, event.y, gain=1)
        

    def CreateNodo(self, ip, x, y):
        self.nodo_canvas.create_oval(x-25, y-25, x+25, y+25, fill="#54d060", outline="#1f831a", width=3)
        self.nodo_canvas.create_text(x, y+30, text=ip, fill="white", font=("Arial", 12, "bold"))


# ===================== [ INFO SECTION ] =====================
class InfoSection(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Ejemplo de contenido
        self.label = ctk.CTkLabel(self, text="INFO / PUERTOS")
        self.label.grid(row=0, column=0)


# ===================== [ APP PRINCIPAL ] =====================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Network-Scanner")
        self.geometry("1200x628")

        # Layout principal
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

        
        self.toolbar = ToolBar(self)
        self.toolbar.grid(row=0, column=0, padx=10, pady=10, sticky="ew")


        self.map_section = MapSection(self)
        self.map_section.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")


        self.info_section = InfoSection(self)
        self.info_section.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

    def run(self):
        self.mainloop()




app = App()
app.run()