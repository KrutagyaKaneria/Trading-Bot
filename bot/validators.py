import re

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")
VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP"}


class ValidationError(ValueError):
    pass


def validate_symbol(symbol):
    if not symbol or not symbol.strip():
        raise ValidationError("Symbol must not be empty.")
    symbol = symbol.strip().upper()
    if not SYMBOL_PATTERN.match(symbol):
        raise ValidationError(
            f"Symbol '{symbol}' is not valid — must be 5-20 uppercase alphanumeric characters."
        )
    return symbol


def validate_side(side):
    if not side or not side.strip():
        raise ValidationError("Side must be BUY or SELL.")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Side '{side}' is not valid — must be BUY or SELL.")
    return side


def validate_order_type(order_type):
    if not order_type or not order_type.strip():
        raise ValidationError("Order type must be MARKET, LIMIT, or STOP.")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Order type '{order_type}' is not valid — must be MARKET, LIMIT, or STOP."
        )
    return order_type


def validate_quantity(quantity):
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity '{quantity}' is not a valid number.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than 0, got {qty}.")
    return qty


def validate_price(price, order_type):
    order_type = validate_order_type(order_type)
    if order_type == "MARKET":
        if price is not None:
            raise ValidationError("Price must not be provided for MARKET orders.")
        return None
    if price is None:
        raise ValidationError(f"Price is required for {order_type} orders.")
    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValidationError(f"Price '{price}' is not a valid number.")
    if p <= 0:
        raise ValidationError(f"Price must be greater than 0, got {p}.")
    return p


def validate_stop_price(stop_price, order_type):
    order_type = validate_order_type(order_type)
    if order_type != "STOP":
        if stop_price is not None:
            raise ValidationError("Stop price must only be provided for STOP orders.")
        return None
    if stop_price is None:
        raise ValidationError("Stop price is required for STOP orders.")
    try:
        sp = float(stop_price)
    except (TypeError, ValueError):
        raise ValidationError(f"Stop price '{stop_price}' is not a valid number.")
    if sp <= 0:
        raise ValidationError(f"Stop price must be greater than 0, got {sp}.")
    return sp
