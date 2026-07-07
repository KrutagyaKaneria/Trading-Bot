import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logger
from bot.orders import place_order
from bot.validators import ValidationError

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


def main():
    load_dotenv()

    api_key = os.environ.get("BINANCE_API_KEY")
    api_secret = os.environ.get("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("Error: BINANCE_API_KEY and BINANCE_API_SECRET must be set in the environment or .env file.", file=sys.stderr)
        sys.exit(1)

    args = parse_args()

    client = BinanceFuturesClient(
        api_key=api_key,
        api_secret=api_secret,
        base_url=args.base_url,
    )

    result = place_order(
        client=client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.type,
        quantity=args.quantity,
        price=args.price,
        stop_price=args.stop_price,
    )

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
