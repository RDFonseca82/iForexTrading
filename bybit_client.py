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
            if float(p.get("size", 0)) > 0:
                return True

        return False

    except Exception as e:
        log_error("bybit_client", "Erro ao verificar posição aberta", e)
        # segurança máxima → assume posição aberta
        return True

# =====================================================
# 🚀 ENVIAR ORDEM MARKET + SL + TP (BYBIT V5)
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

        # SL / TP opcionais (mas recomendados)
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

        log_debug("bybit_client", "Resposta Bybit", result)
        return result

    except Exception as e:
        log_error("bybit_client", "Erro ao enviar ordem", e)
        return None
