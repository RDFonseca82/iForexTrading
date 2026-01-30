import yaml
import datetime
import json
import requests
import traceback
import os

cfg = yaml.safe_load(open("config.yaml"))

DEBUG = cfg.get("logging", {}).get("debug", False)
LOG_FILE = cfg.get("logging", {}).get("log_file", "/tmp/iforextrading.log")

def _write_local(level, module, message, data=None):
    if not DEBUG:
        return

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    log_line = {
        "time": datetime.datetime.utcnow().isoformat(),
        "level": level,
        "module": module,
        "message": message,
        "data": data
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_line, ensure_ascii=False) + "\n")

def log_debug(module, message, data=None):
    _write_local("DEBUG", module, message, data)

def log_info(module, message, data=None, idcliente=None):
    _write_local("INFO", module, message, data)
    _send_api_log("INFO", message, data, idcliente)

def log_error(module, message, error=None, idcliente=None):
    err_data = {
        "error": str(error),
        "traceback": traceback.format_exc()
    }
    _write_local("ERROR", module, message, err_data)
    _send_api_log("ERROR", message, err_data, idcliente)

def _send_api_log(level, message, data, idcliente):
    payload = {
        "IDCliente": idcliente or 0,
        "Level": level,
        "Message": message,
        "Data": data
    }
    try:
        requests.post(cfg["api"]["log_url"], json=payload, timeout=5)
    except:
        pass
