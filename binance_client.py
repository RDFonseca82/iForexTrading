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

def _send_protection_order(api_key, api_secret, symbol, side, order_type, price, env):
    try:
        ts = int(time.time() * 1000)

        params = (
            f"symbol={symbol}"
            f"&side={side}"
            f"&type={order_type}"
            f"&stopPrice={price}"
            f"&closePosition=true"
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
