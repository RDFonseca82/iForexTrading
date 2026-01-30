import requests
import pandas as pd
from logger import log_debug, log_error


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
