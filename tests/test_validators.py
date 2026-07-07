import pytest

from bot.validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)


class TestValidateSymbol:
    def test_valid(self):
        assert validate_symbol("BTCUSDT") == "BTCUSDT"
        assert validate_symbol("  ethusdt  ") == "ETHUSDT"
        assert validate_symbol("1000PEPE") == "1000PEPE"

    def test_empty(self):
        with pytest.raises(ValidationError, match="Symbol must not be empty."):
            validate_symbol("")
        with pytest.raises(ValidationError, match="Symbol must not be empty."):
            validate_symbol("   ")
        with pytest.raises(ValidationError, match="Symbol must not be empty."):
            validate_symbol(None)

    def test_too_short(self):
        with pytest.raises(ValidationError, match="not valid"):
            validate_symbol("BTC")

    def test_too_long(self):
        with pytest.raises(ValidationError, match="not valid"):
            validate_symbol("ABCDEFGHIJKLMNOPQRSTUVWXYZ123")

    def test_special_characters(self):
        with pytest.raises(ValidationError, match="not valid"):
            validate_symbol("BTC/USDT")
        with pytest.raises(ValidationError, match="not valid"):
            validate_symbol("BTCUSDT!")

    def test_lowercase_normalized(self):
        assert validate_symbol("btcusdt") == "BTCUSDT"


class TestValidateSide:
    def test_valid(self):
        assert validate_side("BUY") == "BUY"
        assert validate_side("SELL") == "SELL"

    def test_case_insensitive(self):
        assert validate_side("buy") == "BUY"
        assert validate_side("Buy") == "BUY"
        assert validate_side("sell") == "SELL"

    def test_whitespace_stripped(self):
        assert validate_side("  BUY  ") == "BUY"

    def test_empty(self):
        with pytest.raises(ValidationError, match="Side must be BUY or SELL."):
            validate_side("")
        with pytest.raises(ValidationError, match="Side must be BUY or SELL."):
            validate_side(None)

    def test_invalid_value(self):
        with pytest.raises(ValidationError, match="Side 'BUYY' is not valid"):
            validate_side("BUYY")
        with pytest.raises(ValidationError, match="Side 'HOLD' is not valid"):
            validate_side("HOLD")


class TestValidateOrderType:
    def test_valid(self):
        assert validate_order_type("MARKET") == "MARKET"
        assert validate_order_type("LIMIT") == "LIMIT"
        assert validate_order_type("STOP") == "STOP"

    def test_case_insensitive(self):
        assert validate_order_type("market") == "MARKET"
        assert validate_order_type("Limit") == "LIMIT"
        assert validate_order_type("  stop  ") == "STOP"

    def test_empty(self):
        with pytest.raises(ValidationError, match="must be MARKET, LIMIT, or STOP."):
            validate_order_type("")
        with pytest.raises(ValidationError, match="must be MARKET, LIMIT, or STOP."):
            validate_order_type(None)

    def test_invalid_value(self):
        with pytest.raises(ValidationError, match="not valid"):
            validate_order_type("LIMITX")
        with pytest.raises(ValidationError, match="not valid"):
            validate_order_type("MARKETPEG")


class TestValidateQuantity:
    def test_valid_string(self):
        assert validate_quantity("0.01") == 0.01
        assert validate_quantity("100") == 100.0

    def test_valid_numeric(self):
        assert validate_quantity(0.01) == 0.01
        assert validate_quantity(1) == 1.0

    def test_non_numeric(self):
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_quantity("abc")
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_quantity("12abc")
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_quantity(None)

    def test_zero(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_quantity(0)
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_quantity("0")

    def test_negative(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_quantity(-1)
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_quantity("-0.5")


class TestValidatePrice:
    def test_market_no_price(self):
        assert validate_price(None, "MARKET") is None

    def test_market_rejects_price(self):
        with pytest.raises(ValidationError, match="must not be provided for MARKET"):
            validate_price("100", "MARKET")

    def test_limit_valid(self):
        assert validate_price("100.5", "LIMIT") == 100.5
        assert validate_price(200, "LIMIT") == 200.0

    def test_limit_missing(self):
        with pytest.raises(ValidationError, match="Price is required for LIMIT"):
            validate_price(None, "LIMIT")

    def test_limit_negative(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_price("-1", "LIMIT")

    def test_limit_zero(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_price("0", "LIMIT")

    def test_limit_non_numeric(self):
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_price("free", "LIMIT")

    def test_stop_valid(self):
        assert validate_price("100.5", "STOP") == 100.5

    def test_stop_missing(self):
        with pytest.raises(ValidationError, match="Price is required for STOP"):
            validate_price(None, "STOP")

    def test_stop_negative(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_price("-5", "STOP")

    def test_stop_non_numeric(self):
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_price("nope", "STOP")


class TestValidateStopPrice:
    def test_stop_valid(self):
        assert validate_stop_price("200", "STOP") == 200.0
        assert validate_stop_price(199.5, "STOP") == 199.5

    def test_stop_missing(self):
        with pytest.raises(ValidationError, match="Stop price is required for STOP"):
            validate_stop_price(None, "STOP")

    def test_stop_negative(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_stop_price("-1", "STOP")

    def test_stop_zero(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_stop_price("0", "STOP")

    def test_stop_non_numeric(self):
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_stop_price("nope", "STOP")

    def test_not_for_market(self):
        assert validate_stop_price(None, "MARKET") is None
        with pytest.raises(ValidationError, match="must only be provided for STOP"):
            validate_stop_price("100", "MARKET")

    def test_not_for_limit(self):
        assert validate_stop_price(None, "LIMIT") is None
        with pytest.raises(ValidationError, match="must only be provided for STOP"):
            validate_stop_price("100", "LIMIT")
