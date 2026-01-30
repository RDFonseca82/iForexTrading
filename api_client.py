import requests
import yaml
from logger import log_debug, log_error

cfg = yaml.safe_load(open("config.yaml"))

def get_clients():
    log_debug("api_client", "A consultar forex_api.php")
    try:
        r = requests.get(cfg["api"]["config_url"], timeout=10)
        r.raise_for_status()
        data = r.json()
        log_debug("api_client", "Clientes recebidos", data)
        return data
    except Exception as e:
        log_error("api_client", "Erro ao obter clientes", e)
        return []
