import time
from api_client import get_clients
from market_data import get_candles
from strategy_falcon import falcon_strategy
from bybit_client import has_open_position, place_order
from logger import log_event
import heartbeat

heartbeat.start()

while True:
    try:
        for c in get_clients():

            if c["BotActive"] != 1 or c["Corretora"].lower() != "bybit":
                continue

            env = c.get("BybitEnvironment", "real")

            if has_open_position(
                c["CorretoraClientAPIKey"],
                c["CorretoraClientAPISecret"],
                c["TipoMoeda"],
                env
            ):
                log_event(
                    c["IDCliente"],
                    "Ordem bloqueada: posição já aberta",
                    {"symbol": c["TipoMoeda"], "env": env}
                )
                continue

            df = get_candles(c["TipoMoeda"])
            signal = falcon_strategy(df, c)

            if not signal:
                continue

            res = place_order(
                c["CorretoraClientAPIKey"],
                c["CorretoraClientAPISecret"],
                c["TipoMoeda"],
                signal["side"],
                c["LotSize"],
                env,
                signal["stop"],
                signal["take"]
            )

            log_event(
                c["IDCliente"],
                f"Ordem executada ({env.upper()})",
                res
            )

        time.sleep(60)

    except Exception as e:
        log_event(0, "Erro geral do BOT", str(e), "ERROR")
        time.sleep(10)
