import os

import streamlit as st
from dotenv import load_dotenv

from bot.client import BinanceFuturesClient
from bot.orders import place_order

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
    .field-group { margin-bottom: 0.8rem; }
    div[data-testid="stNotification"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>BINANCE FUTURES TERMINAL</h1>", unsafe_allow_html=True)
st.markdown("<div class='testnet-badge'>TESTNET • USDT-M</div>", unsafe_allow_html=True)

api_key = os.environ.get("BINANCE_API_KEY")
api_secret = os.environ.get("BINANCE_API_SECRET")
if not api_key or not api_secret:
    st.markdown(
        "<div class='failure-box'>BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env</div>",
        unsafe_allow_html=True,
    )
    st.stop()

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

if st.button("PLACE ORDER", type="primary", use_container_width=True):
    with st.spinner("Placing order on testnet..."):
        result = place_order(client, symbol, side, order_type, quantity, price, stop_price)

    side_tag = f"<span class='{'buy-text' if result.request_summary.get('side') == 'BUY' else 'sell-text'}'> {result.request_summary.get('side')}</span>"

    summary_rows = ""
    for key, val in result.request_summary.items():
        if val is not None:
            label = key.replace("_", " ").title()
            val_str = str(val)
            if key in ("price", "stop_price", "quantity"):
                val_str = f"<span class='metric-value'>{val}</span>"
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
                resp_lines += f"<div class='row'><span class='label'>{field}</span><span class='value'>{resp[field]}</span></div>"
        st.markdown(
            f"<div class='success-box'>"
            f"<div style='color:#00c853; font-weight:700; margin-bottom:0.5rem;'>"
            f"<span class='{'buy-text' if side == 'BUY' else 'sell-text'}'>SUCCESS</span> — order placed</div>"
            f"{resp_lines}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='failure-box'>"
            f"<div style='color:#ff1744; font-weight:700; margin-bottom:0.3rem;'>FAILED</div>"
            f"<span style='color:#d0d4dc;'>{result.error}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
