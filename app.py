import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide", page_title="Options Position Hub")
st.title("🎯 Options Trading Position Hub & Market Monitor")

# --- DATA FETCHING & SIGNAL ENGINE ---
@st.cache_data(ttl=300) # Refresh data every 5 minutes
def get_market_signals(ticker_symbol="AAPL"):
    # Fetch Macro Indices
    spy = yf.Ticker("SPY").history(period="6mo")
    vix = yf.Ticker("^VIX").history(period="5d")
    asset = yf.Ticker(ticker_symbol).history(period="6mo")
    
    current_vix = vix['Close'].iloc[-1]
    current_spy = spy['Close'].iloc[-1]
    spy_ma50 = spy['Close'].rolling(window=50).mean().iloc[-1]
    
    # Calculate Daily Returns for Alpha/Beta
    spy_returns = spy['Close'].pct_change().dropna()
    asset_returns = asset['Close'].pct_change().dropna()
    
    # Align returns data
    combined = pd.concat([asset_returns, spy_returns], axis=1).dropna()
    combined.columns = ['Asset', 'Market']
    
    # Calculate Beta and Alpha
    covariance = np.cov(combined['Asset'], combined['Market'])[0][1]
    market_variance = np.var(combined['Market'])
    beta = covariance / market_variance
    alpha = combined['Asset'].mean() - (beta * combined['Market'].mean())
    # Annualized Alpha (approx 252 trading days)
    annualized_alpha = alpha * 252 

    return current_vix, current_spy, spy_ma50, beta, annualized_alpha

# Sidebar for position focus
st.sidebar.header("Active Position Deep Dive")
selected_ticker = st.sidebar.text_input("Ticker Symbol to Analyze", value="AAPL").upper()

try:
    vix_val, spy_val, spy_ma, beta_val, alpha_val = get_market_signals(selected_ticker)
except Exception as e:
    st.error("Error loading ticker data. Defaulting metrics.")
    vix_val, spy_val, spy_ma, beta_val, alpha_val = 20.0, 500.0, 490.0, 1.0, 0.0

# --- ALERT SYSTEM (Visual Indicators) ---
st.subheader("🚨 Market Condition Alerts")
col1, col2, col3, col4 = st.columns(4)

with col1:
    vix_status = "🔴 HIGH VOLATILITY" if vix_val > 23 else "🟢 NORMAL" if vix_val < 18 else "🟡 ELEVATED"
    st.metric("VIX Index", f"{vix_val:.2f}", help="Volatility Index")
    st.markdown(f"Status: **{vix_status}**")

with col2:
    spy_status = "🟢 BULLISH" if spy_val > spy_ma else "🔴 BEARISH"
    st.metric("SPY Price", f"${spy_val:.2f}", f"{(spy_val - spy_ma):.2f} vs 50MA")
    st.markdown(f"Trend: **{spy_status}**")

with col3:
    # Quick Breadth Proxy (Dummy logic for structural layout - can be built out with ticker baskets)
    breadth_signal = "🟢 STRONG" if spy_val > spy_ma and vix_val < 20 else "🔴 WEAK"
    st.metric("Market Breadth Proxy", breadth_signal, help="Proxy using SPY trend confirmation")

with col4:
    st.metric(f"{selected_ticker} Beta / Alpha", f"β: {beta_val:.2f}", f"α: {alpha_val:.2%}")
    if beta_val > 1.5:
        st.caption("⚠️ High Beta: Highly sensitive to SPY swings.")

st.markdown("---")

# --- CHECKLIST & TASK LIST MANAGEMENT ---
st.subheader("📋 Core Option Management Task List")

# Simple state tracking for tasks
if 'tasks' not in st.session_state:
    st.session_state.tasks = [
        {"task": "Check upcoming corporate earnings for active positions", "done": False, "type": "Risk"},
        {"task": "Evaluate VIX status before entering premium selling structures", "done": False, "type": "Macro"},
        {"task": "Manage or roll positions reaching 21 Days to Expiration (DTE)", "done": False, "type": "Execution"},
        {"task": "Check high beta exposures if SPY breaks below its 50MA", "done": False, "type": "Risk"}
    ]

# Form to add a new customized task
with st.expander("➕ Add Custom Task / Adjust Position Rule"):
    with st.form("new_task_form", clear_on_submit=True):
        new_task_desc = st.text_input("Task / Alert Criteria Description")
        task_type = st.selectbox("Category", ["Risk", "Macro", "Execution", "General"])
        submitted = st.form_submit_form_button = st.form_submit_button("Add to Board")
        if submitted and new_task_desc:
            st.session_state.tasks.append({"task": new_task_desc, "done": False, "type": task_type})
            st.rerun()

# Render checklist interactive items
for idx, t in enumerate(st.session_state.tasks):
    category_badge = f"[{t['type']}]"
    cb = st.checkbox(f"**{category_badge}** {t['task']}", value=t['done'], key=f"task_{idx}")
    st.session_state.tasks[idx]['done'] = cb

# --- CONDITIONAL ADVISORY ALERTS ---
st.subheader("💡 Dynamic Checklist Advisory")
if vix_val > 22:
    st.warning("⚠️ **Volatile Market Advisory:** VIX is elevated. Focus on closing or widening risk parameters on credit spreads rather than tight directional entries.")
if spy_val < spy_ma:
    st.error("📉 **Bearish Bias Alert:** SPY is trading below its 50-day moving average. Exercise caution with long-delta option positions (Calls / Bull Put Spreads).")