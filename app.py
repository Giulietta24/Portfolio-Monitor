import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os

# Adjust primary layout engine settings
st.set_page_config(layout="wide", page_title="Institutional Options Workspace")
st.title("🛡️ Institutional Risk Matrix & Option Task Router")

# --- PERMANENT DB STORAGE ENGINE CONFIGURATION ---
DB_FILE = "watchlist_db.json"

def load_permanent_watchlist():
    """Reads saved ticker array file from local system storage disk."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return ["AAPL", "AMD", "NVDA", "TSLA"]
    return ["AAPL", "AMD", "NVDA", "TSLA"]

def save_permanent_watchlist(watchlist):
    """Commits ticker string state array to local permanent system file."""
    try:
        with open(DB_FILE, "w") as f:
            json.dump(watchlist, f)
    except Exception as e:
        st.error(f"Storage System Write Failure: {e}")

# The highly-optimized, high-liquidity Institutional Subsector Framework
SECTOR_SUBSECTOR_TREE = {
    "Technology (XLK)": [
        {"Ticker": "XLK", "Label": "Broad Sector Base"},
        {"Ticker": "XSD", "Label": "⚡ Semiconductors (High Beta Core)"},
        {"Ticker": "IGV", "Label": "💻 Software & Cloud Services"}
    ],
    "Financials (XLF)": [
        {"Ticker": "XLF", "Label": "Broad Sector Base"},
        {"Ticker": "KRE", "Label": "🏦 Regional Banking"},
        {"Ticker": "IAI", "Label": "📈 Broker-Dealers & Capital Markets"}
    ],
    "Healthcare (XLV)": [
        {"Ticker": "XLV", "Label": "Broad Sector Base"},
        {"Ticker": "XBI", "Label": "🧬 Biotech (High Volatility)"},
        {"Ticker": "IHI", "Label": "🩺 Medical Devices & Equipment"}
    ],
    "Consumer Discretionary (XLY)": [
        {"Ticker": "XLY", "Label": "Broad Sector Base"},
        {"Ticker": "XHB", "Label": "🏡 Homebuilders"},
        {"Ticker": "XRT", "Label": "🛒 Retail & Commerce"}
    ],
    "Communications (XLC)": [
        {"Ticker": "XLC", "Label": "Broad Sector Base"},
        {"Ticker": "IYW", "Label": "📱 Social Media & Digital Networks"}
    ],
    "Energy (XLE)": [
        {"Ticker": "XLE", "Label": "Broad Sector Base"},
        {"Ticker": "XOP", "Label": "🛢️ Oil & Gas Exploration"},
        {"Ticker": "XES", "Label": "⚙️ Oil Field Services"}
    ],
    "Real Estate & REITs (XLRE)": [
        {"Ticker": "XLRE", "Label": "Broad Sector Base"},
        {"Ticker": "VNQ", "Label": "🏢 Equity REITs"}
    ],
    "Industrials (XLI)": [
        {"Ticker": "XLI", "Label": "Broad Sector Base"},
        {"Ticker": "XAR", "Label": "✈️ Aerospace & Defense"},
        {"Ticker": "IYT", "Label": "🚂 Transports & Dow Theory Shipping"}
    ],
    "Materials (XLB)": [
        {"Ticker": "XLB", "Label": "Broad Sector Base"},
        {"Ticker": "XME", "Label": "⛏️ Metals & Mining"}
    ],
    "Consumer Staples (XLP)": [
        {"Ticker": "XLP", "Label": "Broad Sector Base"},
        {"Ticker": "PBJ", "Label": "🥤 Food, Beverage & Household Goods"}
    ],
    "Utilities (XLU)": [
        {"Ticker": "XLU", "Label": "Broad Sector Base"},
        {"Ticker": "FIW", "Label": "💧 Water & Clean Power Utilities"}
    ]
}

# --- MODULE 1: COMPREHENSIVE MARKET BREADTH ENGINE ---

@st.cache_data(ttl=900)
def get_industry_breadth_matrix(lookback_window):
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    
    # Background baseline pull always uses 1-year history to calculate the 200MA correctly
    spy_full = yf.Ticker("SPY").history(period="1y")
    spy_close = spy_full['Close'].iloc[-1]
    spy_50 = spy_full['Close'].rolling(50).mean().iloc[-1]
    spy_200 = spy_full['Close'].rolling(200).mean().iloc[-1]
    
    if lookback_window == "3mo":
        spy_sliced = spy_full.tail(63)
    elif lookback_window == "6mo":
        spy_sliced = spy_full.tail(126)
    else:
        spy_sliced = spy_full
    spy_returns = spy_sliced['Close'].pct_change().dropna()
    
    matrix_rows = []
    total_constituents = 0
    above_50_count = 0
    
    for sector_group, subsectors in SECTOR_SUBSECTOR_TREE.items():
        for item in subsectors:
            try:
                target_ticker = item["Ticker"]
                label_desc = item["Label"]
                
                etf_engine = yf.Ticker(target_ticker)
                hist_full = etf_engine.history(period="1y")
                if hist_full.empty: continue
                
                close = hist_full['Close'].iloc[-1]
                ma50 = hist_full['Close'].rolling(50).mean().iloc[-1]
                ma200 = hist_full['Close'].rolling(200).mean().iloc[-1]
                
                if lookback_window == "3mo":
                    hist_sliced = hist_full.tail(63)
                elif lookback_window == "6mo":
                    hist_sliced = hist_full.tail(126)
                else:
                    hist_sliced = hist_full
                    
                etf_returns = hist_sliced['Close'].pct_change().dropna()
                combined = pd.concat([etf_returns, spy_returns], axis=1).dropna()
                
                covariance = np.cov(combined.iloc[:,0], combined.iloc[:,1])[0][1]
                market_variance = np.var(combined.iloc[:,1])
                beta = covariance / market_variance
                annualized_alpha = (combined.iloc[:,0].mean() - (beta * combined.iloc[:,1].mean())) * 252
                
                is_above_50 = close > ma50
                if "base" not in label_desc.lower():
                    total_constituents += 1
                    if is_above_50:
                        above_50_count += 1
                
                matrix_rows.append({
                    "Main Sector Group": sector_group,
                    "Liquid Subsector Focus": label_desc,
                    "Ticker": target_ticker,
                    "Price": round(close, 2),
                    "Annualized Alpha (α)": f"{annualized_alpha:.2%}",
                    "Beta (β)": round(beta, 2),
                    "Above 50MA": "🟢 Yes" if is_above_50 else "🔴 No",
                    "Above 200MA": "🟢 Yes" if close > ma200 else "🔴 No"
                })
            except:
                pass
                
    breadth_pct = (above_50_count / total_constituents) * 100 if total_constituents > 0 else 0
    return vix, spy_close, spy_50, spy_200, breadth_pct, pd.DataFrame(matrix_rows), spy_returns


@st.cache_data(ttl=300)
def analyze_ticker_suite(tickers, lookback_window, spy_returns):
    results = []
    for ticker in tickers:
        try:
            tk_engine = yf.Ticker(ticker)
            subsector = tk_engine.info.get("industry", "N/A")
            
            daily_hist_full = tk_engine.history(period="1y")
            if daily_hist_full.empty: continue
            
            close = daily_hist_full['Close'].iloc[-1]
            
            if lookback_window == "3mo":
                daily_hist = daily_hist_full.tail(63)
            elif lookback_window == "6mo":
                daily_hist = daily_hist_full.tail(126)
            else:
                daily_hist = daily_hist_full
                
            highs = daily_hist['High']
            lows = daily_hist['Low']
            closes = daily_hist['Close']
            
            tr1 = highs - lows
            tr2 = abs(highs - closes.shift(1))
            tr3 = abs(lows - closes.shift(1))
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr14 = true_range.rolling(14).mean().iloc[-1]
            
            ma3 = closes.rolling(3).mean().iloc[-1]
            ma14 = closes.rolling(14).mean().iloc[-1]
            ma50 = daily_hist_full['Close'].rolling(50).mean().iloc[-1]
            ma200 = daily_hist_full['Close'].rolling(200).mean().iloc[-1]
            
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
                
            asset_returns = closes.pct_change().dropna()
            combined = pd.concat([asset_returns, spy_returns], axis=1).dropna()
            covariance = np.cov(combined.iloc[:,0], combined.iloc[:,1])[0][1]
            market_variance = np.var(combined.iloc[:,1])
            beta = covariance / market_variance
            annualized_alpha = (combined.iloc[:,0].mean() - (beta * combined.iloc[:,1].mean())) * 252

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
        except:
            pass
    return pd.DataFrame(results)


# --- MODULE 2: SCREEN INTERFACE LAYOUT STRUCTURE ---

col_main, col_sidebar = st.columns([3, 1])

with col_sidebar:
    st.header("⚙️ Configuration Desk")
    lookback_window = st.selectbox(
        "Performance Lookback Horizon:",
        options=["3mo", "6mo", "1y"],
        index=1
    )
    
    st.markdown("---")
    st.subheader("➕ Permanent Watchlist Manager")
    
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = load_permanent_watchlist()
        
    with st.form("add_ticker_form", clear_on_submit=True):
        new_tk = st.text_input("Append Asset Ticker Identification:").strip().upper()
        if st.form_submit_button("Commit Changes") and new_tk:
            if new_tk not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_tk)
                save_permanent_watchlist(st.session_state.watchlist)
                st.rerun()
                
    st.write("Saved Tickers Tracker:", st.session_state.watchlist)
    if st.button("Wipe Inventory Board"):
        st.session_state.watchlist = []
        save_permanent_watchlist([])
        st.rerun()

# Run calculations
vix_v, spy_v, spy_50_v, spy_200_v, breadth_v, df_industry_breadth, spy_returns_raw = get_industry_breadth_matrix(lookback_window)

with col_main:
    st.subheader("🌐 Global Market Dashboard")
    m1, m2, m3 = st.columns(3)
    m1.metric("VIX Volatility Index", f"{vix_v:.2f}", "Elevated Risk (>22)" if vix_v > 22 else "Normal Range")
    m2.metric("S&P 500 Proxy (SPY)", f"${spy_v:.2f}", f"Above 50MA (${spy_50_v:.1f}) & 200MA (${spy_200_v:.1f})" if spy_v > spy_200_v else "Down-trend Warning")
    m3.metric("Institutional Subsector Breadth", f"{breadth_v:.1f}%", "Healthy Expansion" if breadth_v > 50 else "Narrow Concentration")
    
    # PATCHED EXPANDER MATRIX VIEW
    with st.expander(f"📊 View Complete Line-by-Line 11-Sector Breadth Matrix ({lookback_window} Timeline)"):
        # FIXED: Sorting keys now exactly match dataframe column definitions
        df_sorted_view = df_industry_breadth.sort_values(by=["Main Sector Group", "Liquid Subsector Focus"], ascending=[True, False])
        
        # Enforce column viewing arrangement order
        ordered_columns = ["Main Sector Group", "Liquid Subsector Focus", "Ticker", "Price", "Annualized Alpha (α)", "Beta (β)", "Above 50MA", "Above 200MA"]
        df_sorted_view = df_sorted_view[ordered_columns]
        
        st.dataframe(df_sorted_view, hide_index=True, use_container_width=True)
        
    st.markdown("---")
    
    st.subheader(f"📋 Watchlist Multi-Timeframe Matrix ({lookback_window} Base)")
    if st.session_state.watchlist:
        df_ticker_analysis = analyze_ticker_suite(st.session_state.watchlist, lookback_window, spy_returns_raw)
        
        if not df_ticker_analysis.empty:
            st.dataframe(df_ticker_analysis, hide_index=True, use_container_width=True)
            
            st.markdown("### 💡 Automated Rules Implementation Engine")
            for _, row in df_ticker_analysis.iterrows():
                if row['vs 200MA'] == "🔴 Below":
                    st.error(f"⚠️ **{row['Ticker']} Trend Breach:** Asset below long-term 200MA. Avoid long directional call strategies.")
                if "Overextended Up" in row['3-Day Tactical Signal']:
                    st.warning(f"📈 **{row['Ticker']} Extreme Extension:** Scaled past upper ATR threshold band. Great timing for harvesting premium or deploying credit spreads.")
                if "Momentum Bullish" in row['3-Day Tactical Signal'] and row['vs 14MA'] == "🟢 Above" and row['VWAP Intraday'] == "🟢 Above VWAP" and row['vs 50MA'] == "🟢 Above":
                    st.success(f"🔥 **{row['Ticker']} High-Conviction Long Setup:** Structural alignment achieved. Ideal setup for put credit writing or vertical debit entries.")
    else:
        st.info("Input a target symbol in the inventory panel to initialize tracking.")
