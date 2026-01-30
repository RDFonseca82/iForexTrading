def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def falcon_strategy(df, cfg):
    df["ema9"] = ema(df["close"], 9)
    df["ema20"] = ema(df["close"], 20)
    df["ema50"] = ema(df["close"], 50)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    long_signal = prev.ema9 < prev.ema20 and last.ema9 > last.ema20
    short_signal = prev.ema9 > prev.ema20 and last.ema9 < last.ema20

    trend_long = last.ema20 > last.ema50
    trend_short = last.ema20 < last.ema50

    sl = cfg["StopLoss"] / 100
    tp = cfg["TakeProfit"] / 100

    if long_signal and trend_long:
        return {
            "side": "BUY",
            "entry": last.close,
            "stop": last.close * (1 - sl),
            "take": last.close * (1 + tp)
        }

    if short_signal and trend_short:
        return {
            "side": "SELL",
            "entry": last.close,
            "stop": last.close * (1 + sl),
            "take": last.close * (1 - tp)
        }

    return None
