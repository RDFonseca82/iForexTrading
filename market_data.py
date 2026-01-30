import requests
import pandas as pd
import time
from logger import log_debug, log_error

def get_candles(symbol, interval="5", limit=200, env="real"):
    """
    interval:
      1  = 1m
      3  = 3m
      5  = 5m
      15 = 15m
      60 = 1h
    """

    base_url = (
        "https://api-demo.bybit.com"
        if env == "testnet"
        else "https://api.bybit.com"
    )

    url = f"{base_url}/v5/market/kline"

    params = {
        "category": "linear",      # USDT Futures
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    log_debug("market_data", "A obter candles Bybit", params)

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()

        raw = r.json()
        log_debug("market_data", "Resposta Bybit Kline", raw)

        if raw.get("retCode") != 0:
            raise ValueError(raw.get("retMsg"))

        rows = raw["result"]["list"]

        # Bybit devolve do mais recente → mais antigo
        df = pd.DataFrame(rows, columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "turnover"
        ])

        for col in ["open", "high", "low", "close"]:
            df[col] = df[col].astype(float)

        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="ms")

        return df.iloc[::-1].reset_index(drop=True)

    except Exception as e:
        log_error("market_data", "Erro ao obter candles Bybit", e)
        return None
