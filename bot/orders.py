from dataclasses import dataclass, asdict

from bot.client import BinanceAPIError, BinanceNetworkError
from bot.logging_config import setup_logger
from bot.validators import ValidationError, validate_symbol, validate_side, validate_order_type, validate_quantity, validate_price, validate_stop_price

logger = setup_logger(__name__)


@dataclass
class OrderResult:
    success: bool
    request_summary: dict
    response: dict | None = None
    error: str | None = None

    def as_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


def place_order(client, symbol, side, order_type, quantity, price=None, stop_price=None):
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        order_type = validate_order_type(order_type)
        quantity = validate_quantity(quantity)
        price = validate_price(price, order_type)
        stop_price = validate_stop_price(stop_price, order_type)
    except ValidationError as e:
        request_summary = {
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "quantity": quantity,
            "price": price,
            "stop_price": stop_price,
        }
        logger.warning("Validation failed: %s", e)
        return OrderResult(success=False, request_summary=request_summary, error=str(e))

    request_summary = {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "price": price,
        "stop_price": stop_price,
    }

    if order_type in ("LIMIT", "STOP"):
        request_summary["time_in_force"] = "GTC"

    logger.info("Placing order: %s", request_summary)

    try:
        response = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except BinanceAPIError as e:
        logger.error("Order rejected by Binance: %s | payload: %s", e, request_summary)
        return OrderResult(success=False, request_summary=request_summary, error=str(e))
    except BinanceNetworkError as e:
        logger.error("Network error placing order: %s | payload: %s", e, request_summary)
        return OrderResult(success=False, request_summary=request_summary, error=str(e))
    except Exception:
        logger.exception("Unexpected error placing order: %s", request_summary)
        raise

    logger.info("Order placed successfully: %s", response)
    return OrderResult(success=True, request_summary=request_summary, response=response)
