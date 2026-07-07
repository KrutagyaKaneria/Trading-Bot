import hashlib
import hmac
import logging
import time
import urllib.parse

import requests


class BinanceAPIError(Exception):
    pass


class BinanceNetworkError(Exception):
    pass


class BinanceFuturesClient:
    def __init__(self, api_key, api_secret, base_url):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")

    def _sign(self, params):
        query = urllib.parse.urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def place_order(self, symbol, side, order_type, quantity, price=None, stop_price=None):
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "timestamp": int(time.time() * 1000),
        }

        if order_type in ("LIMIT", "STOP"):
            params["timeInForce"] = "GTC"
            params["price"] = price

        if order_type == "STOP":
            params["stopPrice"] = stop_price

        params["newOrderRespType"] = "RESULT"
        params["signature"] = self._sign(params)

        headers = {"X-MBX-APIKEY": self.api_key}

        try:
            resp = requests.post(
                f"{self.base_url}/fapi/v1/order",
                headers=headers,
                data=params,
            )
        except requests.RequestException as e:
            raise BinanceNetworkError(str(e))

        if resp.status_code != 200:
            try:
                err = resp.json()
                msg = err.get("msg", resp.text)
            except Exception:
                msg = resp.text
            raise BinanceAPIError(msg)

        return resp.json()

    def place_twap_order(self, symbol, side, total_quantity, num_slices, interval_seconds):
        slice_qty = total_quantity / num_slices
        slice_logger = logging.getLogger(f"{__name__}.twap")

        responses = []
        for i in range(num_slices):
            slice_logger.info(
                "TWAP slice %d/%d: %s %s qty=%s",
                i + 1, num_slices, symbol, side, slice_qty,
            )
            try:
                resp = self.place_order(symbol, side, "MARKET", slice_qty)
                responses.append(("ok", resp))
            except (BinanceAPIError, BinanceNetworkError) as e:
                slice_logger.error("TWAP slice %d/%d failed: %s", i + 1, num_slices, e)
                responses.append(("error", str(e)))

            if i < num_slices - 1:
                time.sleep(interval_seconds)

        return responses
