import requests
import pandas as pd

def get_candles(symbol, timeframe="5min", limit=200):
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol.replace("USDT", "/USDT"),
        "interval": timeframe,
        "apikey": "a0e1684f24ef45f98a0f8e46eb3e03bf",
        "outputsize": limit
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()

    df = pd.DataFrame(r.json()["values"])
    for c in ["open", "high", "low", "close"]:
        df[c] = df[c].astype(float)

    return df.iloc[::-1].reset_index(drop=True)
