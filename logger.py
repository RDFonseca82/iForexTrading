import yaml
import datetime
import json
import requests
import traceback
import os
import time

# =====================================================
# CONFIG
# =====================================================
cfg = yaml.safe_load(open("config.yaml"))

DEBUG = cfg.get("logging", {}).get("debug", False)
LOG_FILE = cfg.get("logging", {}).get("log_file", "/tmp/iforextrading.log")
LOG_CLEAN_INTERVAL = 60 * 60  # 60 minutos

_last_log_cleanup = 0


# =====================================================
# LOG LOCAL
# =====================================================
def _cleanup_log_if_needed():
    global _last_log_cleanup

    now = time.time()

    if _last_log_cleanup == 0:
        _last_log_cleanup = now
        return

    if now - _last_log_cleanup >= LOG_CLEAN_INTERVAL:
        try:
            if os.path.exists(LOG_FILE):
                open(LOG_FILE, "w").close()  # limpa o ficheiro
            _last_log_cleanup = now
        except:
            pass


def _write_local(level, module, message, data=None):
    if not DEBUG:
        return

    _cleanup_log_if_needed()

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


# =====================================================
# LOGGING API
# =====================================================
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


# =====================================================
# API LOG
# =====================================================
def _send_api_log(level, message, data, idcliente):
    payload = {
        "IDCliente": idcliente or 0,
        "Level": level,
        "Message": message,
        "Data": data
    }

    try:
        r = requests.post(
            cfg["api"]["log_url"],
            json=payload,
            timeout=5,
            headers={"Content-Type": "application/json"}
        )

        if r.status_code != 200:
            _write_local(
                "ERROR",
                "logger",
                "Erro ao enviar log para API",
                {
                    "status_code": r.status_code,
                    "response": r.text,
                    "payload": payload
                }
            )

    except Exception as e:
        _write_local(
            "ERROR",
            "logger",
            "Exceção ao enviar log para API",
            {
                "error": str(e),
                "payload": payload
            }
        )
