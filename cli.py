import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logger
from bot.orders import place_order
from bot.validators import ValidationError, validate_order_type, validate_price, validate_quantity, validate_side, validate_stop_price, validate_symbol

logger = setup_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Place an order on Binance Futures Testnet.")
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"], help="BUY or SELL")
    parser.add_argument("--type", required=True, choices=["MARKET", "LIMIT", "STOP", "market", "limit", "stop"], help="Order type")
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", help="Price (required for LIMIT/STOP)")
    parser.add_argument("--stop-price", help="Stop price (required for STOP)")
    parser.add_argument("--base-url", default="https://testnet.binancefuture.com", help="Binance Futures base URL")
    return parser.parse_args()


def _print_result(result):
    print()
    print("--- Order Request Summary ---")
    for key, val in result.request_summary.items():
        if val is not None:
            print(f"  {key}: {val}")

    if result.success:
        print()
        print("--- Order Response ---")
        if result.response:
            for field in ("orderId", "status", "executedQty", "avgPrice"):
                if field in result.response:
                    print(f"  {field}: {result.response[field]}")
        print()
        print("\u2705 SUCCESS: order placed.")
    else:
        print(f"\u274c FAILED: {result.error}")
        sys.exit(1)


def _prompt(prompt_text, validator, *validator_args):
    while True:
        raw = input(prompt_text).strip()
        try:
            return validator(raw, *validator_args)
        except ValidationError as e:
            print(f"  Invalid: {e}")


SIDE_MENU = {1: "BUY", 2: "SELL"}
TYPE_MENU = {1: "MARKET", 2: "LIMIT", 3: "STOP"}


def _pick(prompt_text, menu):
    print(prompt_text)
    for num, label in menu.items():
        print(f"  {num}. {label}")
    choices = {str(k): v for k, v in menu.items()}
    while True:
        raw = input("Choice: ").strip()
        resolved = choices.get(raw, raw)
        try:
            return validate_side(resolved) if "BUY" in menu.values() else validate_order_type(resolved)
        except ValidationError as e:
            print(f"  Invalid: {e}")


def interactive_mode(client):
    print("Interactive order entry\n")

    symbol = _prompt("Symbol (e.g. BTCUSDT): ", validate_symbol)
    side = _pick("Side:", SIDE_MENU)
    order_type = _pick("Order type:", TYPE_MENU)
    quantity = _prompt("Quantity: ", validate_quantity)
    price = None
    if order_type != "MARKET":
        price = _prompt(f"Price (required for {order_type}): ", validate_price, order_type)
    stop_price = None
    if order_type == "STOP":
        stop_price = _prompt("Stop price (required for STOP): ", validate_stop_price, order_type)

    summary = {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
    }
    if price is not None:
        summary["price"] = price
    if stop_price is not None:
        summary["stop_price"] = stop_price
    if order_type in ("LIMIT", "STOP"):
        summary["time_in_force"] = "GTC"

    print()
    print("--- Order Summary ---")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    while True:
        confirm = input("\nConfirm and place order? (y/n): ").strip().lower()
        if confirm == "y":
            break
        if confirm == "n":
            print("Order cancelled.")
            return

    result = place_order(client, symbol, side, order_type, quantity, price, stop_price)
    _print_result(result)


def main():
    load_dotenv()

    api_key = os.environ.get("BINANCE_API_KEY")
    api_secret = os.environ.get("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("Error: BINANCE_API_KEY and BINANCE_API_SECRET must be set in the environment or .env file.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) <= 1 or "--interactive" in sys.argv:
        base_url = "https://testnet.binancefuture.com"
        for i, arg in enumerate(sys.argv):
            if arg == "--base-url" and i + 1 < len(sys.argv):
                base_url = sys.argv[i + 1]
                break
        client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret, base_url=base_url)
        interactive_mode(client)
        return

    args = parse_args()
    client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret, base_url=args.base_url)

    result = place_order(
        client=client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.type,
        quantity=args.quantity,
        price=args.price,
        stop_price=args.stop_price,
    )

    _print_result(result)


def entry_point():
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except ValidationError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    entry_point()
