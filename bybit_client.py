import time
import hmac
import hashlib
import requests
import json

from logger import log_debug, log_error

# =====================================================
# CONFIGURAÇÃO BASE
# =====================================================

RECV_WINDOW = "5000"

def _base_url(env: str) -> str:
    return "https://api-demo.bybit.com" if env == "testnet" else "https://api.bybit.com"


def _sign(secret: str, payload: str) -> str:
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


def _headers(api_key: str, sign: str, ts: str) -> dict:
    return {
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-SIGN": sign,
        "X-BAPI-TIMESTAMP": ts,
        "X-BAPI-RECV-WINDOW": RECV_WINDOW,
        "Content-Type": "application/json"
    }

# =====================================================
# 🔎 VERIFICAR POSIÇÃO ABERTA (FUTURES LINEAR)
# =====================================================

def has_open_position(api_key, api_secret, symbol, env="real") -> bool:
    try:
        log_debug("bybit_client", "A verificar posição aberta", {
            "symbol": symbol,
            "env": env
        })

        ts = str(int(time.time() * 1000))
        query = f"category=linear&symbol={symbol}"

        sign_payload = ts + api_key + RECV_WINDOW + query
        sign = _sign(api_secret, sign_payload)

        url = f"{_base_url(env)}/v5/position/list?{query}"

        r = requests.get(
            url,
            headers=_headers(api_key, sign, ts),
            timeout=10
        )

        r.raise_for_status()
        data = r.json()

        positions = data.get("result", {}).get("list", [])
        log_debug("bybit_client", "Resultado posição aberta", positions)

        for p in positions:
            if float(p.get("size", 0)) != 0:
                return True

        return False

    except Exception as e:
        log_error("bybit_client", "Erro ao verificar posição aberta", e)
        # segurança máxima → assume posição aberta
        return True

# =====================================================
# 🚀 ENVIAR ORDEM MARKET + SL + TP
# =====================================================

def place_order(api_key, api_secret, symbol, side, qty, env="real", sl=None, tp=None):
    try:
        ts = str(int(time.time() * 1000))

        order_side = "Buy" if side.upper() == "BUY" else "Sell"

        payload = {
            "category": "linear",
            "symbol": symbol,
            "side": order_side,
            "orderType": "Market",
            "qty": str(qty),
            "timeInForce": "GTC"
        }

        if sl:
            payload["stopLoss"] = str(round(sl, 5))

        if tp:
            payload["takeProfit"] = str(round(tp, 5))

        body = json.dumps(payload)

        sign_payload = ts + api_key + RECV_WINDOW + body
        sign = _sign(api_secret, sign_payload)

        log_debug("bybit_client", "A enviar ordem MARKET", payload)

        url = f"{_base_url(env)}/v5/order/create"

        r = requests.post(
            url,
            headers=_headers(api_key, sign, ts),
            data=body,
            timeout=10
        )

        r.raise_for_status()
        result = r.json()

        log_debug("bybit_client", "Resposta Bybit (order)", result)
        return result

    except Exception as e:
        log_error("bybit_client", "Erro ao enviar ordem", e)
        return None

# =====================================================
# 📊 OBTER TRADES FECHADOS (REALIZED PNL)
# =====================================================

def get_closed_trades(api_key, api_secret, symbol, env="real", limit=20):
    """
    Retorna trades FECHADOS com PnL realizado
    """
    try:
        ts = str(int(time.time() * 1000))

        query = (
            f"category=linear"
            f"&symbol={symbol}"
            f"&limit={limit}"
        )

        sign_payload = ts + api_key + RECV_WINDOW + query
        sign = _sign(api_secret, sign_payload)

        url = f"{_base_url(env)}/v5/position/closed-pnl?{query}"

        log_debug("bybit_client", "A obter trades fechados", {
            "symbol": symbol,
            "env": env,
            "limit": limit
        })

        r = requests.get(
            url,
            headers=_headers(api_key, sign, ts),
            timeout=10
        )

        r.raise_for_status()
        data = r.json()

        trades = data.get("result", {}).get("list", [])

        parsed = []
        for t in trades:
            parsed_trade = {
                "orderId": t.get("orderId"),
                "symbol": t.get("symbol"),
                "side": t.get("side"),
                "entry_price": float(t.get("entryPrice", 0)),
                "exit_price": float(t.get("exitPrice", 0)),
                "qty": float(t.get("qty", 0)),
                "fee": float(t.get("cumExecFee", 0)),
                "pnl": float(t.get("closedPnl", 0)),
                "createdTime": t.get("createdTime"),
                "updatedTime": t.get("updatedTime")
            }
            parsed.append(parsed_trade)

        log_debug("bybit_client", "Trades fechados obtidos", parsed)
        return parsed

    except Exception as e:
        log_error("bybit_client", "Erro ao obter trades fechados", e)
        return []
