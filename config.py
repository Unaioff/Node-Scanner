import json
from pathlib import Path

ConfigPath = Path(__file__).parent / "config.json"



Defaults = {
    "scan_options": {
        "icmp": True,
        "arp": True,
        "ports": False,
        "os_detect": False,
    },
    "scan_timeout": 2,
    "theme": "dark",
}


def LoadConfig():
    if not ConfigPath.exists():
        print(f"[config] No se encontró {ConfigPath}, usando valores por defecto.")
        return Defaults.copy()

    try:
        with open(ConfigPath, encoding="utf-8") as F:
            UserCfg = json.load(F)
    except json.JSONDecodeError as E:
        print(f"[config] Error al leer config.json: {E}. Usando valores por defecto.")
        return Defaults.copy()

    Merged = Defaults.copy()
    for Key, Value in UserCfg.items():
        if isinstance(Value, dict) and Key in Merged and isinstance(Merged[Key], dict):
            Merged[Key].update(Value)
        else:
            Merged[Key] = Value

    return Merged


Config = LoadConfig()