import time

from api_client import get_clients
from market_data import get_candles_bybit, get_candles_binance
from strategy_falcon import falcon_strategy
from bybit_client import (
    has_open_position as bybit_has_position,
    place_order as bybit_place_order
)
from binance_client import (
    has_open_position as binance_has_position,
    place_order as binance_place_order
)
from logger import log_info, log_debug, log_error
import heartbeat


# =====================================================
# BOOT
# =====================================================
log_info("main", "BOT iForexTrading iniciado")
heartbeat.start()


# =====================================================
# LOOP PRINCIPAL
# =====================================================
while True:
    try:
        clients = get_clients()
        log_debug("main", "Clientes recebidos", clients)

        for c in clients:
            try:
                log_debug("main", "Processar cliente", c)

                # -------------------------------------------------
                # Ativo?
                # -------------------------------------------------
                if c.get("BotActive") != 1:
                    log_debug(
                        "main",
                        "BotActive=0, ignorado",
                        c.get("IDCliente")
                    )
                    continue

                # -------------------------------------------------
                # Campos obrigatórios
                # -------------------------------------------------
                required_fields = [
                    "TipoMoeda",
                    "LotSize",
                    "StopLoss",
                    "TakeProfit",
                    "Corretora",
                    "CorretoraClientAPIKey",
                    "CorretoraClientAPISecret"
                ]

                missing = [
                    f for f in required_fields
                    if c.get(f) in (None, "", 0)
                ]

                if missing:
                    log_info(
                        "main",
                        "Cliente ignorado: configuração incompleta",
                        {"missing_fields": missing},
                        idcliente=c.get("IDCliente")
                    )
                    continue

                # -------------------------------------------------
                # Normalização
                # -------------------------------------------------
                corretora = c["Corretora"].lower()
                api_key = c["CorretoraClientAPIKey"]
                api_secret = c["CorretoraClientAPISecret"]
                symbol = c["TipoMoeda"]

                # Ambiente
                if corretora == "bybit":
                    env = c.get("BybitEnvironment") or "real"
                else:
                    # Binance não diferencia real/testnet da mesma forma
                    env = "testnet" if c.get("BybitEnvironment") == "testnet" else "real"

                # -------------------------------------------------
                # Verificar posição aberta (ANTI-DUPLICADOS)
                # -------------------------------------------------
                has_position = False

                if corretora == "bybit":
                    has_position = bybit_has_position(
                        api_key,
                        api_secret,
                        symbol,
                        env
                    )

                elif corretora == "binance":
                    has_position = binance_has_position(
                        api_key,
                        api_secret,
                        symbol,
                        env
                    )

                else:
                    log_error(
                        "main",
                        "Corretora não suportada",
                        {"corretora": corretora},
                        idcliente=c.get("IDCliente")
                    )
                    continue

                if has_position:
                    log_info(
                        "main",
                        "Ordem bloqueada: posição já aberta",
                        {"symbol": symbol, "corretora": corretora},
                        idcliente=c.get("IDCliente")
                    )
                    continue

                # -------------------------------------------------
                # Market Data
                # -------------------------------------------------
                if corretora == "bybit":
                    df = get_candles_bybit(
                        symbol,
                        interval="5",
                        env=env
                    )

                elif corretora == "binance":
                    df = get_candles_binance(
                        symbol,
                        interval="5m",
                        env=env
                    )

                if df is None or df.empty:
                    log_debug("main", "Sem candles válidos", symbol)
                    continue

                # -------------------------------------------------
                # Estratégia
                # -------------------------------------------------
                signal = falcon_strategy(df, c)
                log_debug("main", "Sinal calculado", signal)

                if not signal:
                    continue

                # -------------------------------------------------
                # Execução
                # -------------------------------------------------
                if corretora == "bybit":
                    result = bybit_place_order(
                        api_key=api_key,
                        api_secret=api_secret,
                        symbol=symbol,
                        side=signal["side"],
                        qty=c["LotSize"],
                        env=env,
                        sl=signal["stop"],
                        tp=signal["take"]
                    )

                elif corretora == "binance":
                    result = binance_place_order(
                        api_key=api_key,
                        api_secret=api_secret,
                        symbol=symbol,
                        side=signal["side"],
                        qty=c["LotSize"],
                        env=env,
                        sl=signal["stop"],
                        tp=signal["take"]
                    )

                log_info(
                    "main",
                    f"Ordem executada ({corretora.upper()} | {env.upper()})",
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
