import requests
import time
import yaml
import threading

cfg = yaml.safe_load(open("config.yaml"))

def heartbeat_loop():
    while True:
        try:
            requests.post(
                cfg["api"]["heartbeat_url"],
                json={"BotOnline": 1},
                timeout=5
            )
        except:
            pass
        time.sleep(cfg["heartbeat"]["interval_seconds"])

def start():
    threading.Thread(target=heartbeat_loop, daemon=True).start()
