import requests
import yaml

cfg = yaml.safe_load(open("config.yaml"))

def get_clients():
    r = requests.get(cfg["api"]["config_url"], timeout=10)
    r.raise_for_status()
    return r.json()
