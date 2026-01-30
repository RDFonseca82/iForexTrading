import time
from api_client import get_clients
from market_data import get_candles
from strategy_falcon import falcon_strategy
from bybit_client import has_open_position, place_order
from logger import log_info, log_debug, log_error
import heartbeat

log_info("main", "BOT iniciado")

heartbeat.start()

while True:
    try:
        clients = get_clients()
        log_debug("main", "Loop clientes", clients)

        for c in clients:
            log_debug("main", "Processar cliente", c)

            if c["BotActive"] != 1:
                log_debug("main", "BotActive = 0, ignorado", c["IDCliente"])
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
        
    log_debug("main", "Sinal calculado", signal)
    
    except Exception as e:
        log_error("main", "Erro fatal no loop principal", e)
        time.sleep(10)
