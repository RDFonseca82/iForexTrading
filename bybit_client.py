import time, hmac, hashlib, requests, json
from logger import log_debug, log_error

def _base_url(env):
    return "https://api-testnet.bybit.com" if env == "testnet" else "https://api.bybit.com"

def _sign(secret, payload):
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

def _headers(key, sign, ts):
    return {
        "X-BAPI-API-KEY": key,
        "X-BAPI-SIGN": sign,
        "X-BAPI-TIMESTAMP": ts,
        "X-BAPI-RECV-WINDOW": "5000",
        "Content-Type": "application/json"
    }

# 🔎 VERIFICAR POSIÇÃO ABERTA
def has_open_position(api_key, api_secret, symbol, env):    
    log_debug("bybit_client", "A verificar posição aberta", {
        "symbol": symbol,
        "env": env
    })
    
    ts = str(int(time.time() * 1000))
    query = f"category=linear&symbol={symbol}"
    sign_payload = ts + api_key + "5000" + query
    sign = _sign(api_secret, sign_payload)

    url = _base_url(env) + "/v5/position/list?" + query
    r = requests.get(url, headers=_headers(api_key, sign, ts), timeout=10)
    r.raise_for_status()

    positions = r.json()["result"]["list"]
    log_debug("bybit_client", "Resultado posição aberta", positions)
    for p in positions:
        if float(p["size"]) > 0:
            return True
    return False

# 🚀 ENVIAR ORDEM
def place_order(api_key, api_secret, symbol, side, qty, env, sl, tp):
    
    log_debug("bybit_client", "A enviar ordem", payload)
    ts = str(int(time.time() * 1000))
    payload = {
        "category": "linear",
        "symbol": symbol,
        "side": "Buy" if side == "BUY" else "Sell",
        "orderType": "Market",
        "qty": str(qty),
        "stopLoss": str(round(sl, 2)),
        "takeProfit": str(round(tp, 2))
    }

    body = json.dumps(payload)
    sign_payload = ts + api_key + "5000" + body
    sign = _sign(api_secret, sign_payload)

    url = _base_url(env) + "/v5/order/create"
    r = requests.post(url, headers=_headers(api_key, sign, ts), data=body, timeout=10)
    r.raise_for_status()
    log_debug("bybit_client", "Resposta Bybit", r.json())
    return r.json()
