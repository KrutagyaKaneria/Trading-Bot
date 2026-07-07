import os
import subprocess
import sys
import time
from pathlib import Path

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


class TestValidators:
    def test_validate_symbol_valid(self):
        assert validate_symbol("  btcusdt  ") == "BTCUSDT"
        assert validate_symbol("ETHUSDT") == "ETHUSDT"

    def test_validate_symbol_empty(self):
        with pytest.raises(ValidationError, match="Symbol must not be empty"):
            validate_symbol("")
        with pytest.raises(ValidationError, match="Symbol must not be empty"):
            validate_symbol("   ")
        with pytest.raises(ValidationError, match="Symbol must not be empty"):
            validate_symbol(None)

    def test_validate_symbol_malformed(self):
        with pytest.raises(ValidationError, match="not valid"):
            validate_symbol("BTC")
        with pytest.raises(ValidationError, match="not valid"):
            validate_symbol("BTCUSDT!")

    def test_validate_side_valid(self):
        assert validate_side("buy") == "BUY"
        assert validate_side("SELL") == "SELL"
        assert validate_side("  Buy  ") == "BUY"

    def test_validate_side_invalid(self):
        with pytest.raises(ValidationError, match="Side 'BUYY' is not valid"):
            validate_side("buyy")
        with pytest.raises(ValidationError, match="Side must be BUY or SELL"):
            validate_side("")

    def test_validate_order_type_valid(self):
        assert validate_order_type("market") == "MARKET"
        assert validate_order_type("LIMIT") == "LIMIT"
        assert validate_order_type("  stop  ") == "STOP"

    def test_validate_order_type_invalid(self):
        with pytest.raises(ValidationError, match="not valid"):
            validate_order_type("limitx")
        with pytest.raises(ValidationError, match="must be MARKET, LIMIT, or STOP"):
            validate_order_type("")

    def test_validate_quantity_valid(self):
        assert validate_quantity("0.01") == 0.01
        assert validate_quantity(1) == 1.0
        assert validate_quantity("100") == 100.0

    def test_validate_quantity_non_numeric(self):
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_quantity("abc")
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_quantity(None)

    def test_validate_quantity_zero_or_negative(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_quantity(0)
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_quantity("-5")

    def test_validate_price_market(self):
        assert validate_price(None, "MARKET") is None
        with pytest.raises(ValidationError, match="must not be provided for MARKET"):
            validate_price("100", "MARKET")

    def test_validate_price_limit(self):
        assert validate_price("100.5", "LIMIT") == 100.5
        with pytest.raises(ValidationError, match="Price is required for LIMIT"):
            validate_price(None, "LIMIT")
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_price("-1", "LIMIT")

    def test_validate_price_stop(self):
        assert validate_price("100.5", "STOP") == 100.5
        with pytest.raises(ValidationError, match="Price is required for STOP"):
            validate_price(None, "STOP")
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_price("nope", "STOP")

    def test_validate_stop_price_only_stop(self):
        assert validate_stop_price("200", "STOP") == 200.0
        with pytest.raises(ValidationError, match="Stop price is required for STOP"):
            validate_stop_price(None, "STOP")
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_stop_price("0", "STOP")

    def test_validate_stop_price_not_for_market(self):
        assert validate_stop_price(None, "MARKET") is None
        with pytest.raises(ValidationError, match="must only be provided for STOP"):
            validate_stop_price("100", "MARKET")

    def test_validate_stop_price_not_for_limit(self):
        assert validate_stop_price(None, "LIMIT") is None
        with pytest.raises(ValidationError, match="must only be provided for STOP"):
            validate_stop_price("100", "LIMIT")


class TestCLI:

    def _run(self, args, cwd=None, env_add=None):
        base_env = {"PATH": os.environ["PATH"]}
        if env_add:
            base_env.update(env_add)
        return subprocess.run(
            [sys.executable, "cli.py", *args],
            capture_output=True, text=True, timeout=30,
            env=base_env, cwd=cwd,
        )

    def test_exits_1_when_credentials_missing(self):
        result = self._run(["--symbol", "BTCUSDT", "--side", "BUY", "--type", "MARKET", "--quantity", "0.01"])
        assert result.returncode == 1
        assert "BINANCE_API_KEY" in result.stderr

    def test_rejects_missing_price_for_limit(self):
        result = self._run(
            ["--symbol", "BTCUSDT", "--side", "BUY", "--type", "LIMIT", "--quantity", "0.01"],
            env_add={"BINANCE_API_KEY": "x", "BINANCE_API_SECRET": "x"},
        )
        assert result.returncode == 1
        assert "FAILED" in result.stdout
        assert "Price is required" in result.stdout

    def test_logs_warning_on_validation_failure(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        result = self._run(
            ["--symbol", "", "--side", "BUY", "--type", "MARKET", "--quantity", "0.01"],
            cwd=tmp_path,
            env_add={"BINANCE_API_KEY": "x", "BINANCE_API_SECRET": "x"},
        )
        assert result.returncode == 1
        assert "FAILED" in result.stdout

        log_file = log_dir / "trading_bot.log"
        assert log_file.exists(), f"Log file not found at {log_file}"
        content = log_file.read_text()
        assert "WARNING" in content
        assert "Symbol must not be empty" in content
