import requests
import pandas as pd
from logger import log_debug, log_error

# =====================================================
# BYBIT FUTURES - MARKET DATA
# =====================================================

def get_candles_bybit(symbol, interval="5", limit=200, env="real"):
    """
    interval:
      1  = 1m
      3  = 3m
      5  = 5m
      15 = 15m
      60 = 1h
    """

    base_url = (
        "https://api-testnet.bybit.com"
        if env == "testnet"
        else "https://api.bybit.com"
    )

    url = f"{base_url}/v5/market/kline"

    params = {
        "category": "linear",   # USDT-M Futures
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    log_debug("market_data", "A obter candles Bybit", params)

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()

        raw = r.json()
        log_debug("market_data", "Resposta Bybit", raw)

        if raw.get("retCode") != 0:
            raise ValueError(raw.get("retMsg"))

        rows = raw["result"]["list"]

        df = pd.DataFrame(
            rows,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "turnover"
            ]
        )

        for c in ["open", "high", "low", "close"]:
            df[c] = df[c].astype(float)

        df["timestamp"] = pd.to_datetime(
            df["timestamp"].astype(int),
            unit="ms"
        )

        # Bybit devolve do mais recente → mais antigo
        return df.iloc[::-1].reset_index(drop=True)

    except Exception as e:
        log_error("market_data", "Erro ao obter candles Bybit", e)
        return None


# =====================================================
# BINANCE FUTURES - MARKET DATA
# =====================================================

def get_candles_binance(symbol, interval="5m", limit=200, env="real"):
    base_url = (
        "https://testnet.binancefuture.com"
        if env == "testnet"
        else "https://fapi.binance.com"
    )

    url = f"{base_url}/fapi/v1/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    log_debug("market_data", "A obter candles Binance", params)

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()

        rows = r.json()

        df = pd.DataFrame(
            rows,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "_",
                "_",
                "_",
                "_",
                "_",
                "_"
            ]
        )

        for c in ["open", "high", "low", "close"]:
            df[c] = df[c].astype(float)

        return df.reset_index(drop=True)

    except Exception as e:
        log_error("market_data", "Erro ao obter candles Binance", e)
        return None
