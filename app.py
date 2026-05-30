import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide", page_title="Advanced Option Matrix")
st.title("🛡️ Institutional Risk Matrix & Option Task Router")

# List of sector ETFs to dynamically calculate breadth
SECTOR_ETFS = {
    "XLE": "Energy", "XLF": "Financials", "XLK": "Technology", 
    "XLY": "Consumer Disc", "XLP": "Consumer Staples", "XLV": "Healthcare",
    "XLI": "Industrials", "XLC": "Telecom", "XLB": "Materials", 
    "XLU": "Utilities", "XLRE": "Real Estate"
}

# --- CALCULATING SECTOR BREADTH & INDICES ---
@st.cache_data(ttl=900) # Cache for 15 mins to save API bandwidth
def get_market_breadth_and_macro():
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    spy = yf.Ticker("SPY").history(period="1y")
    spy_close = spy['Close'].iloc[-1]
    spy_50 = spy['Close'].rolling(50).mean().iloc[-1]
    spy_200 = spy['Close'].rolling(200).mean().iloc[-1]
    
    # Calculate how many sectors are performing well
    above_50_count = 0
    sector_summary = []
    
    for etf, name in SECTOR_ETFS.items():
        try:
            hist = yf.Ticker(etf).history(period="1y")
            close = hist['Close'].iloc[-1]
            ma50 = hist['Close'].rolling(50).mean().iloc[-1]
            ma200 = hist['Close'].rolling(200).mean().iloc[-1]
            
            is_above_50 = close > ma50
            if is_above_50:
                above_50_count += 1
                
            sector_summary.append({
                "Sector": name, "ETF": etf, "Price": round(close, 2),
                "Above 50MA": "🟢 Yes" if is_above_50 else "🔴 No",
                "Above 200MA": "🟢 Yes" if close > ma200 else "🔴 No"
            })
        except:
            pass
            
    breadth_pct = (above_50_count / len(SECTOR_ETFS)) * 100
    return vix, spy_close, spy_50, spy_200, breadth_pct, pd.DataFrame(sector_summary)


# --- INDIVIDUAL TICKER ANALYSIS (WITH VWAP, 50MA, 200MA) ---
@st.cache_data(ttl=300)
def analyze_ticker_suite(tickers, spy_returns):
    results = []
    for ticker in tickers:
        try:
            # 1. Fetch daily data for moving averages & alpha/beta
            daily_hist = yf.Ticker(ticker).history(period="1y")
            if daily_hist.empty: continue
            
            close = daily_hist['Close'].iloc[-1]
            ma50 = daily_hist['Close'].rolling(50).mean().iloc[-1]
            ma200 = daily_hist['Close'].rolling(200).mean().iloc[-1]
            
            # Alpha/Beta calculation
            asset_returns = daily_hist['Close'].pct_change().dropna()
            combined = pd.concat([asset_returns, spy_returns], axis=1).dropna()
            covariance = np.cov(combined.iloc[:,0], combined.iloc[:,1])[0][1]
            market_variance = np.var(combined.iloc[:,1])
            beta = covariance / market_variance
            
            # 2. Fetch intraday 1-minute data to compute true VWAP
            intraday = yf.Ticker(ticker).history(period="1d", interval="1m")
            if not intraday.empty:
                # VWAP = Sum(Price * Volume) / Sum(Volume)
                intraday['TP'] = (intraday['High'] + intraday['Low'] + intraday['Close']) / 3
                intraday['PV'] = intraday['TP'] * intraday['Volume']
                cum_pv = intraday['PV'].sum()
                cum_vol = intraday['Volume'].sum()
                vwap = cum_pv / cum_vol if cum_vol > 0 else close
            else:
                vwap = close # Fallback if extended hours or data interval fails
                
            # Entry/Exit VWAP Signals
            vwap_signal = "🟢 Long Bias (Above VWAP)" if close > vwap else "🔴 Short/Credit Bias (Below)"

            results.append({
                "Ticker": ticker,
                "Price": round(close, 2),
                "Intraday VWAP": round(vwap, 2),
                "VWAP Execution": vwap_signal,
                "vs 50MA": "🟢 Above" if close > ma50 else "🔴 Below",
                "vs 200MA": "🟢 Above" if close > ma200 else "🔴 Below",
                "Beta (β)": round(beta, 2)
            })
        except Exception as e:
            pass
    return pd.DataFrame(results)

# --- EXECUTION ENVIRONMENT ---

# Fetch Global Macro States First
spy_raw = yf.Ticker("SPY").history(period="1y")
spy_returns_raw = spy_raw['Close'].pct_change().dropna()
vix_v, spy_v, spy_50_v, spy_200_v, breadth_v, df_sectors = get_market_breadth_and_macro()

# UI Layout Columns
col_main, col_sidebar = st.columns([3, 1])

with col_sidebar:
    st.header("⚙️ Active Inventory")
    
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ["AAPL", "AMD", "NVDA"]
        
    with st.form("add_ticker_form", clear_on_submit=True):
        new_tk = st.text_input("Add Ticker String:").strip().upper()
        if st.form_submit_button("Append Target") and new_tk:
            if new_tk not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_tk)
                st.rerun()
                
    st.write("Monitored:", st.session_state.watchlist)
    if st.button("Reset Matrix Data"):
        st.session_state.watchlist = []
        st.rerun()

with col_main:
    # 1. Macro Dashboard Elements
    st.subheader("🌐 Global Market Dashboard")
    m1, m2, m3 = st.columns(3)
    m1.metric("VIX Volatility Shield", f"{vix_v:.2f}", "Elevated Risk (>22)" if vix_v > 22 else "Normal Pricing Environment")
    
    spy_perf_string = f"Above 50MA (${spy_50_v:.1f}) & 200MA (${spy_200_v:.1f})" if spy_v > spy_200_v else "Warning: Long Term Breakdown"
    m2.metric("S&P 500 (SPY)", f"${spy_v:.2f}", spy_perf_string)
    m3.metric("Sector Breadth Score (vs 50MA)", f"{breadth_v:.1f}%", "Healthy Sector Rotation" if breadth_v > 50 else "Narrow Market Breadth")
    
    # Expandable Sector Matrix View
    with st.expander("📊 View Detailed Sector Breadth Breakdown"):
        st.dataframe(df_sectors, hide_index=True, use_container_width=True)
        
    st.markdown("---")
    
    # 2. Automated Action Checklist Table
    st.subheader("📋 Core Watchlist Option Rules & Intraday Signals")
    if st.session_state.watchlist:
        df_ticker_analysis = analyze_ticker_suite(st.session_state.watchlist, spy_returns_raw)
        
        if not df_ticker_analysis.empty:
            st.dataframe(df_ticker_analysis, hide_index=True, use_container_width=True)
            
            # Dynamic Strategy Overlay Box
            st.markdown("### 💡 Automated Rules Implementation Engine")
            for _, row in df_ticker_analysis.iterrows():
                if row['vs 200MA'] == "🔴 Below":
                    st.error(f"⚠️ **{row['Ticker']} Rules Breach:** Stock is in a long-term bear phase (below 200MA). Avoid naked long calls or credit bull put options.")
                elif "🟢 Long Bias" in row['VWAP Execution'] and row['vs 50MA'] == "🟢 Above":
                    st.success(f"🔥 **{row['Ticker']} Setup Confirmed:** Bullish execution framework active. Trading above structural 50MA and current VWAP floor.")
        else:
            st.info("Awaiting valid API pipeline population strings.")
    else:
        st.info("Input a target symbol in the inventory panel to run the calculation engine.")
