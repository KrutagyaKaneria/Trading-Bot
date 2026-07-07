import os
import random

import streamlit as st
from dotenv import load_dotenv

from bot.client import BinanceFuturesClient
from bot.orders import OrderResult, place_order
from bot.validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

load_dotenv()

st.set_page_config(
    page_title="Binance Futures Terminal",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .stApp {
        background-color: #0b0f1a;
        color: #d0d4dc;
    }
    .stApp header { display: none; }
    .main > div { padding-top: 1.2rem; }
    h1 {
        color: #e8ecef;
        font-family: 'Courier New', Courier, monospace;
        font-weight: 700;
        letter-spacing: 1px;
        font-size: 1.4rem;
        padding-bottom: 0;
        margin-bottom: 0.2rem;
    }
    .testnet-badge {
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.7rem;
        color: #f59e0b;
        letter-spacing: 2px;
        margin-bottom: 1.5rem;
    }
    .demo-badge {
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.7rem;
        color: #f59e0b;
        letter-spacing: 2px;
        margin-bottom: 0.5rem;
    }
    .demo-banner {
        background-color: #3d3000;
        border-left: 3px solid #f59e0b;
        padding: 1rem 1.2rem;
        border-radius: 2px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.85rem;
        margin-bottom: 1rem;
        color: #fbbf24;
    }
    label {
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 0.75rem !important;
        letter-spacing: 1px;
        color: #9ca3af !important;
        text-transform: uppercase;
    }
    .stTextInput input, .stNumberInput input {
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 0.95rem;
        background-color: #131926 !important;
        border: 1px solid #1f2937 !important;
        color: #e8ecef !important;
        border-radius: 2px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: none !important;
    }
    div[data-baseweb="select"] {
        font-family: 'Courier New', Courier, monospace !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #131926 !important;
        border: 1px solid #1f2937 !important;
        border-radius: 2px !important;
    }
    div[data-baseweb="select"] span {
        color: #e8ecef !important;
        font-family: 'Courier New', Courier, monospace !important;
    }
    .stButton button {
        font-family: 'Courier New', Courier, monospace;
        font-weight: 700;
        letter-spacing: 2px;
        background-color: #1f2937 !important;
        border: 1px solid #374151 !important;
        border-radius: 2px !important;
        color: #e8ecef !important;
        padding: 0.6rem 1rem !important;
        transition: none !important;
    }
    .stButton button:hover {
        background-color: #2d3748 !important;
        border-color: #4b5563 !important;
    }
    div.stButton > button[kind="primary"] {
        background-color: #2563eb !important;
        border-color: #3b82f6 !important;
        color: #fff !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #3b82f6 !important;
    }
    .buy-text { color: #00c853; font-weight: 700; }
    .sell-text { color: #ff1744; font-weight: 700; }
    .summary-card {
        background-color: #131926;
        border: 1px solid #1f2937;
        border-radius: 2px;
        padding: 1rem 1.2rem;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.85rem;
        margin-top: 1rem;
    }
    .summary-card .row {
        display: flex;
        padding: 0.2rem 0;
        border-bottom: 1px solid #1a2332;
    }
    .summary-card .label {
        color: #6b7280;
        width: 8rem;
        flex-shrink: 0;
    }
    .summary-card .value {
        color: #e8ecef;
        font-weight: 600;
    }
    .success-box {
        background-color: #003d1a;
        border-left: 3px solid #00c853;
        padding: 1rem 1.2rem;
        border-radius: 2px;
        font-family: 'Courier New', Courier, monospace;
        margin-top: 1rem;
    }
    .failure-box {
        background-color: #3d000a;
        border-left: 3px solid #ff1744;
        padding: 1rem 1.2rem;
        border-radius: 2px;
        font-family: 'Courier New', Courier, monospace;
        margin-top: 1rem;
    }
    hr { border-color: #1f2937; margin: 1.5rem 0; }
    div[data-testid="stNotification"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>BINANCE FUTURES TERMINAL</h1>", unsafe_allow_html=True)

api_key = os.environ.get("BINANCE_API_KEY")
api_secret = os.environ.get("BINANCE_API_SECRET")
demo_mode = not api_key or not api_secret

if demo_mode:
    st.markdown(
        "<div class='demo-banner'>&#9888;&#65039; Running in DEMO MODE — no API credentials found. "
        "Fill in .env with your Binance Testnet API key/secret to place real orders.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='demo-badge'>DEMO • USDT-M</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='testnet-badge'>TESTNET • USDT-M</div>", unsafe_allow_html=True)
    client = BinanceFuturesClient(
        api_key=api_key,
        api_secret=api_secret,
        base_url="https://testnet.binancefuture.com",
    )


symbol = st.text_input("Symbol", value="BTCUSDT", placeholder="e.g. BTCUSDT", key="symbol_input")

col1, col2 = st.columns(2)
with col1:
    side = st.selectbox("Side", ["BUY", "SELL"], key="side_select")
with col2:
    order_type = st.selectbox("Type", ["MARKET", "LIMIT", "STOP"], key="type_select")

quantity = st.number_input("Quantity", min_value=0.0, value=0.001, step=0.001, format="%.3f", key="qty_input")

price = None
if order_type != "MARKET":
    price = st.number_input("Price", min_value=0.0, step=0.01, format="%.2f", key="price_input")

stop_price = None
if order_type == "STOP":
    stop_price = st.number_input("Stop Price", min_value=0.0, step=0.01, format="%.2f", key="stop_input")

st.markdown("<br>", unsafe_allow_html=True)


def _render_result(result, is_demo):
    side_tag = (
        f"<span class='{'buy-text' if result.request_summary.get('side') == 'BUY' else 'sell-text'}'>"
        f" {result.request_summary.get('side')}</span>"
    )

    summary_rows = ""
    for key, val in result.request_summary.items():
        if val is not None:
            label = key.replace("_", " ").title()
            val_str = str(val)
            if key in ("price", "stop_price", "quantity"):
                val_str = f"<span class='value'>{val}</span>"
            elif key == "side":
                val_str = side_tag
            else:
                val_str = f"<span class='value'>{val_str}</span>"
            summary_rows += f"<div class='row'><span class='label'>{label}</span>{val_str}</div>"

    st.markdown(
        f"<div class='summary-card'>{summary_rows}</div>",
        unsafe_allow_html=True,
    )

    if result.success:
        resp = result.response or {}
        resp_lines = ""
        for field in ("orderId", "status", "executedQty", "avgPrice", "cumQuote"):
            if field in resp:
                resp_lines += (
                    f"<div class='row'><span class='label'>{field}</span>"
                    f"<span class='value'>{resp[field]}</span></div>"
                )

        if is_demo:
            title = "<span class='buy-text'>[DEMO] SUCCESS</span> — Simulated order — not sent to Binance."
        else:
            title = f"<span class='{'buy-text' if result.request_summary.get('side') == 'BUY' else 'sell-text'}'>SUCCESS</span> — order placed"

        st.markdown(
            f"<div class='success-box'><div style='color:#00c853; font-weight:700; "
            f"margin-bottom:0.5rem;'>{title}</div>{resp_lines}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='failure-box'>"
            f"<div style='color:#ff1744; font-weight:700; margin-bottom:0.3rem;'>FAILED</div>"
            f"<span style='color:#d0d4dc;'>{result.error}</span></div>",
            unsafe_allow_html=True,
        )


if st.button("PLACE ORDER", type="primary", use_container_width=True):
    if demo_mode:
        try:
            v_symbol = validate_symbol(symbol)
            v_side = validate_side(side)
            v_type = validate_order_type(order_type)
            v_qty = validate_quantity(quantity)
            v_price = validate_price(price, v_type)
            v_stop = validate_stop_price(stop_price, v_type)
        except ValidationError as e:
            st.markdown(
                f"<div class='failure-box'>"
                f"<div style='color:#ff1744;font-weight:700;margin-bottom:0.3rem;'>VALIDATION ERROR</div>"
                f"<span style='color:#d0d4dc;'>{e}</span></div>",
                unsafe_allow_html=True,
            )
            st.stop()

        request_summary = {
            "symbol": v_symbol,
            "side": v_side,
            "order_type": v_type,
            "quantity": v_qty,
        }
        if v_price is not None:
            request_summary["price"] = v_price
        if v_stop is not None:
            request_summary["stop_price"] = v_stop
        if v_type in ("LIMIT", "STOP"):
            request_summary["time_in_force"] = "GTC"

        if "BTC" in v_symbol:
            base_price = 65000.0
        elif "ETH" in v_symbol:
            base_price = 3500.0
        else:
            base_price = 100.0
        jitter = base_price * random.uniform(-0.01, 0.01)
        fake_avg_price = round(base_price + jitter, 2)

        is_market = v_type == "MARKET"
        fake_executed_qty = str(v_qty) if is_market else "0.000"

        if "order_id_counter" not in st.session_state:
            st.session_state.order_id_counter = 1000000
        st.session_state.order_id_counter += 1

        fake_response = {
            "orderId": st.session_state.order_id_counter,
            "status": "NEW",
            "executedQty": fake_executed_qty,
            "avgPrice": str(fake_avg_price),
        }
        if not is_market:
            fake_response["cumQuote"] = "0.000"

        result = OrderResult(
            success=True, request_summary=request_summary, response=fake_response
        )
        _render_result(result, is_demo=True)
    else:
        with st.spinner("Placing order on testnet..."):
            result = place_order(client, symbol, side, order_type, quantity, price, stop_price)
        _render_result(result, is_demo=False)
