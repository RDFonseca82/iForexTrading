import requests
import pandas as pd
from logger import log_debug, log_error

def get_candles(symbol, timeframe="5min", limit=200):
    log_debug("market_data", f"A obter candles {symbol}")

    try:
        r = requests.get(
            "https://api.twelvedata.com/time_series",
            params={
                "symbol": symbol.replace("USDT", "/USDT"),
                "interval": timeframe,
                "apikey": "SUA_TWELVEDATA_KEY",
                "outputsize": limit
            },
            timeout=10
        )
        r.raise_for_status()
        raw = r.json()

        log_debug("market_data", "Resposta TwelveData", raw)

        df = pd.DataFrame(raw["values"])
        for c in ["open", "high", "low", "close"]:
            df[c] = df[c].astype(float)

        return df.iloc[::-1].reset_index(drop=True)

    except Exception as e:
        log_error("market_data", "Erro ao obter candles", e)
        return None
