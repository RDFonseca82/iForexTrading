import time
import hmac
import hashlib
import requests

from logger import log_debug, log_error

# =====================================================
# UTILITÁRIOS
# =====================================================

def _base_url(env: str) -> str:
    """
    Define o endpoint conforme o ambiente
    """
    if env == "testnet":
        return "https://testnet.binancefuture.com"
    return "https://fapi.binance.com"


def _sign(secret: str, query: str) -> str:
    """
    Assinatura HMAC SHA256 exigida pela Binance
    """
    return hmac.new(
        secret.encode(),
        query.encode(),
        hashlib.sha256
    ).hexdigest()


# =====================================================
# VERIFICAR POSIÇÃO ABERTA
# =====================================================

def has_open_position(api_key, api_secret, symbol, env="real") -> bool:
    """
    Retorna True se existir posição aberta para o símbolo
    """

    try:
        ts = int(time.time() * 1000)
        query = f"timestamp={ts}"
        signature = _sign(api_secret, query)

        url = f"{_base_url(env)}/fapi/v2/positionRisk?{query}&signature={signature}"

        log_debug("binance", "A verificar posição aberta", {
            "symbol": symbol,
            "env": env
        })

        r = requests.get(
            url,
            headers={"X-MBX-APIKEY": api_key},
            timeout=10
        )

        r.raise_for_status()
        positions = r.json()

        for p in positions:
            if p["symbol"] == symbol and float(p["positionAmt"]) != 0:
                log_debug("binance", "Posição encontrada", p)
                return True

        return False

    except Exception as e:
        log_error("binance", "Erro ao verificar posição aberta", e)
        # segurança: se falhar, assume que há posição
        return True


# =====================================================
# ENVIAR ORDEM (MARKET + SL + TP)
# =====================================================

def place_order(api_key, api_secret, symbol, side, qty, env="real", sl=None, tp=None):
    """
    Envia ordem MARKET e cria SL/TP separados
    """

    try:
        base = _base_url(env)
        ts = int(time.time() * 1000)

        # -----------------------------
        # ORDEM MARKET
        # -----------------------------
        order_side = "BUY" if side.upper() == "LONG" else "SELL"

        params = (
            f"symbol={symbol}"
            f"&side={order_side}"
            f"&type=MARKET"
            f"&quantity={qty}"
            f"&timestamp={ts}"
        )

        signature = _sign(api_secret, params)

        url = f"{base}/fapi/v1/order?{params}&signature={signature}"

        log_debug("binance", "A enviar ordem MARKET", {
            "symbol": symbol,
            "side": order_side,
            "qty": qty,
            "env": env
        })

        r = requests.post(
            url,
            headers={"X-MBX-APIKEY": api_key},
            timeout=10
        )

        r.raise_for_status()
        result = r.json()

        # -----------------------------
        # STOP LOSS
        # -----------------------------
        if sl:
            _send_protection_order(
                api_key,
                api_secret,
                symbol,
                "SELL" if order_side == "BUY" else "BUY",
                "STOP_MARKET",
                sl,
                env
            )

        # -----------------------------
        # TAKE PROFIT
        # -----------------------------
        if tp:
            _send_protection_order(
                api_key,
                api_secret,
                symbol,
                "SELL" if order_side == "BUY" else "BUY",
                "TAKE_PROFIT_MARKET",
                tp,
                env
            )

        return result

    except Exception as e:
        log_error("binance", "Erro ao enviar ordem", e)
        return None


# =====================================================
# SL / TP (ORDENS DE PROTEÇÃO)
# =====================================================

def _send_protection_order(api_key, api_secret, symbol, order_type, price, env):
    try:
        ts = int(time.time() * 1000)
        price = round(float(price), 2)

        params = (
            f"symbol={symbol}"
            f"&type={order_type}"
            f"&stopPrice={price}"
            f"&closePosition=true"
            f"&workingType=MARK_PRICE"
            f"&timestamp={ts}"
        )

        signature = _sign(api_secret, params)
        url = f"{_base_url(env)}/fapi/v1/order?{params}&signature={signature}"

        log_debug("binance", f"A enviar {order_type}", {
            "symbol": symbol,
            "price": price,
            "env": env
        })

        r = requests.post(
            url,
            headers={"X-MBX-APIKEY": api_key},
            timeout=10
        )

        r.raise_for_status()
        return r.json()

    except Exception as e:
        log_error("binance", f"Erro ao enviar {order_type}", e)
        return None

def get_closed_trades(api_key, api_secret, symbol, env="real", limit=20):
    """
    Retorna trades FECHADOS (Binance Futures)
    """
    try:
        base = _base_url(env)
        ts = int(time.time() * 1000)

        # ----------------------------------
        # 1️⃣ Verificar se posição está fechada
        # ----------------------------------
        query_pos = f"timestamp={ts}"
        sign_pos = _sign(api_secret, query_pos)

        url_pos = f"{base}/fapi/v2/positionRisk?{query_pos}&signature={sign_pos}"

        r_pos = requests.get(
            url_pos,
            headers={"X-MBX-APIKEY": api_key},
            timeout=10
        )
        r_pos.raise_for_status()

        positions = r_pos.json()
        pos = next((p for p in positions if p["symbol"] == symbol), None)

        if not pos or float(pos["positionAmt"]) != 0:
            return []

        # ----------------------------------
        # 2️⃣ Buscar trades executados
        # ----------------------------------
        query = (
            f"symbol={symbol}"
            f"&limit={limit}"
            f"&timestamp={ts}"
        )

        sign = _sign(api_secret, query)
        url = f"{base}/fapi/v1/userTrades?{query}&signature={sign}"

        log_debug("binance", "A obter trades fechados", {
            "symbol": symbol,
            "env": env
        })

        r = requests.get(
            url,
            headers={"X-MBX-APIKEY": api_key},
            timeout=10
        )
        r.raise_for_status()

        trades = r.json()

        closed = []
        for t in trades:
            closed.append({
                "orderId": t["orderId"],
                "symbol": t["symbol"],
                "side": t["side"],
                "entry_price": float(t["price"]),
                "exit_price": float(t["price"]),  # market fill
                "qty": float(t["qty"]),
                "fee": float(t["commission"]),
                "pnl": float(t.get("realizedPnl", 0)),
                "createdTime": t["time"],
                "updatedTime": t["time"]
            })

        return closed

    except Exception as e:
        log_error("binance", "Erro ao obter trades fechados", e)
        return []
