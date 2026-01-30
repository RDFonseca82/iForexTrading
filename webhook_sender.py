import requests
import yaml

cfg = yaml.safe_load(open("config.yaml"))

def send_signal(broker, api_key, symbol, lot, signal):
    payload = {
        "symbol": symbol,
        "side": signal["side"],
        "qty": lot,
        "entry": signal["entry"],
        "stop_loss": signal["stop"],
        "take_profit": signal["take"],
        "api_key": api_key
    }

    if broker.lower() == "binance":
        url = cfg["webhooks"]["binance"]
    elif broker.lower() == "bybit":
        url = cfg["webhooks"]["bybit"]
    else:
        raise Exception("Corretora não suportada")

    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
