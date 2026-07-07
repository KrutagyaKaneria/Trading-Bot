# Trading Bot — Binance Futures Testnet (USDT-M)

A CLI tool for placing orders on **Binance Futures Testnet** (USDT-M perpetual contracts).

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # BinanceFuturesClient — HMAC-signed REST calls
│   ├── logging_config.py  # setup_logger() — file + console handlers
│   ├── orders.py          # place_order() — business logic + OrderResult
│   └── validators.py      # Pure validation functions + ValidationError
├── cli.py                 # argparse entry point
├── .env.example           # API key template
├── .gitignore
├── README.md
└── requirements.txt
```

## Setup

1.  **Create a testnet account** at https://testnet.binancefuture.com/
2.  **Generate an API key** from the testnet dashboard (HMAC, enable Futures trading).
3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure credentials:**

    ```bash
    cp .env.example .env
    # Edit .env — fill in BINANCE_API_KEY and BINANCE_API_SECRET
    ```

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Usage

### Non-interactive (argparse) mode

All commands require `--symbol`, `--side`, `--type`, and `--quantity`.

#### MARKET order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

#### LIMIT order

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 35000
```

#### STOP order (stop-limit)

```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP --quantity 0.01 --price 30000 --stop-price 31000
```

### Interactive mode

Run with no arguments or `--interactive`. Prompts are validated inline — bad input is rejected and re-prompted instead of crashing.

```
$ python cli.py
Interactive order entry

Symbol (e.g. BTCUSDT): BTCUSDT
Side:
  1. BUY
  2. SELL
Choice: 1
Order type:
  1. MARKET
  2. LIMIT
  3. STOP
Choice: 2
Quantity: 0.01
Price (required for LIMIT): 35000

--- Order Summary ---
  symbol: BTCUSDT
  side: BUY
  order_type: LIMIT
  quantity: 0.01
  price: 35000.0
  time_in_force: GTC

Confirm and place order? (y/n): y

--- Order Request Summary ---
  symbol: BTCUSDT
  side: BUY
  order_type: LIMIT
  quantity: 0.01
  price: 35000.0
  time_in_force: GTC

--- Order Response ---
  orderId: 123456789
  status: NEW
  executedQty: 0.000

✅ SUCCESS: order placed.
```

## Sample Output

```
--- Order Request Summary ---
  symbol: BTCUSDT
  side: BUY
  order_type: STOP
  quantity: 0.01
  price: 30000.0
  stop_price: 31000.0
  time_in_force: GTC

--- Order Response ---
  orderId: 123456789
  status: NEW
  executedQty: 0.000

✅ SUCCESS: order placed.
```

On failure:

```
❌ FAILED: Price must be greater than 0, got -5.
```

## Logging

All logs are written to `logs/trading_bot.log` with **DEBUG** level and `logs/` created automatically. The file handler uses **2 MB** max size with **5 backup** rotations (RotatingFileHandler).

Each log line includes:

```
2026-07-07 14:30:00 | INFO     | orders:53 | Placing order: ...
```

The console handler prints **INFO**+ messages in a shorter format.

## Error Handling

| Scenario | Behaviour |
|---|---|
| **Validation error** (bad symbol, missing price for LIMIT, etc.) | Returns a failed `OrderResult` without calling the API. CLI prints `❌ FAILED: <message>` and exits with code 1. |
| **Binance API error** (order rejected, insufficient balance, etc.) | Caught as `BinanceAPIError` in `orders.py`. Logged with full payload. Returns failed `OrderResult`. |
| **Network error** (timeout, connection refused) | Caught as `BinanceNetworkError` in `orders.py`. Logged with payload. Returns failed `OrderResult`. |
| **Unexpected exception** (bug, type error, etc.) | Logged with full stack trace via `logger.exception()`. **Re-raised** — bugs are not swallowed. |
| **Missing API credentials** | CLI prints a clear message and exits with code 1. No traceback. |
| **KeyboardInterrupt (Ctrl+C)** | Caught in `entry_point()`. Prints `Interrupted.` and exits with code 130. |

## Assumptions

- **USDT-M contracts only** — the `/fapi/v1/order` endpoint is for USDⓈ-M Futures.
- **Default `timeInForce`** — LIMIT and STOP orders use `GTC` (Good Till Cancelled). This is hard-coded in the client and not user-configurable.
- **Single order per CLI invocation** — the tool places one order and exits.
- **`newOrderRespType=RESULT`** — the API returns full execution details (`executedQty`, `avgPrice`, etc.) in the response.
- **HMAC signing** — API credentials must be HMAC keys (not RSA).
- **Float precision** — validation converts values to Python `float`. Binance API receives string representations via form-encoding.
