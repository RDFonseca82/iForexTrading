import time
import yaml
from api_client import get_clients
from market_data import get_candles
from strategy_falcon import falcon_strategy
from webhook_sender import send_signal
from logger import log_event
import heartbeat

cfg = yaml.safe_load(open("config.yaml"))

heartbeat.start()

while True:
    try:
        clients = get_clients()

        for c in clients:
            if c["BotActive"] != 1:
                continue

            df = get_candles(
                symbol=c["TipoMoeda"],
                timeframe="5min",
                limit=cfg["bot"]["candle_limit"]
            )

            signal = falcon_strategy(df, c)

            if signal:
                send_signal(
                    broker=c["Corretora"],
                    api_key=c["CorretoraClientAPIKey"],
                    symbol=c["TipoMoeda"],
                    lot=c["LotSize"],
                    signal=signal
                )

                log_event(
                    idcliente=c["IDCliente"],
                    message=f"Sinal {signal['side']} enviado",
                    data=signal
                )

        time.sleep(cfg["bot"]["poll_interval_seconds"])

    except Exception as e:
        log_event(
            idcliente=0,
            message="Erro geral no BOT",
            data=str(e),
            level="ERROR"
        )
        time.sleep(10)
