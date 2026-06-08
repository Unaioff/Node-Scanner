import json
import threading
import customtkinter as ctk

from config import Config, ConfigPath
from models import NodeStore, Node
from canvas_map import MapCanvas
from network import IsValidIp, IsNetwork, ScanSingleIp, ScanNetwork, GetSelfIp, GetGateway


ctk.set_appearance_mode(Config.get("theme", "dark"))
ctk.set_default_color_theme("blue")


# ===================== [ SETTINGS DIALOG ] =====================

# Configuración UI
# No tocar, no se por que funciona

class SettingsDialog(ctk.CTkToplevel):

    def __init__(self, Master, ConfigData, OnSave=None, **Kwargs):
        super().__init__(Master, **Kwargs)

        self.ConfigData = ConfigData
        self.OnSave     = OnSave

        self.title("Configuración")
        self.geometry("380x400")
        self.resizable(False, False)

        self.Build()

        self.after(100, self._focus_dialog)

    def _focus_dialog(self):
        self.grab_set()
        self.lift()
        self.focus_force()

    def Build(self):
        Pad = {"padx": 20, "pady": 6}

        ctk.CTkLabel(self, text="Tema de la interfaz", font=ctk.CTkFont(weight="bold")).pack(anchor="w", **Pad)

        self.ThemeVar = ctk.StringVar(value=self.ConfigData.get("theme", "dark"))
        ThemeFrame = ctk.CTkFrame(self, fg_color="transparent")
        ThemeFrame.pack(anchor="w", padx=20, pady=(0, 10))
        for T in ("dark", "light", "system"):
            ctk.CTkRadioButton(ThemeFrame, text=T.capitalize(), variable=self.ThemeVar, value=T).pack(side="left", padx=6)

        ctk.CTkFrame(self, height=2, fg_color="gray30").pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(self, text="Timeout de escaneo (segundos)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", **Pad)

        self.TimeoutVar = ctk.IntVar(value=self.ConfigData.get("scan_timeout", 2))
        TimeoutFrame = ctk.CTkFrame(self, fg_color="transparent")
        TimeoutFrame.pack(anchor="w", padx=20, pady=(0, 10))
        ctk.CTkSlider(TimeoutFrame, from_=1, to=10, number_of_steps=9, variable=self.TimeoutVar, width=200).pack(side="left")
        self.TimeoutLbl = ctk.CTkLabel(TimeoutFrame, text=f"{self.TimeoutVar.get()} s", width=40)
        self.TimeoutLbl.pack(side="left", padx=8)
        self.TimeoutVar.trace_add("write", lambda *_: self.TimeoutLbl.configure(text=f"{self.TimeoutVar.get()} s"))

        ctk.CTkFrame(self, height=2, fg_color="gray30").pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(self, text="Opciones de escaneo", font=ctk.CTkFont(weight="bold")).pack(anchor="w", **Pad)

        Opts = self.ConfigData.get("scan_options", {})
        self.OptVars = {}
        OptionsFrame = ctk.CTkFrame(self, fg_color="transparent")
        OptionsFrame.pack(anchor="w", padx=20, pady=(0, 10))

        OptionLabels = {
            "icmp":      "ICMP ping",
            "arp":       "ARP scan",
            "ports":     "Escaneo de puertos",
            "os_detect": "Detección de OS",
        }

        for Key, Label in OptionLabels.items():
            Var = ctk.BooleanVar(value=Opts.get(Key, False))
            self.OptVars[Key] = Var
            ctk.CTkCheckBox(OptionsFrame, text=Label, variable=Var).pack(anchor="w", pady=2)

        ctk.CTkFrame(self, height=2, fg_color="gray30").pack(fill="x", padx=12, pady=4)

        BtnFrame = ctk.CTkFrame(self, fg_color="transparent")
        BtnFrame.pack(pady=10)
        ctk.CTkButton(BtnFrame, text="Guardar", width=110, command=self.Save).pack(side="left", padx=8)
        ctk.CTkButton(BtnFrame, text="Cancelar", width=110, fg_color="gray40", command=self.destroy).pack(side="left", padx=8)


    # Guarda la configuración actual

    def Save(self):
        self.ConfigData["theme"] = self.ThemeVar.get()
        self.ConfigData["scan_timeout"] = self.TimeoutVar.get()
        for Key, Var in self.OptVars.items():
            self.ConfigData["scan_options"][Key] = Var.get()

        try:
            with open(ConfigPath, "w", encoding="utf-8") as F:
                json.dump(self.ConfigData, F, indent=4)
        except OSError as E:
            print(f"[settings] No se pudo guardar config.json: {E}")

        ctk.set_appearance_mode(self.ConfigData["theme"])

        if self.OnSave:
            self.OnSave(self.ConfigData)

        self.destroy()


# ===================== [ TOOLBAR ] =====================

class ToolBar(ctk.CTkFrame):

    def __init__(self, Master, OnScan, OnSettings, **Kwargs):
        super().__init__(Master, **Kwargs)


        self.OnScan = OnScan
        self.OnSettings = OnSettings

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)

        self.Entry = ctk.CTkEntry(self, placeholder_text="IP o rango - ej: 192.168.1.0/24")
        self.Entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.Entry.bind("<Return>", lambda E: self.TriggerScan())

        self.ScanBtn = ctk.CTkButton(self, text="↻ Scan", width=90, height=36, command=self.TriggerScan)
        self.ScanBtn.grid(row=0, column=1, padx=(0, 8))

        self.SettingsBtn = ctk.CTkButton(self, text="⚙", width=36, height=36, command=self.OnSettings)
        self.SettingsBtn.grid(row=0, column=2)


    def TriggerScan(self):
        Ip = self.Entry.get().strip()
        if not Ip:
            return
        self.SetLoading(True)
        self.OnScan(Ip, Callback=lambda: self.SetLoading(False))


    def SetLoading(self, Loading):
        State = "disabled" if Loading else "normal"
        Text  = "Scanning…" if Loading else "⟳ Scan"
        self.ScanBtn.configure(state=State, text=Text)
        self.Entry.configure(state=State)


    def Clear(self):
        self.Entry.configure(state="normal")
        self.Entry.delete(0, "end")


# ===================== [ INFO PANEL ] =====================

class InfoPanel(ctk.CTkScrollableFrame):

    def __init__(self, Master, **Kwargs):
        super().__init__(Master, **Kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.Title = ctk.CTkLabel(self, text="Selecciona un nodo", font=ctk.CTkFont(size=15, weight="bold"))
        self.Title.grid(row=0, column=0, pady=(0, 12), sticky="w")

        self.Rows = []

    def ShowNode(self, NodeObj):
        for W in self.Rows:
            W.destroy()
        self.Rows.clear()

        self.Title.configure(text=NodeObj.ip)

        Fields = [
            ("Estado",    "🟢 Online" if NodeObj.online else "🔴 Offline"),
            ("MAC",       NodeObj.mac or "—"),
            ("Hostname",  NodeObj.hostname or "—"),
            ("OS",        NodeObj.os or "—"),
            ("Es host",   "Sí" if NodeObj.is_host else "No"),
            ("Servicios", ", ".join(NodeObj.services) if NodeObj.services else "—"),
        ]

        for I, (Label, Value) in enumerate(Fields, start=1):
            Lbl = ctk.CTkLabel(self, text=f"{Label}:", anchor="w", font=ctk.CTkFont(size=12, weight="bold"))
            Lbl.grid(row=I * 2 - 1, column=0, sticky="w", pady=(6, 0))
            Val = ctk.CTkLabel(self, text=Value, anchor="w", font=ctk.CTkFont(size=12))
            Val.grid(row=I * 2, column=0, sticky="w")
            self.Rows += [Lbl, Val]

    def Clear(self):
        for W in self.Rows:
            W.destroy()
        self.Rows.clear()
        self.Title.configure(text="Selecciona un nodo")


# ===================== [ APP PRINCIPAL ] =====================

class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Node-Scanner")
        self.geometry("1280x700")
        self.minsize(900, 500)

        self.Store      = NodeStore()
        self.ConfigData = Config

        self.BuildLayout()

    def BuildLayout(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

        self.Toolbar = ToolBar(self, OnScan=self.HandleScan, OnSettings=self.OpenSettings)
        self.Toolbar.grid(row=0, column=0, padx=12, pady=10, sticky="ew")

        self.MapCanvas = MapCanvas(self, OnNodeClick=self.OnNodeClick)
        self.MapCanvas.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        self.InfoPanel = InfoPanel(self)
        self.InfoPanel.grid(row=0, column=1, rowspan=2, padx=(0, 12), pady=12, sticky="nsew")

    def OnNodeClick(self, NodeObj):
        self.InfoPanel.ShowNode(NodeObj)

    def OpenSettings(self):
        SettingsDialog(self, ConfigData=self.ConfigData, OnSave=self.OnConfigSaved)

    def OnConfigSaved(self, NewConfig):
        self.ConfigData = NewConfig

    def HandleScan(self, Ip, Callback=None):
        if not IsValidIp(Ip):
            self.ShowError(f'"{Ip}" no es una IP o rango válido.')
            if Callback:
                Callback()
            return

        def Run():
            try:
                if IsNetwork(Ip):
                    Results = ScanNetwork(Ip)
                    Gateway = GetGateway()
                    
                    for Data in Results:
                        NodeObj, Created = self.Store.AddOrUpdate(Data)
                        self.after(0, self.RenderNode, NodeObj, Created)
                    
                    # Unir cada nodo al gateway, y el gateway a tu IP
                    if Gateway:
                        GwData = {"ip": Gateway, "online": True, "mac": None, "hostname": "", "os": "", "services": []}
                        GwNode, GwCreated = self.Store.AddOrUpdate(GwData)
                        self.after(0, self.RenderNode, GwNode, GwCreated)
                        
                        SelfIp = GetSelfIp()
                        SelfData = {"ip": SelfIp, "online": True, "mac": None, "hostname": "", "os": "", "services": []}
                        SelfNode, _ = self.Store.AddOrUpdate(SelfData)
                        self.after(0, self.RenderNode, SelfNode, _)

                        for Node_ in self.Store.nodes:
                            if Node_.ip not in (Gateway, SelfIp):
                                self.after(0, self.MapCanvas.DrawEdge, Node_, GwNode, False)
                        
                        self.after(0, self.MapCanvas.DrawEdge, GwNode, SelfNode, False)



                else:
                    Data = ScanSingleIp(Ip)
                    NodeObj, Created = self.Store.AddOrUpdate(Data)
                    self.after(0, self.RenderNode, NodeObj, Created)

                    if Data.get("online"):
                        Gateway = GetGateway()
                        SelfIp = GetSelfIp()

                        if Gateway and Ip not in (Gateway, SelfIp):
                            GwData = {"ip": Gateway, "online": True, "mac": None, "hostname": "", "os": "", "services": []}
                            GwNode, GwCreated = self.Store.AddOrUpdate(GwData)
                            self.after(0, self.RenderNode, GwNode, GwCreated)

                            SelfData = {"ip": SelfIp, "online": True, "mac": None, "hostname": "", "os": "", "services": []}
                            SelfNode, _ = self.Store.AddOrUpdate(SelfData)
                            self.after(0, self.RenderNode, SelfNode, _)

                            self.after(0, self.MapCanvas.DrawEdge, NodeObj, GwNode, False)
                            self.after(0, self.MapCanvas.DrawEdge, GwNode, SelfNode, False)

 
                        elif Gateway and Ip == Gateway:
                            SelfData = {"ip": SelfIp, "online": True, "mac": None, "hostname": "", "os": "", "services": []}
                            SelfNode, _ = self.Store.AddOrUpdate(SelfData)
                            self.after(0, self.RenderNode, SelfNode, _)
                            self.after(0, self.MapCanvas.DrawEdge, NodeObj, SelfNode, False)

                    if Data.get("online"):
                        Hops = Data.get("connections", [])
                        HopNodes = []
                        for HopIp in Hops:
                            if HopIp == Ip:
                                continue
                            HopData = {"ip": HopIp, "online": True, "mac": None, "hostname": "", "os": "", "services": [], "connections": []}
                            HopNode, HopCreated = self.Store.AddOrUpdate(HopData)
                            self.after(0, self.RenderNode, HopNode, HopCreated)
                            HopNodes.append(HopNode)


                        FullChain = HopNodes + [NodeObj]

                        for I in range(len(FullChain) - 1):
                            A = FullChain[I]
                            B = FullChain[I + 1]
                            IsHop = (I < len(FullChain) - 2)
                            self.after(0, self.MapCanvas.DrawEdge, A, B, IsHop)
            finally:
                self.after(0, self.Toolbar.Clear)
                if Callback:
                    self.after(0, Callback)

        threading.Thread(target=Run, daemon=True).start()

    def RenderNode(self, NodeObj, Created):
        if Created:
            self.MapCanvas.DrawNode(NodeObj)
        else:
            self.MapCanvas.UpdateNode(NodeObj)

    def ShowError(self, Msg):
        Win = ctk.CTkToplevel(self)
        Win.title("Error")
        Win.geometry("320x120")
        Win.grab_set()
        ctk.CTkLabel(Win, text=Msg, wraplength=280).pack(pady=20)
        ctk.CTkButton(Win, text="OK", command=Win.destroy).pack()

    def Run(self):
        self.mainloop()


if __name__ == "__main__":
    App_ = App()
    App_.Run()