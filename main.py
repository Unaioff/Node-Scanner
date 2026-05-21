from ui import App
import os
import ctypes
import platform
import sys


def Admin():
    system = platform.system()

    if system == "Windows":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    else:
        return os.geteuid() == 0


if not Admin(): 
    sys.exit()


#[ Ejecutar Interfaz] 
if __name__ == "__main__":
    app = App()
    app.RunApp()






