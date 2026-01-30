import time
import requests

from api_client import get_clients
from market_data import get_candles_binance
from strategy_falcon import falcon_strategy
from bybit_client import (
    has_open_position as bybit_has_position,
    place_order as bybit_place_order,
    get_closed_trades
)
from binance_client import (
    has_open_position as binance_has_position,
    place_order as binance_place_order,
    get_closed_trades as binance_get_closed_trades
)
from logger import log_info, log_debug, log_error
import heartbeat


# =====================================================
# CONFIG
# =====================================================

TRADES_API_URL = "http://invest.rdfonseca.com/api/forex_api_trades.php"

# Evitar duplicados durante execução
SENT_TRADES = set()


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

                idcliente = c.get("IDCliente")

                # -------------------------------------------------
                # Ativo?
                # -------------------------------------------------
                if c.get("BotActive") != 1:
                    log_debug("main", "BotActive=0, ignorado", idcliente)
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
                        idcliente=idcliente
                    )
                    continue

                # -------------------------------------------------
                # Normalização
                # -------------------------------------------------
                corretora = c["Corretora"].lower()
                api_key = c["CorretoraClientAPIKey"]
                api_secret = c["CorretoraClientAPISecret"]
                symbol = c["TipoMoeda"]

                if corretora == "bybit":
                    env = c.get("BybitEnvironment") or "real"
                else:
                    env = "testnet" if c.get("BybitEnvironment") == "testnet" else "real"

                # =================================================
                # 📊 PASSO 2 — TRADES FECHADOS (SÓ BYBIT)
                # =================================================
                if corretora == "bybit":
                    closed_trades = get_closed_trades(
                        api_key,
                        api_secret,
                        symbol,
                        env=env,
                        limit=10
                    )

                    for t in closed_trades:
                        trade_id = t.get("orderId")

                        if not trade_id or trade_id in SENT_TRADES:
                            continue

                        payload = {
                            "IDCliente": idcliente,
                            "Corretora": "bybit",
                            "Symbol": t["symbol"],
                            "Side": t["side"],
                            "EntryPrice": t["entry_price"],
                            "ExitPrice": t["exit_price"],
                            "Qty": t["qty"],
                            "Fee": t["fee"],
                            "PnL": t["pnl"],
                            "OrderID": trade_id,
                            "OpenTime": t["createdTime"],
                            "CloseTime": t["updatedTime"],
                            "Environment": env
                        }

                        try:
                            log_debug(
                                "main",
                                "A enviar trade fechado para API",
                                payload
                            )

                            r = requests.post(
                                TRADES_API_URL,
                                json=payload,
                                timeout=10
                            )

                            r.raise_for_status()

                            SENT_TRADES.add(trade_id)

                            log_info(
                                "main",
                                "Trade fechado enviado com sucesso",
                                payload,
                                idcliente=idcliente
                            )

                        except Exception as e:
                            log_error(
                                "main",
                                "Erro ao enviar trade fechado",
                                e,
                                idcliente=idcliente
                            )

                    # =================================================
                    # 📊 PASSO 2 — TRADES FECHADOS (BINANCE)
                    # =================================================
                    elif corretora == "binance":
                        closed_trades = binance_get_closed_trades(
                            api_key,
                            api_secret,
                            symbol,
                            env=env,
                            limit=10
                        )
                    
                        for t in closed_trades:
                            trade_id = f"BINANCE-{t['orderId']}"
                    
                            if trade_id in SENT_TRADES:
                                continue
                    
                            payload = {
                                "IDCliente": idcliente,
                                "Corretora": "binance",
                                "Symbol": t["symbol"],
                                "Side": t["side"],
                                "EntryPrice": t["entry_price"],
                                "ExitPrice": t["exit_price"],
                                "Qty": t["qty"],
                                "Fee": t["fee"],
                                "PnL": t["pnl"],
                                "OrderID": trade_id,
                                "OpenTime": t["createdTime"],
                                "CloseTime": t["updatedTime"],
                                "Environment": env
                            }
                    
                            try:
                                log_debug(
                                    "main",
                                    "A enviar trade fechado BINANCE para API",
                                    payload
                                )
                    
                                r = requests.post(
                                    TRADES_API_URL,
                                    json=payload,
                                    timeout=10
                                )
                    
                                r.raise_for_status()
                    
                                SENT_TRADES.add(trade_id)
                    
                                log_info(
                                    "main",
                                    "Trade fechado BINANCE enviado",
                                    payload,
                                    idcliente=idcliente
                                )
                    
                            except Exception as e:
                                log_error(
                                    "main",
                                    "Erro ao enviar trade fechado BINANCE",
                                    e,
                                    idcliente=idcliente
                                )



                
                # -------------------------------------------------
                # Verificar posição aberta (ANTI-DUPLICADOS)
                # -------------------------------------------------
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
                    continue

                if has_position:
                    log_info(
                        "main",
                        "Ordem bloqueada: posição já aberta",
                        {"symbol": symbol, "corretora": corretora},
                        idcliente=idcliente
                    )
                    continue

                # -------------------------------------------------
                # Market Data (Binance)
                # -------------------------------------------------
                df = get_candles_binance(
                    symbol,
                    interval="5m",
                    env=env
                )

                if df is None or df.empty:
                    log_debug(
                        "main",
                        "Sem candles válidos (Binance)",
                        {"symbol": symbol}
                    )
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

                else:
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
                    idcliente=idcliente
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
