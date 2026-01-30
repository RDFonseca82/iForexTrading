import requests
import pandas as pd
import yaml

cfg = yaml.safe_load(open("config.yaml"))

def get_candles(symbol, timeframe="5min", limit=200):
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol.replace("USDT", "/USDT"),
        "interval": timeframe,
        "apikey": cfg["market_data"]["api_key"],
        "outputsize": limit
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()["values"]

    df = pd.DataFrame(data)
    df["close"] = df["close"].astype(float)
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)

    df = df.iloc[::-1].reset_index(drop=True)
    return df
