import threading, time, requests, yaml

cfg = yaml.safe_load(open("config.yaml"))

def start():
    def loop():
        while True:
            try:
                requests.post(cfg["api"]["heartbeat_url"], json={"BotOnline": 1}, timeout=5)
            except:
                pass
            time.sleep(300)
    threading.Thread(target=loop, daemon=True).start()
