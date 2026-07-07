import pytest

from bot.client import BinanceAPIError, BinanceNetworkError
from bot.orders import OrderResult, place_order
from bot.validators import ValidationError


class FakeClient:
    """Fake BinanceFuturesClient for testing place_order without network calls."""

    def __init__(self, fail_with=None):
        self.fail_with = fail_with
        self.calls = []

    def place_order(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_with == "api":
            raise BinanceAPIError("Order rejected: insufficient balance")
        if self.fail_with == "network":
            raise BinanceNetworkError("Connection refused to testnet")
        return {"orderId": 123, "status": "NEW", "executedQty": "0.000", "avgPrice": "0.000"}


class TestPlaceOrderValidationShortCircuits:
    """Validation failures must return a failed OrderResult without calling the client."""

    def test_bad_symbol(self):
        client = FakeClient()
        result = place_order(client, "", "BUY", "MARKET", "0.01")
        assert result.success is False
        assert "Symbol must not be empty" in result.error
        assert client.calls == []

    def test_bad_side(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "HOLD", "MARKET", "0.01")
        assert result.success is False
        assert "not valid" in result.error
        assert client.calls == []

    def test_bad_order_type(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "PEGGED", "0.01")
        assert result.success is False
        assert "not valid" in result.error
        assert client.calls == []

    def test_bad_quantity_non_numeric(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "MARKET", "abc")
        assert result.success is False
        assert "not a valid number" in result.error
        assert client.calls == []

    def test_bad_quantity_zero(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "MARKET", "0")
        assert result.success is False
        assert "must be greater than 0" in result.error
        assert client.calls == []

    def test_limit_missing_price(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "LIMIT", "0.01")
        assert result.success is False
        assert "Price is required" in result.error
        assert client.calls == []

    def test_stop_missing_stop_price(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "STOP", "0.01", price="30000")
        assert result.success is False
        assert "Stop price is required" in result.error
        assert client.calls == []

    def test_stop_missing_price(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "STOP", "0.01", stop_price="31000")
        assert result.success is False
        assert "Price is required" in result.error
        assert client.calls == []

    def test_market_with_price_rejected(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "MARKET", "0.01", price="100")
        assert result.success is False
        assert "must not be provided for MARKET" in result.error
        assert client.calls == []


class TestPlaceOrderSuccess:
    def test_market_order(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "MARKET", "0.01")
        assert result.success is True
        assert result.response == {"orderId": 123, "status": "NEW", "executedQty": "0.000", "avgPrice": "0.000"}
        assert len(client.calls) == 1
        call = client.calls[0]
        assert call["symbol"] == "BTCUSDT"
        assert call["side"] == "BUY"
        assert call["order_type"] == "MARKET"
        assert call["quantity"] == 0.01

    def test_limit_order(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "SELL", "LIMIT", "0.01", price="35000")
        assert result.success is True
        assert len(client.calls) == 1
        call = client.calls[0]
        assert call["price"] == 35000.0

    def test_stop_order(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "STOP", "0.01", price="30000", stop_price="31000")
        assert result.success is True
        assert len(client.calls) == 1
        call = client.calls[0]
        assert call["price"] == 30000.0
        assert call["stop_price"] == 31000.0


class TestPlaceOrderResultFields:
    def test_request_summary_includes_symbol_and_side(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "MARKET", "0.01")
        assert result.request_summary["symbol"] == "BTCUSDT"
        assert result.request_summary["side"] == "BUY"

    def test_request_summary_excludes_none_fields(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "MARKET", "0.01")
        assert "price" not in result.request_summary
        assert "stop_price" not in result.request_summary

    def test_request_summary_includes_time_in_force_for_limit(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "LIMIT", "0.01", price="35000")
        assert result.request_summary["time_in_force"] == "GTC"

    def test_request_summary_includes_time_in_force_for_stop(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "STOP", "0.01", price="30000", stop_price="31000")
        assert result.request_summary["time_in_force"] == "GTC"

    def test_as_dict_omits_none(self):
        client = FakeClient()
        result = place_order(client, "BTCUSDT", "BUY", "MARKET", "0.01")
        d = result.as_dict()
        assert "error" not in d
        assert d["success"] is True
        assert "response" in d


class TestPlaceOrderClientErrors:
    def test_binance_api_error(self):
        client = FakeClient(fail_with="api")
        result = place_order(client, "BTCUSDT", "BUY", "MARKET", "0.01")
        assert result.success is False
        assert "insufficient balance" in result.error
        assert len(client.calls) == 1

    def test_binance_network_error(self):
        client = FakeClient(fail_with="network")
        result = place_order(client, "BTCUSDT", "BUY", "MARKET", "0.01")
        assert result.success is False
        assert "Connection refused" in result.error
        assert len(client.calls) == 1

    def test_request_summary_present_on_api_error(self):
        client = FakeClient(fail_with="api")
        result = place_order(client, "BTCUSDT", "BUY", "MARKET", "0.01")
        assert result.request_summary["symbol"] == "BTCUSDT"

    def test_request_summary_present_on_network_error(self):
        client = FakeClient(fail_with="network")
        result = place_order(client, "BTCUSDT", "BUY", "MARKET", "0.01")
        assert result.request_summary["symbol"] == "BTCUSDT"


class TestPlaceOrderUnexpectedError:
    def test_re_raises_unexpected_exception(self):
        class BrokenClient:
            def place_order(self, **kwargs):
                raise RuntimeError("something went terribly wrong")

        with pytest.raises(RuntimeError, match="something went terribly wrong"):
            place_order(BrokenClient(), "BTCUSDT", "BUY", "MARKET", "0.01")
