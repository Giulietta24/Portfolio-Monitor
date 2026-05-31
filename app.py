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
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return ["AAPL", "AMD", "NVDA", "TSLA"]
    return ["AAPL", "AMD", "NVDA", "TSLA"]

def save_permanent_watchlist(watchlist):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(watchlist, f)
    except Exception as e:
        st.error(f"Storage System Write Failure: {e}")

# --- MASTER SECTOR TREE ---
UNIFIED_SECTOR_TREE = {
    "1. Technology (XLK)": [
        {"Ticker": "XLK", "Label": "🏛️ BROAD TECHNOLOGY SECTOR BASE", "Is_Parent": True},
        {"Ticker": "XSD", "Label": "   ⚡ Semiconductors (High Beta Core)", "Is_Parent": False},
        {"Ticker": "IGV", "Label": "   💻 Software & Cloud Services", "Is_Parent": False}
    ],
    "2. Financials (XLF)": [
        {"Ticker": "XLF", "Label": "🏛️ BROAD FINANCIALS SECTOR BASE", "Is_Parent": True},
        {"Ticker": "KRE", "Label": "   🏦 Regional Banking Hub", "Is_Parent": False},
        {"Ticker": "IAI", "Label": "   📈 Broker-Dealers & Capital Markets", "Is_Parent": False},
        {"Ticker": "KIE", "Label": "   🛡️ Insurance Companies", "Is_Parent": False}
    ],
    "3. Healthcare (XLV)": [
        {"Ticker": "XLV", "Label": "🏛️ BROAD HEALTHCARE SECTOR BASE", "Is_Parent": True},
        {"Ticker": "XBI", "Label": "   🧬 Biotech (High Volatility Alpha)", "Is_Parent": False},
        {"Ticker": "IHI", "Label": "   🩺 Medical Devices & Equipment", "Is_Parent": False},
        {"Ticker": "XPH", "Label": "   💊 Pharmaceuticals (Defensive Base)", "Is_Parent": False}
    ],
    "4. Consumer Discretionary (XLY)": [
        {"Ticker": "XLY", "Label": "🏛️ BROAD CONSUMER DISCRETIONARY BASE", "Is_Parent": True},
        {"Ticker": "XHB", "Label": "   🏡 Homebuilders & Construction", "Is_Parent": False},
        {"Ticker": "XRT", "Label": "   🛒 Retailers & Digital Commerce", "Is_Parent": False}
    ],
    "5. Communications (XLC)": [
        {"Ticker": "XLC", "Label": "🏛️ BROAD COMMUNICATIONS SECTOR BASE", "Is_Parent": True},
        {"Ticker": "IYW", "Label": "   📱 Tech Networks & Big Tech Platforms", "Is_Parent": False},
        {"Ticker": "XTL", "Label": "   📡 Telecom & Communication Hardware", "Is_Parent": False}
    ],
    "6. Energy (XLE)": [
        {"Ticker": "XLE", "Label": "🏛️ BROAD ENERGY SECTOR BASE", "Is_Parent": True},
        {"Ticker": "XOP", "Label": "   🛢️ Oil & Gas Exploration & Production", "Is_Parent": False},
        {"Ticker": "XES", "Label": "   ⚙️ Oil Field Equipment & Services", "Is_Parent": False}
    ],
    "7. Real Estate & REITs (XLRE)": [
        {"Ticker": "XLRE", "Label": "🏛️ BROAD REAL ESTATE SECTOR BASE", "Is_Parent": True},
        {"Ticker": "VNQ", "Label": "   🏢 Diversified Equity REITs Portfolio", "Is_Parent": False},
        {"Ticker": "RWR", "Label": "   🏗️ Commercial Real Estate Focus", "Is_Parent": False}
    ],
    "8. Industrials (XLI)": [
        {"Ticker": "XLI", "Label": "🏛️ BROAD INDUSTRIALS SECTOR BASE", "Is_Parent": True},
        {"Ticker": "XAR", "Label": "   ✈️ Aerospace & Defense", "Is_Parent": False},
        {"Ticker": "IYT", "Label": "   🚂 Transports & Dow Theory Logistics", "Is_Parent": False}
    ],
    "9. Materials (XLB)": [
        {"Ticker": "XLB", "Label": "🏛️ BROAD MATERIALS SECTOR BASE", "Is_Parent": True},
        {"Ticker": "XME", "Label": "   ⛏️ Metals, Mining & Steel Production", "Is_Parent": False},
        {"Ticker": "XLB2", "Label": "   🧪 Chemicals & Basic Materials Focus", "Is_Parent": False}
    ],
    "10. Consumer Staples (XLP)": [
        {"Ticker": "XLP", "Label": "🏛️ BROAD CONSUMER STAPLES BASE", "Is_Parent": True},
        {"Ticker": "PBJ", "Label": "   🥤 Food & Consumer Goods Products", "Is_Parent": False},
        {"Ticker": "XLP2", "Label": "   🧼 Household Goods & Defensives Hub", "Is_Parent": False}
    ],
    "11. Utilities (XLU)": [
        {"Ticker": "XLU", "Label": "🏛️ BROAD UTILITIES SECTOR BASE", "Is_Parent": True},
        {"Ticker": "FIW", "Label": "   💧 Water Utilities & Infrastructure", "Is_Parent": False},
        {"Ticker": "XLU2", "Label": "   ⚡ Traditional Regulated Electric Grids", "Is_Parent": False}
    ]
}

# --- DATA PROCESSING ENGINES ---

@st.cache_data(ttl=900)
def get_unified_breadth_matrix(lookback_window):
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    
    spy_full = yf.Ticker("SPY").history(period="1y")
    spy_close = spy_full['Close'].iloc[-1]
    spy_50 = spy_full['Close'].rolling(50).mean().iloc[-1]
    spy_200 = spy_full['Close'].rolling(200).mean().iloc[-1]
    
    # Precise lookback slicing to honor the user's timeline toggle configuration
    if lookback_window == "3mo":
        spy_sliced = spy_full.tail(63)
    elif lookback_window == "6mo":
        spy_sliced = spy_full.tail(126)
    else:
        spy_sliced = spy_full
        
    spy_returns = spy_sliced['Close'].pct_change().dropna()
    
    matrix_rows = []
    total_subsectors = 0
    subsectors_above_50 = 0
    
    for sector_group in sorted(list(UNIFIED_SECTOR_TREE.keys())):
        for item in UNIFIED_SECTOR_TREE[sector_group]:
            try:
                # Handle tracking duplicates cleanly by removing layout indexing flags
                raw_ticker = item["Ticker"]
                target_ticker = "XLB" if raw_ticker == "XLB2" else ("XLP" if raw_ticker == "XLP2" else ("XLU" if raw_ticker == "XLU2" else raw_ticker))
                
                label_desc = item["Label"]
                is_parent = item["Is_Parent"]
                
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
                if not is_parent:
                    total_subsectors += 1
                    if is_above_50: subsectors_above_50 += 1
                
                matrix_rows.append({
                    "Sector Sorting Class": sector_group,
                    "Is Parent Class": 1 if is_parent else 0,
                    "Market Matrix Framework Structure": label_desc,
                    "Ticker": target_ticker,
                    "Price": round(close, 2),
                    "Annualized Alpha (α)": f"{annualized_alpha:.2%}",
                    "Beta (β)": round(beta, 2),
                    "Above 50MA": "🟢 Yes" if is_above_50 else "🔴 No",
                    "Above 200MA": "🟢 Yes" if close > ma200 else "🔴 No"
                })
            except: pass
            
    # --- ACTIONABLE HIGH-ALPHA ROTATION SPREADS ENGINE ---
    # Replaces raw static numbers with mathematical alpha spreads
    rotation_spreads = {}
    try:
        # Mid-Caps Engine Setup
        mdyg = yf.Ticker("MDYG").history(period="1y")
        mdyv = yf.Ticker("MDYV").history(period="1y")
        mid_ratio = mdyg['Close'] / mdyv['Close']
        mid_ratio_ma20 = mid_ratio.rolling(20).mean()
        
        # Small-Caps Engine Setup
        slyg = yf.Ticker("SLYG").history(period="1y")
        slyv = yf.Ticker("SLYV").history(period="1y")
        small_ratio = slyg['Close'] / slyv['Close']
        small_ratio_ma20 = small_ratio.rolling(20).mean()
        
        if lookback_window == "3mo":
            m_pct = mid_ratio.tail(63).pct_change().sum()
            s_pct = small_ratio.tail(63).pct_change().sum()
        elif lookback_window == "6mo":
            m_pct = mid_ratio.tail(126).pct_change().sum()
            s_pct = small_ratio.tail(126).pct_change().sum()
        else:
            m_pct = mid_ratio.pct_change().sum()
            s_pct = small_ratio.pct_change().sum()

        rotation_spreads["Mid_Cap"] = "🚀 Growth Leading" if mid_ratio.iloc[-1] > mid_ratio_ma20.iloc[-1] else "🧱 Value Defensive"
        rotation_spreads["Mid_Pct"] = f"{m_pct:+.2%}"
        rotation_spreads["Small_Cap"] = "🔥 Growth Chasing" if small_ratio.iloc[-1] > small_ratio_ma20.iloc[-1] else "🌾 Value Defensive"
        rotation_spreads["Small_Pct"] = f"{s_pct:+.2%}"
    except:
        rotation_spreads = {"Mid_Cap": "N/A", "Mid_Pct": "0%", "Small_Cap": "N/A", "Small_Pct": "0%"}
                
    breadth_pct = (subsectors_above_50 / total_subsectors) * 100 if total_subsectors > 0 else 0
    return vix, spy_close, spy_50, spy_200, breadth_pct, pd.DataFrame(matrix_rows), spy_returns, rotation_spreads

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
            
            # Synchronize historical lookbacks with lookback toggle selections
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
            
            if close > upper_atr_target: short_term_signal = "⚠️ Overextended Up (Sell Vol)"
            elif close < lower_atr_target: short_term_signal = "⚠️ Overextended Down (Sell Puts)"
            elif close > ma3: short_term_signal = "🟢 Short Momentum Bullish"
            else: short_term_signal = "🔴 Short Momentum Bearish"
                
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
                "Ticker": ticker, "Subsector / Industry": subsector, "Price": round(close, 2), "Daily ATR": round(atr14, 2),
                "3-Day Tactical Signal": short_term_signal, "VWAP Intraday": vwap_signal, "Alpha (α)": f"{annualized_alpha:.2%}",
                "Beta (β)": round(beta, 2), "vs 14MA": "🟢 Above" if close > ma14 else "🔴 Below",
                "vs 50MA": "🟢 Above" if close > ma50 else "🔴 Below", "vs 200MA": "🟢 Above" if close > ma200 else "🔴 Below"
            })
        except: pass
    return pd.DataFrame(results)

# --- INTERFACE LAYOUT STRUCTURE ---

col_main, col_sidebar = st.columns([3, 1])

with col_sidebar:
    st.header("⚙️ Configuration Desk")
    lookback_window = st.selectbox("Performance Lookback Horizon:", options=["3mo", "6mo", "1y"], index=1)
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

# Run master calculations
vix_v, spy_v, spy_50_v, spy_200_v, breadth_v, df_unified, spy_returns_raw, spreads_v = get_unified_breadth_matrix(lookback_window)

with col_main:
    st.subheader("🌐 Global Market Dashboard")
    
    # ROW 1: CORE VOLATILITY & BENCHMARK INDEX METRICS
    m1, m2, m3 = st.columns(3)
    m1.metric("VIX Volatility Index", f"{vix_v:.2f}", "Elevated Risk (>22)" if vix_v > 22 else "Normal Range")
    m2.metric("S&P 500 Proxy (SPY)", f"${spy_v:.2f}", f"Above 50MA (${spy_50_v:.1f}) & 200MA (${spy_200_v:.1f})" if spy_v > spy_200_v else "Down-trend Warning")
    m3.metric("Institutional Subsector Breadth", f"{breadth_v:.1f}%", "Healthy Expansion" if breadth_v > 50 else "Narrow Concentration")
    
    # ROW 2: ACTIONABLE FACTOR ROTATION ALPHA ENGINE
    st.markdown(f"##### 🔄 Institutional Style-Factor Rotation Radar ({lookback_window} Velocity)")
    f1, f2 = st.columns(2)
    f1.metric("Mid-Cap Rotation Engine (MDYG/MDYV)", spreads_v["Mid_Cap"], f"Trend Velocity: {spreads_v['Mid_Pct']}")
    f2.metric("Small-Cap Speculative Alpha (SLYG/SLYV)", spreads_v["Small_Cap"], f"Trend Velocity: {spreads_v['Small_Pct']}")
    
    st.markdown("---")
    
    # UNIFIED SECTOR INTERNALS TABLE
    st.markdown("### 🏛️ Complete Unified 11-Sector Industry Matrix")
    if not df_unified.empty:
        df_display_sorted = df_unified.sort_values(
            by=["Sector Sorting Class", "Is Parent Class", "Market Matrix Framework Structure"], 
            ascending=[True, False, True]
        )
        
        final_view_cols = ["Market Matrix Framework Structure", "Ticker", "Price", "Annualized Alpha (α)", "Beta (β)", "Above 50MA", "Above 200MA"]
        df_display_clean = df_display_sorted[final_view_cols]
        
        st.dataframe(df_display_clean, hide_index=True, use_container_width=True, height=550)
        
    st.markdown("---")
    
    # USER WATCHLIST TRACKER (With All Restored Systems Active)
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
