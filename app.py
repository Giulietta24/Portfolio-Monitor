import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Adjust primary layout engine settings
st.set_page_config(layout="wide", page_title="Institutional Options Workspace")
st.title("🛡️ Institutional Risk Matrix & Option Task Router")

# Major index sector tracking matrix for baseline macro configurations
SECTOR_ETFS = {
    "XLE": "Energy", "XLF": "Financials", "XLK": "Technology", 
    "XLY": "Consumer Disc", "XLP": "Consumer Staples", "XLV": "Healthcare",
    "XLI": "Industrials", "XLC": "Telecom", "XLB": "Materials", 
    "XLU": "Utilities", "XLRE": "Real Estate"
}

# --- MODULE 1: MAIN CALCULATION ENGINES (MARKET AND SYMBOLS) ---

@st.cache_data(ttl=900)
def get_market_breadth_and_macro(lookback_window):
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    spy = yf.Ticker("SPY").history(period=lookback_window)
    spy_close = spy['Close'].iloc[-1]
    spy_50 = spy['Close'].rolling(50).mean().iloc[-1] if len(spy) >= 50 else spy_close
    spy_200 = spy['Close'].rolling(200).mean().iloc[-1] if len(spy) >= 200 else spy_close
    spy_returns = spy['Close'].pct_change().dropna()
    
    above_50_count = 0
    sector_summary = []
    
    for etf, name in SECTOR_ETFS.items():
        try:
            etf_ticker = yf.Ticker(etf)
            hist = etf_ticker.history(period=lookback_window)
            if hist.empty: continue
            
            close = hist['Close'].iloc[-1]
            ma50 = hist['Close'].rolling(50).mean().iloc[-1] if len(hist) >= 50 else close
            ma200 = hist['Close'].rolling(200).mean().iloc[-1] if len(hist) >= 200 else close
            
            # Fetch sector focus area (industry info mapping fallback)
            info = etf_ticker.info
            subsector = info.get("industry", "Diversified Sector Funds")
            
            # Calculate Risk-Adjusted Alpha and Beta for the specific Sector
            etf_returns = hist['Close'].pct_change().dropna()
            combined = pd.concat([etf_returns, spy_returns], axis=1).dropna()
            
            covariance = np.cov(combined.iloc[:,0], combined.iloc[:,1])[0][1]
            market_variance = np.var(combined.iloc[:,1])
            beta = covariance / market_variance
            annualized_alpha = (combined.iloc[:,0].mean() - (beta * combined.iloc[:,1].mean())) * 252
            
            is_above_50 = close > ma50
            if is_above_50:
                above_50_count += 1
                
            sector_summary.append({
                "Sector Group": name,
                "ETF": etf,
                "Subsector Focus": subsector,
                "Price": round(close, 2),
                "Sector Alpha (α)": f"{annualized_alpha:.2%}",
                "Sector Beta (β)": round(beta, 2),
                "Above 50MA": "🟢 Yes" if is_above_50 else "🔴 No",
                "Above 200MA": "🟢 Yes" if close > ma200 else "🔴 No"
            })
        except:
            pass
            
    breadth_pct = (above_50_count / len(SECTOR_ETFS)) * 100 if SECTOR_ETFS else 0
    return vix, spy_close, spy_50, spy_200, breadth_pct, pd.DataFrame(sector_summary), spy_returns


@st.cache_data(ttl=300)
def analyze_ticker_suite(tickers, lookback_window, spy_returns):
    results = []
    for ticker in tickers:
        try:
            tk_engine = yf.Ticker(ticker)
            
            # Extract fundamental subsector/industry profile classification data
            tk_info = tk_engine.info
            subsector = tk_info.get("industry", "N/A")
            
            # Pull daily price chart metrics using the custom sidebar window
            daily_hist = tk_engine.history(period=lookback_window)
            if daily_hist.empty: 
                continue
            
            close = daily_hist['Close'].iloc[-1]
            highs = daily_hist['High']
            lows = daily_hist['Low']
            closes = daily_hist['Close']
            
            # --- Dynamic Technical Calculations ---
            # Volatility Bounds (14-period ATR)
            tr1 = highs - lows
            tr2 = abs(highs - closes.shift(1))
            tr3 = abs(lows - closes.shift(1))
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr14 = true_range.rolling(14).mean().iloc[-1]
            
            ma3 = closes.rolling(3).mean().iloc[-1]
            ma14 = closes.rolling(14).mean().iloc[-1]
            ma50 = closes.rolling(50).mean().iloc[-1] if len(closes) >= 50 else close
            ma200 = closes.rolling(200).mean().iloc[-1] if len(closes) >= 200 else close
            
            upper_atr_target = ma3 + (1.5 * atr14)
            lower_atr_target = ma3 - (1.5 * atr14)
            
            if close > upper_atr_target:
                short_term_signal = "⚠️ Overextended Up (Sell Vol)"
            elif close < lower_atr_target:
                short_term_signal = "⚠️ Overextended Down (Sell Puts)"
            elif close > ma3:
                short_term_signal = "🟢 Short Momentum Bullish"
            else:
                short_term_signal = "🔴 Short Momentum Bearish"
                
            # --- Mathematical Alpha & Beta Risk Metrics ---
            asset_returns = closes.pct_change().dropna()
            combined = pd.concat([asset_returns, spy_returns], axis=1).dropna()
            
            covariance = np.cov(combined.iloc[:,0], combined.iloc[:,1])[0][1]
            market_variance = np.var(combined.iloc[:,1])
            beta = covariance / market_variance
            annualized_alpha = (combined.iloc[:,0].mean() - (beta * combined.iloc[:,1].mean())) * 252

            # --- Intraday Realtime Institutional VWAP Mapping ---
            intraday = tk_engine.history(period="1d", interval="1m")
            if not intraday.empty:
                intraday['TP'] = (intraday['High'] + intraday['Low'] + intraday['Close']) / 3
                intraday['PV'] = intraday['TP'] * intraday['Volume']
                vwap = intraday['PV'].sum() / intraday['Volume'].sum()
            else:
                vwap = close
                
            vwap_signal = "🟢 Above VWAP" if close > vwap else "🔴 Below VWAP"

            results.append({
                "Ticker": ticker,
                "Subsector / Industry": subsector,
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


# --- MODULE 2: STREAMLIT APP ENGINE LAYOUT ---

# Establish Primary Columns Grid Interface
col_main, col_sidebar = st.columns([3, 1])

# Dynamic Sidebar Framework Workspace
with col_sidebar:
    st.header("⚙️ Configuration Desk")
    
    # Toggle Controls for Lookback Windows Setup
    lookback_window = st.selectbox(
        "Select Performance Lookback Horizon:",
        options=["3mo", "6mo", "1y"],
        index=1,
        help="Adjusts the historical calculation timeframe for alpha, beta, and baseline technical indicators."
    )
    
    st.markdown("---")
    st.subheader("➕ Active Inventory Management")
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ["AAPL", "AMD", "NVDA", "TSLA"]
        
    with st.form("add_ticker_form", clear_on_submit=True):
        new_tk = st.text_input("Append Asset Ticker Identification:").strip().upper()
        if st.form_submit_button("Commit Changes") and new_tk:
            if new_tk not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_tk)
                st.rerun()
                
    st.write("Active Targets:", st.session_state.watchlist)
    if st.button("Wipe Inventory Board"):
        st.session_state.watchlist = []
        st.rerun()

# Execute Computations using the user selected timeline
vix_v, spy_v, spy_50_v, spy_200_v, breadth_v, df_sectors, spy_returns_raw = get_market_breadth_and_macro(lookback_window)

# Main Output Dashboard Container Layout
with col_main:
    st.subheader("🌐 Global Market Dashboard")
    m1, m2, m3 = st.columns(3)
    m1.metric("VIX Volatility Base", f"{vix_v:.2f}", "Elevated Risk (>22)" if vix_v > 22 else "Normal Range")
    
    spy_perf_string = f"Above 50MA (${spy_50_v:.1f}) & 200MA (${spy_200_v:.1f})" if spy_v > spy_200_v else "Warning: Long Term Breakdown"
    m2.metric("S&P 500 Proxy (SPY)", f"${spy_v:.2f}", spy_perf_string)
    m3.metric("Sector Breadth Base (vs 50MA)", f"{breadth_v:.1f}%", "Healthy Dynamic Rotation" if breadth_v > 50 else "Narrow Expansion")
    
    # Restructured Expander module displaying Subsectors, Alpha, and Beta for market segments
    with st.expander(f"📊 View Sector Breadth Matrix (Calculated via {lookback_window} Base)"):
        st.dataframe(df_sectors, hide_index=True, use_container_width=True)
        
    st.markdown("---")
    
    st.subheader(f"📋 Core Watchlist Option Rules & Intraday Signals ({lookback_window} Base)")
    if st.session_state.watchlist:
        df_ticker_analysis = analyze_ticker_suite(st.session_state.watchlist, lookback_window, spy_returns_raw)
        
        if not df_ticker_analysis.empty:
            # Display tracking data matrix layout view (including the restored vs 50MA filter)
            st.dataframe(df_ticker_analysis, hide_index=True, use_container_width=True)
            
            # Automated System Advisories Notification Rules Block
            st.markdown("### 💡 Automated Rules Implementation Engine")
            for _, row in df_ticker_analysis.iterrows():
                if row['vs 200MA'] == "🔴 Below":
                    st.error(f"⚠️ **{row['Ticker']} ({row['Subsector / Industry']}) Trend Breach:** Underlying is in a structural bear phase. Avoid long calls or bullish premium strategies.")
                
                if "Overextended Up" in row['3-Day Tactical Signal']:
                    st.warning(f"📈 **{row['Ticker']} Volatility Alert:** Asset has stretched past its 1.5 ATR volatility band limit. Implied Volatility is likely elevated. Look to harvest gains or deploy credit call spreads.")
                
                if "Momentum Bullish" in row['3-Day Tactical Signal'] and row['vs 14MA'] == "🟢 Above" and row['VWAP Intraday'] == "🟢 Above VWAP" and row['vs 50MA'] == "🟢 Above":
                    st.success(f"🔥 **{row['Ticker']} High-Conviction Long Setup:** Asset shows flawless structural alignment across short, intermediate, and cyclical moving averages. Excellent candidate for writing put credits or deploying directional debit structures.")
        else:
            st.info("Awaiting valid API pipeline asset strings.")
    else:
        st.info("Input a target symbol in the inventory panel to initialize tracking.")
