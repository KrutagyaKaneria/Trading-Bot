import time
from dataclasses import dataclass, asdict

from bot.client import BinanceAPIError, BinanceNetworkError
from bot.logging_config import setup_logger
from bot.validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
    validate_twap_params,
)

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


@dataclass
class TwapResult:
    success: bool
    request_summary: dict
    slice_results: list[OrderResult]
    succeeded: int
    failed: int
    error: str | None = None


def place_twap_order(client, symbol, side, total_quantity, num_slices, interval_seconds):
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        total_quantity = validate_quantity(total_quantity)
        num_slices, interval_seconds = validate_twap_params(num_slices, interval_seconds)
    except ValidationError as e:
        request_summary = {
            "symbol": symbol,
            "side": side,
            "total_quantity": total_quantity,
            "num_slices": num_slices,
            "interval_seconds": interval_seconds,
        }
        logger.warning("TWAP validation failed: %s", e)
        return TwapResult(
            success=False,
            request_summary=request_summary,
            slice_results=[],
            succeeded=0,
            failed=0,
            error=str(e),
        )

    request_summary = {
        "symbol": symbol,
        "side": side,
        "total_quantity": total_quantity,
        "num_slices": num_slices,
        "interval_seconds": interval_seconds,
    }

    logger.info("TWAP order: %s", request_summary)

    slice_qty = total_quantity / num_slices
    slice_results = []

    for i in range(num_slices):
        logger.info("TWAP slice %d/%d: placing %s %s qty=%s", i + 1, num_slices, symbol, side, slice_qty)
        order_result = place_order(client, symbol, side, "MARKET", slice_qty)
        slice_results.append(order_result)
        if i < num_slices - 1:
            time.sleep(interval_seconds)

    succeeded = sum(1 for r in slice_results if r.success)
    failed = len(slice_results) - succeeded

    logger.info("TWAP complete: %d succeeded, %d failed", succeeded, failed)

    return TwapResult(
        success=failed == 0,
        request_summary=request_summary,
        slice_results=slice_results,
        succeeded=succeeded,
        failed=failed,
    )
