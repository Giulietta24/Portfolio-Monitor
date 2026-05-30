import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Set broad workspace layout
st.set_page_config(layout="wide", page_title="Institutional Options Hub")
st.title("🛡️ Institutional Risk Matrix & Option Task Router")

# Major index sector ETFs for dynamic market breadth calculations
SECTOR_ETFS = {
    "XLE": "Energy", "XLF": "Financials", "XLK": "Technology", 
    "XLY": "Consumer Disc", "XLP": "Consumer Staples", "XLV": "Healthcare",
    "XLI": "Industrials", "XLC": "Telecom", "XLB": "Materials", 
    "XLU": "Utilities", "XLRE": "Real Estate"
}

# --- MODULE 1: GLOBAL BREADTH & INDICES ENGINE ---
@st.cache_data(ttl=900)  # Cached for 15 minutes to preserve API resource limits
def get_market_breadth_and_macro():
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    spy = yf.Ticker("SPY").history(period="1y")
    spy_close = spy['Close'].iloc[-1]
    spy_50 = spy['Close'].rolling(50).mean().iloc[-1]
    spy_200 = spy['Close'].rolling(200).mean().iloc[-1]
    
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


# --- MODULE 2: MULTI-TIME FRAME TICKER CORE ENGINE ---
@st.cache_data(ttl=300)  # Cached for 5 minutes
def analyze_ticker_suite(tickers, spy_returns):
    results = []
    for ticker in tickers:
        try:
            # 1. Fetch historical daily bars
            daily_hist = yf.Ticker(ticker).history(period="1y")
            if daily_hist.empty: 
                continue
            
            close = daily_hist['Close'].iloc[-1]
            highs = daily_hist['High']
            lows = daily_hist['Low']
            closes = daily_hist['Close']
            
            # --- Technical Metrics Calculations ---
            # True Range & 14-period ATR
            tr1 = highs - lows
            tr2 = abs(highs - closes.shift(1))
            tr3 = abs(lows - closes.shift(1))
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr14 = true_range.rolling(14).mean().iloc[-1]
            
            # Key System Averages
            ma3 = closes.rolling(3).mean().iloc[-1]
            ma14 = closes.rolling(14).mean().iloc[-1]
            ma50 = closes.rolling(50).mean().iloc[-1]
            ma200 = closes.rolling(200).mean().iloc[-1]
            
            # Dynamic Volatility Envelope Boundaries
            upper_atr_band = ma3 + (1.5 * atr14)
            lower_atr_band = ma3 - (1.5 * atr14)
            
            # Short-Term Tactical Rules Logic
            if close > upper_atr_band:
                short_term_signal = "⚠️ Overextended Up (Take Profit / Sell Calls)"
            elif close < lower_atr_band:
                short_term_signal = "⚠️ Overextended Down (Take Profit / Sell Puts)"
            elif close > ma3:
                short_term_signal = "🟢 Short Momentum Bullish (Ride 3MA)"
            else:
                short_term_signal = "🔴 Short Momentum Bearish"
                
            # Systemic Capital Asset Pricing Model (Alpha & Beta) Matrix
            asset_returns = closes.pct_change().dropna()
            combined = pd.concat([asset_returns, spy_returns], axis=1).dropna()
            covariance = np.cov(combined.iloc[:,0], combined.iloc[:,1])[0][1]
            market_variance = np.var(combined.iloc[:,1])
            beta = covariance / market_variance
            annualized_alpha = (combined.iloc[:,0].mean() - (beta * combined.iloc[:,1].mean())) * 252

            # 2. Fetch intraday 1-minute data streams for true institutional VWAP
            intraday = yf.Ticker(ticker).history(period="1d", interval="1m")
            if not intraday.empty:
                intraday['TP'] = (intraday['High'] + intraday['Low'] + intraday['Close']) / 3
                intraday['PV'] = intraday['TP'] * intraday['Volume']
                vwap = intraday['PV'].sum() / intraday['Volume'].sum()
            else:
                vwap = close
                
            vwap_signal = "🟢 Above VWAP" if close > vwap else "🔴 Below VWAP"

            results.append({
                "Ticker": ticker,
                "Price": round(close, 2),
                "Daily ATR": round(atr14, 2),
                "3-Day Tactical Signal": short_term_signal,
                "VWAP Intraday": vwap_signal,
                "Alpha (α)": f"{annualized_alpha:.2%}",
                "Beta (β)": round(beta, 2),
                "vs 14MA": "🟢 Above" if close > ma14 else "🔴 Below",
                "vs 50MA": "🟢 Above" if close > ma50 else "🔴 Below",
                "vs 200MA": "🟢 Above" if close > ma200 else "🔴 Below"
            })
        except Exception as e:
            pass
    return pd.DataFrame(results)


# --- MODULE 3: STREAMLIT WORKSPACE LAYOUT ---

# Compute Global Benchmarks Front-End
spy_raw = yf.Ticker("SPY").history(period="1y")
spy_returns_raw = spy_raw['Close'].pct_change().dropna()
vix_v, spy_v, spy_50_v, spy_200_v, breadth_v, df_sectors = get_market_breadth_and_macro()

# UI Layout Grid Splits
col_main, col_sidebar = st.columns([3, 1])

# Sidebar Controls: Option B Session State Form Integration
with col_sidebar:
    st.header("⚙️ Active Inventory")
    
    # Instantiate persistence state container array
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ["AAPL", "AMD", "NVDA", "TSLA"]
        
    with st.form("add_ticker_form", clear_on_submit=True):
        new_tk = st.text_input("Type Ticker String to Append:").strip().upper()
        if st.form_submit_button("Append Target") and new_tk:
            if new_tk not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_tk)
                st.rerun()
                
    st.write("Currently Monitored Inventory Asset Strings:", st.session_state.watchlist)
    if st.button("Reset Matrix Data Board"):
        st.session_state.watchlist = []
        st.rerun()

# Primary Workspace Matrix Dashboard Display
with col_main:
    # Macro Market Risk Status HUD Headers
    st.subheader("🌐 Global Market Dashboard")
    m1, m2, m3 = st.columns(3)
    m1.metric("VIX Volatility Shield", f"{vix_v:.2f}", "Elevated Risk (>22)" if vix_v > 22 else "Normal Market Environment")
    
    spy_perf_string = f"Above 50MA (${spy_50_v:.1f}) & 200MA (${spy_200_v:.1f})" if spy_v > spy_200_v else "Warning: Long Term Breakdown"
    m2.metric("S&P 500 (SPY)", f"${spy_v:.2f}", spy_perf_string)
    m3.metric("Sector Breadth Score (vs 50MA)", f"{breadth_v:.1f}%", "Healthy Sector Rotation" if breadth_v > 50 else "Narrow Market Breadth")
    
    # Expandable Market Breadth Module
    with st.expander("📊 View Detailed Sector Breadth Breakdown"):
        st.dataframe(df_sectors, hide_index=True, use_container_width=True)
        
    st.markdown("---")
    
    # Main Options Watchlist Operational Framework
    st.subheader("📋 Core Watchlist Option Rules & Intraday Signals")
    if st.session_state.watchlist:
        df_ticker_analysis = analyze_ticker_suite(st.session_state.watchlist, spy_returns_raw)
        
        if not df_ticker_analysis.empty:
            # Render main interactive data view structure
            st.dataframe(df_ticker_analysis, hide_index=True, use_container_width=True)
            
            # Dynamic Decision Engine Overlay Block
            st.markdown("### 💡 Automated Rules Implementation Engine")
            for _, row in df_ticker_analysis.iterrows():
                # Execution Logic Alert Flags
                if row['vs 200MA'] == "🔴 Below":
                    st.error(f"⚠️ **{row['Ticker']} Rules Breach:** Stock is in a long-term bear phase (below 200MA). Avoid buying long calls or selling naked bull put structures.")
                
                if "Overextended Up" in row['3-Day Tactical Signal']:
                    st.warning(f"📈 **{row['Ticker']} Target Warning:** Asset is stretched beyond 1.5 ATR from its 3MA. Implied Volatility (IV) is likely extended. Look to harvest long delta or deploy option premium selling structures.")
                
                if "Momentum Bullish" in row['3-Day Tactical Signal'] and row['vs 14MA'] == "🟢 Above" and row['VWAP Intraday'] == "🟢 Above VWAP":
                    st.success(f"🔥 **{row['Ticker']} High-Conviction Setup:** Asset alignment is entirely bullish across micro-moments (3MA, VWAP) and key structural frames (14MA). Highly favorable framework for long delta setups or writing put credits.")
        else:
            st.info("Awaiting valid API pipeline population strings.")
    else:
        st.info("Input a target symbol in the inventory panel to run the calculation engine.")
