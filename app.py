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
            return ["AAPL", "AMD", "NVDA", "TSLA"] # Fallback defaults
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
        {"Ticker": "XLK", "Label": "Broad Technology Sector"},
        {"Ticker": "XSD", "Label": "⚡ Semiconductors (High Beta Core)"},
        {"Ticker": "IGV", "Label": "💻 Software & Cloud (Institutional Core)"}
    ],
    "Financials (XLF)": [
        {"Ticker": "XLF", "Label": "Broad Financials Sector"},
        {"Ticker": "KRE", "Label": "🏦 Regional Banking Subsector"},
        {"Ticker": "IAI", "Label": "📈 Broker-Dealers / Capital Markets"}
    ],
    "Healthcare (XLV)": [
        {"Ticker": "XLV", "Label": "Broad Healthcare Sector"},
        {"Ticker": "XBI", "Label": "🧬 Biotech Subsector (High Alpha/Volatility)"},
        {"Ticker": "IHI", "Label": "🩺 Medical Devices Subsector"}
    ],
    "Consumer Discretionary (XLY)": [
        {"Ticker": "XLY", "Label": "Broad Consumer Discretionary Sector"},
        {"Ticker": "XHB", "Label": "🏡 Homebuilders Subsector"},
        {"Ticker": "XRT", "Label": "🛒 Retail & Commerce Subsector"}
    ],
    "Communications (XLC)": [
        {"Ticker": "XLC", "Label": "Broad Communications Sector"},
        {"Ticker": "IYW", "Label": "📱 Social Media / Digital Networks Proxy"}
    ],
    "Energy (XLE)": [
        {"Ticker": "XLE", "Label": "Broad Energy Sector"},
        {"Ticker": "XOP", "Label": "🛢️ Oil & Gas Exploration subsector"},
        {"Ticker": "XES", "Label": "⚙️ Oil Field Services subsector"}
    ],
    "Real Estate & REITs (XLRE)": [
        {"Ticker": "XLRE", "Label": "Broad Real Estate Sector"},
        {"Ticker": "VNQ", "Label": "🏢 Liquid Equity REITs Subsector"}
    ],
    "Industrials (XLI)": [
        {"Ticker": "XLI", "Label": "Broad Industrials Sector"},
        {"Ticker": "XAR", "Label": "✈️ Aerospace & Defense subsector"},
        {"Ticker": "IYT", "Label": "🚂 Transports Subsector (Macro Health Indicator)"}
    ],
    "Materials (XLB)": [
        {"Ticker": "XLB", "Label": "Broad Materials Sector"},
        {"Ticker": "XME", "Label": "⛏️ Metals & Mining subsector"}
    ],
    "Consumer Staples (XLP)": [
        {"Ticker": "XLP", "Label": "Broad Consumer Staples Sector"},
        {"Ticker": "PBJ", "Label": "🥤 Food & Beverage subsector"}
    ],
    "Utilities (XLU)": [
        {"Ticker": "XLU", "Label": "Broad Utilities Sector"},
        {"Ticker": "FIW", "Label": "💧 Clean Water Infrastructure"}
    ]
}

# --- MODULE 1: COMPREHENSIVE MARKET BREADTH ENGINE ---

@st.cache_data(ttl=900)
def get_industry_breadth_matrix(lookback_window):
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    spy = yf.Ticker("SPY").history(period=lookback_window)
    spy_close = spy['Close'].iloc[-1]
    spy_50 = spy['Close'].rolling(50).mean().iloc[-1] if len(spy) >= 50 else spy_close
    spy_200 = spy['Close'].rolling(200).mean().iloc[-1] if len(spy) >= 200 else spy_close
    spy_returns = spy['Close'].pct_change().dropna()
    
    matrix_rows = []
    total_constituents = 0
    above_50_count = 0
    
    for sector_group, subsectors in SECTOR_SUBSECTOR_TREE.items():
        for item in subsectors:
            try:
                target_ticker = item["Ticker"]
                label_desc = item["Label"]
                
                etf_engine = yf.Ticker(target_ticker)
                hist = etf_engine.history(period=lookback_window)
                if hist.empty: continue
                
                close = hist['Close'].iloc[-1]
                ma50 = hist['Close'].rolling(50).mean().iloc[-1] if len(hist) >= 50 else close
                ma200 = hist['Close'].rolling(200).mean().iloc[-1] if len(hist) >= 200 else close
                
                etf_returns = hist['Close'].pct_change().dropna()
                combined = pd.concat([etf_returns, spy_returns], axis=1).dropna()
                
                covariance = np.cov(combined.iloc[:,0], combined.iloc[:,1])[0][1]
                market_variance = np.var(combined.iloc[:,1])
                beta = covariance / market_variance
                annualized_alpha = (combined.iloc[:,0].mean() - (beta * combined.iloc[:,1].mean())) * 252
                
                is_above_50 = close > ma50
                if "sector" in label_desc.lower() or "proxy" in label_desc.lower() or "subsector" in label_desc.lower():
                    total_constituents += 1
                    if is_above_50:
                        above_50_count += 1
                
                matrix_rows.append({
                    "Main Sector Class": sector_group,
                    "Subsector / ETF Line Item": label_desc,
                    "ETF Ticker": target_ticker,
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
            daily_hist = tk_engine.history(period=lookback_window)
            if daily_hist.empty: continue
            
            close = daily_hist['Close'].iloc[-1]
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


# --- MODULE 2: INTERFACE LAYOUT STRUCTURE ---

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
    
    # Initialize session state directly from saved JSON file data framework
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = load_permanent_watchlist()
        
    with st.form("add_ticker_form", clear_on_submit=True):
        new_tk = st.text_input("Append Asset Ticker Identification:").strip().upper()
        if st.form_submit_button("Commit Changes") and new_tk:
            if new_tk not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_tk)
                save_permanent_watchlist(st.session_state.watchlist) # Commits to system file drive
                st.rerun()
                
    st.write("Saved Tickers Tracker:", st.session_state.watchlist)
    if st.button("Wipe Inventory Board"):
        st.session_state.watchlist = []
        save_permanent_watchlist([]) # Wipes local system storage database
        st.rerun()

# Compute the global 11-sector matrix models
vix_v, spy_v, spy_50_v, spy_200_v, breadth_v, df_industry_breadth, spy_returns_raw = get_industry_breadth_matrix(lookback_window)

with col_main:
    st.subheader("🌐 Global Market Dashboard")
    m1, m2, m3 = st.columns(3)
    m1.metric("VIX Volatility Index", f"{vix_v:.2f}", "Elevated Risk (>22)" if vix_v > 22 else "Normal Range")
    m2.metric("S&P 500 Proxy (SPY)", f"${spy_v:.2f}", f"Above 50MA (${spy_50_v:.1f}) & 200MA (${spy_200_v:.1f})" if spy_v > spy_200_v else "Down-trend Warning")
    m3.metric("Institutional Subsector Breadth", f"{breadth_v:.1f}%", "Healthy Expansion" if breadth_v > 50 else "Narrow Concentration")
    
    with st.expander(f"📊 View Complete Line-by-Line 11-Sector Breadth Matrix ({lookback_window} Timeline)"):
        df_sorted_view = df_industry_breadth.sort_values(by=["Main Sector Class", "Subsector / ETF Line Item"], ascending=[True, False])
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
