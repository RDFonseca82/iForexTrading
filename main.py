import time

from api_client import get_clients
from market_data import get_candles
from strategy_falcon import falcon_strategy
from bybit_client import has_open_position, place_order
from logger import log_info, log_debug, log_error
import heartbeat

log_info("main", "BOT iForexTrading iniciado")

heartbeat.start()

while True:
    try:
        clients = get_clients()
        log_debug("main", "Clientes recebidos", clients)

        for c in clients:
            try:
                log_debug("main", "Processar cliente", c)
                
                if c.get("BotActive") != 1:
                    log_debug("main", "BotActive=0, ignorado", c.get("IDCliente"))
                    continue
                
                # 🔒 Validação OBRIGATÓRIA antes de qualquer chamada à corretora
                required_fields = [
                    "LotSize",
                    "StopLoss",
                    "TakeProfit",
                    "CorretoraClientAPIKey",
                    "CorretoraClientAPISecret"
                ]
                
                missing = [f for f in required_fields if not c.get(f)]
                
                if missing:
                    log_info(
                        "main",
                        "Cliente ignorado: configuração incompleta",
                        {
                            "missing_fields": missing
                        },
                        idcliente=c.get("IDCliente")
                    )
                    continue
                
                # Environment default seguro
                env = c.get("BybitEnvironment") or "real"
                symbol = c.get("TipoMoeda")
                
                # 🔒 SÓ AGORA falamos com a Bybit
                if has_open_position(
                    c["CorretoraClientAPIKey"],
                    c["CorretoraClientAPISecret"],
                    symbol,
                    env
                ):
                    log_info(
                        "main",
                        "Ordem bloqueada: posição já aberta",
                        {"symbol": symbol},
                        idcliente=c.get("IDCliente")
                    )
                    continue


                df = get_candles(symbol)
                if df is None or df.empty:
                    log_debug("main", "Sem candles válidos", symbol)
                    continue

                signal = falcon_strategy(df, c)
                log_debug("main", "Sinal calculado", signal)

                if not signal:
                    continue

                result = place_order(
                    api_key=c["CorretoraClientAPIKey"],
                    api_secret=c["CorretoraClientAPISecret"],
                    symbol=symbol,
                    side=signal["side"],
                    qty=c["LotSize"],
                    env=env,
                    sl=signal["stop"],
                    tp=signal["take"]
                )

                log_info(
                    "main",
                    f"Ordem executada ({env.upper()})",
                    result,
                    idcliente=c.get("IDCliente")
                )

            except Exception as e:
                log_error(
                    "main",
                    "Erro ao processar cliente",
                    e,
                    idcliente=c.get("IDCliente")
                )

        time.sleep(60)

    except Exception as e:
        log_error("main", "Erro fatal no loop principal", e)
        time.sleep(10)
