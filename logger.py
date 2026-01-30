import requests
import yaml
import datetime

cfg = yaml.safe_load(open("config.yaml"))

def log_event(idcliente, message, data=None, level="INFO"):
    payload = {
        "IDCliente": idcliente,
        "Level": level,
        "Message": message,
        "Data": data,
        "Timestamp": datetime.datetime.utcnow().isoformat()
    }

    try:
        requests.post(cfg["api"]["log_url"], json=payload, timeout=5)
    except:
        pass

    with open(cfg["logging"]["local_file"], "a") as f:
        f.write(str(payload) + "\n")
