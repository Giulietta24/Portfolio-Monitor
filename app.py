import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os

# Adjust primary layout engine settings to high-density wide format
st.set_page_config(layout="wide", page_title="Institutional Options Workspace")
st.markdown("### 🛡️ Institutional Risk Matrix & Option Task Router")

# --- HIGH DENSITY GLOBAL CSS INJECTION ---
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    h3 {margin-top: 0rem; margin-bottom: 0.5rem;}
    div[data-testid="stMetric"] {padding: 2px 10px; background-color: rgba(255,255,255,0.05); border-radius: 4px;}
    button[data-baseweb="tab"] {font-size: 13px !important; padding: 4px 12px !important;}
    .stDataFrame {font-size: 11px !important;}
    </style>
""", unsafe_allow_html=True)

# --- PERMANENT DB STORAGE ENGINE CONFIGURATION WITH ABSOLUTE PATHING ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "watchlist_db.json")

def load_permanent_watchlist():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            st.sidebar.error(f"Storage System Read Failure: {e}")
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
        {"Ticker": "IAI", "Label": "   📈 Broker-Dealers & Capital Markets", "Is_Parent": False}
    ],
    "3. Healthcare (XLV)": [
        {"Ticker": "XLV", "Label": "🏛️ BROAD HEALTHCARE SECTOR BASE", "Is_Parent": True},
        {"Ticker": "XBI", "Label": "   🧬 Biotech (High Volatility Alpha)", "Is_Parent": False},
        {"Ticker": "IHI", "Label": "   🩺 Medical Devices & Equipment", "Is_Parent": False}
    ],
    "4. Consumer Discretionary (XLY)": [
        {"Ticker": "XLY", "Label": "🏛️ BROAD CONSUMER DISCRETIONARY BASE", "Is_Parent": True},
        {"Ticker": "XHB", "Label": "   🏡 Homebuilders & Construction", "Is_Parent": False},
        {"Ticker": "XRT", "Label": "   🛒 Retailers & Digital Commerce", "Is_Parent": False}
    ],
    "5. Energy (XLE)": [
        {"Ticker": "XLE", "Label": "🏛️ BROAD ENERGY SECTOR BASE", "Is_Parent": True},
        {"Ticker": "XOP", "Label": "   🛢️ Oil & Gas Exploration & Production", "Is_Parent": False}
    ],
    "6. Industrials (XLI)": [
        {"Ticker": "XLI", "Label": "🏛️ BROAD INDUSTRIALS SECTOR BASE", "Is_Parent": True},
        {"Ticker": "XAR", "Label": "   ✈️ Aerospace & Defense", "Is_Parent": False},
        {"Ticker": "IYT", "Label": "   🚂 Transports & Logistics", "Is_Parent": False}
    ]
}

# --- SYNCHRONIZED INTERMARKET CAP-SIZE SECTOR TREE ---
CAP_SIZE_SECTOR_TREE = {
    "1. Mid-Cap Core Benchmarks": [
        {"Ticker": "MDY", "Label": "🏛️ S&P MIDCAP 400 CORE BASE", "Is_Parent": True},
        {"Ticker": "MDYG", "Label": "   🚀 Mid-Cap Growth Component", "Is_Parent": False},
        {"Ticker": "MDYV", "Label": "   🧱 Mid-Cap Value Component", "Is_Parent": False}
    ],
    "2. Small-Cap Core Benchmarks": [
        {"Ticker": "IWM", "Label": "🏛️ RUSSELL 2000 SMALL-CAP BASE", "Is_Parent": True},
        {"Ticker": "IWO", "Label": "   🚀 Small-Cap Growth Component", "Is_Parent": False},
        {"Ticker": "IWN", "Label": "   🧱 Small-Cap Value Component", "Is_Parent": False}
    ],
    "3. S&P Small-Cap Pure Segments": [
        {"Ticker": "SLY", "Label": "🏛️ S&P SMALLCAP 600 BASELINE", "Is_Parent": True},
        {"Ticker": "SLYG", "Label": "   🔥 S&P Small-Cap Pure Growth", "Is_Parent": False},
        {"Ticker": "SLYV", "Label": "   🌾 S&P Small-Cap Pure Value", "Is_Parent": False}
    ]
}

# --- DATA PROCESSING ENGINES ---

def process_matrix_calculations(sector_tree, slice_len, spy_returns):
    matrix_rows = []
    total_subsectors = 0
    subsectors_above_50 = 0
    
    for sector_group in sorted(list(sector_tree.keys())):
        for item in sector_tree[sector_group]:
            try:
                target_ticker = item["Ticker"]
                label_desc = item["Label"]
                is_parent = item["Is_Parent"]
                
                etf_engine = yf.Ticker(target_ticker)
                hist_full = etf_engine.history(period="1y")
                if hist_full.empty: continue
                
                close = hist_full['Close'].iloc[-1]
                ma50 = hist_full['Close'].rolling(50).mean().iloc[-1]
                ma200 = hist_full['Close'].rolling(200).mean().iloc[-1]
                
                hist_sliced = hist_full.tail(slice_len)
                highs = hist_sliced['High']
                lows = hist_sliced['Low']
                closes = hist_sliced['Close']
                
                tr1 = highs - lows
                tr2 = abs(highs - closes.shift(1))
                tr3 = abs(lows - closes.shift(1))
                true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr14 = true_range.rolling(14).mean().iloc[-1] if len(true_range) >= 14 else true_range.mean()
                
                ma3 = closes.rolling(3).mean().iloc[-1]
                ma14 = closes.rolling(14).mean().iloc[-1] if len(closes) >= 14 else closes.mean()
                
                upper_atr_target = ma3 + (1.5 * atr14)
                lower_atr_target = ma3 - (1.5 * atr14)
                
                if close > upper_atr_target: sector_tactical = "⚠️ Overextended Up"
                elif close < lower_atr_target: sector_tactical = "⚠️ Overextended Down"
                elif close > ma3: sector_tactical = "🟢 Momentum Bullish"
                else: sector_tactical = "🔴 Momentum Bearish"
                
                etf_returns = closes.pct_change().dropna()
                combined = pd.concat([etf_returns, spy_returns], axis=1).dropna()
                
                covariance = np.cov(combined.iloc[:,0], combined.iloc[:,1])[0][1]
                market_variance = np.var(combined.iloc[:,1])
                beta = covariance / market_variance
                
                # Fixed: Raw horizon alpha computation instead of forcing inaccurate serialization
                horizon_alpha = combined.iloc[:,0].mean() - (beta * combined.iloc[:,1].mean())
                
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
                    "3-Day Tactical Signal": sector_tactical,
                    "vs 14MA": "🟢 Above" if close > ma14 else "🔴 Below",
                    "Above 50MA": "🟢 Yes" if is_above_50 else "🔴 No",
                    "Above 200MA": "🟢 Yes" if close > ma200 else "🔴 No",
                    "Alpha (α)": f"{horizon_alpha:+.2%}",
                    "Beta (β)": round(beta, 2)
                })
            except: pass
    return pd.DataFrame(matrix_rows), total_subsectors, subsectors_above_50

@st.cache_data(ttl=900)
def get_unified_breadth_matrix(lookback_window):
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    spy_full = yf.Ticker("SPY").history(period="1y")
    spy_close = spy_full['Close'].iloc[-1]
    spy_50 = spy_full['Close'].rolling(50).mean().iloc[-1]
    spy_200 = spy_full['Close'].rolling(200).mean().iloc[-1]
    
    if lookback_window == "10d": slice_len = 10
    elif lookback_window == "1mo": slice_len = 21
    elif lookback_window == "3mo": slice_len = 63
    elif lookback_window == "6mo": slice_len = 126
    else: slice_len = 252
        
    spy_sliced = spy_full.tail(slice_len)
    spy_returns = spy_sliced['Close'].pct_change().dropna()
    
    df_macro, ts, sa = process_matrix_calculations(UNIFIED_SECTOR_TREE, slice_len, spy_returns)
    df_cap_size, _, _ = process_matrix_calculations(CAP_SIZE_SECTOR_TREE, slice_len, spy_returns)
            
    rotation_spreads = {}
    try:
        mdyg = yf.Ticker("MDYG").history(period="1y")['Close']
        mdyv = yf.Ticker("MDYV").history(period="1y")['Close']
        mid_ratio = (mdyg / mdyv).dropna()
        mid_ratio_sliced = mid_ratio.tail(slice_len)
        
        slyg = yf.Ticker("SLYG").history(period="1y")['Close']
        slyv = yf.Ticker("SLYV").history(period="1y")['Close']
        small_ratio = (slyg / slyv).dropna()
        small_ratio_sliced = small_ratio.tail(slice_len)
        
        m_pct = (mid_ratio_sliced.iloc[-1] - mid_ratio_sliced.iloc[0]) / mid_ratio_sliced.iloc[0]
        s_pct = (small_ratio_sliced.iloc[-1] - small_ratio_sliced.iloc[0]) / small_ratio_sliced.iloc[0]

        if m_pct >= 0:
            rotation_spreads["Mid_Cap"] = "🚀 Growth Leading"
            rotation_spreads["Mid_Playbook"] = "BUY Call Spreads"
        else:
            rotation_spreads["Mid_Cap"] = "🧱 Value Defensive"
            rotation_spreads["Mid_Playbook"] = "SELL Covered Calls / Condors"
        rotation_spreads["Mid_Pct"] = f"{m_pct:+.2%}"
        
        if s_pct >= 0:
            rotation_spreads["Small_Cap"] = "🔥 Growth Chasing"
            rotation_spreads["Small_Playbook"] = "BUY Bull Debit Spreads"
        else:
            rotation_spreads["Small_Cap"] = "🌾 Value Defensive"
            rotation_spreads["Small_Playbook"] = "SELL OTM Credit Spreads"
        rotation_spreads["Small_Pct"] = f"{s_pct:+.2%}"
    except Exception as e:
        rotation_spreads = {"Mid_Cap": "Error", "Mid_Playbook": str(e), "Mid_Pct": "0%", "Small_Cap": "Error", "Small_Playbook": str(e), "Small_Pct": "0%"}
                
    breadth_pct = (sa / ts) * 100 if ts > 0 else 0
    return vix, spy_close, spy_50, spy_200, breadth_pct, df_macro, df_cap_size, spy_returns, rotation_spreads

@st.cache_data(ttl=300)
def analyze_ticker_suite(tickers, lookback_window, spy_returns):
    results = []
    if lookback_window == "10d": slice_len = 10
    elif lookback_window == "1mo": slice_len = 21
    elif lookback_window == "3mo": slice_len = 63
    elif lookback_window == "6mo": slice_len = 126
    else: slice_len = 252
        
    for ticker in tickers:
        try:
            tk_engine = yf.Ticker(ticker)
            subsector = tk_engine.info.get("industry", "N/A")
            daily_hist_full = tk_engine.history(period="1y")
            if daily_hist_full.empty: continue
            
            close = daily_hist_full['Close'].iloc[-1]
            daily_hist = daily_hist_full.tail(slice_len)
            
            highs = daily_hist['High']
            lows = daily_hist['Low']
            closes = daily_hist['Close']
            
            tr1 = highs - lows
            tr2 = abs(highs - closes.shift(1))
            tr3 = abs(lows - closes.shift(1))
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr14 = true_range.rolling(14).mean().iloc[-1] if len(true_range) >= 14 else true_range.mean()
            
            ma3 = closes.rolling(3).mean().iloc[-1]
            ma14 = closes.rolling(14).mean().iloc[-1] if len(closes) >= 14 else closes.mean()
            ma50 = daily_hist_full['Close'].rolling(50).mean().iloc[-1]
            ma200 = daily_hist_full['Close'].rolling(200).mean().iloc[-1]
            
            upper_atr_target = ma3 + (1.5 * atr14)
            lower_atr_target = ma3 - (1.5 * atr14)
            
            if close > upper_atr_target: short_term_signal = "⚠️ Overextended Up"
            elif close < lower_atr_target: short_term_signal = "⚠️ Overextended Down"
            elif close > ma3: short_term_signal = "🟢 Short Momentum Bullish"
            else: short_term_signal = "🔴 Short Momentum Bearish"
                
            asset_returns = closes.pct_change().dropna()
            combined = pd.concat([asset_returns, spy_returns], axis=1).dropna()
            covariance = np.cov(combined.iloc[:,0], combined.iloc[:,1])[0][1]
            market_variance = np.var(combined.iloc[:,1])
            beta = covariance / market_variance
            horizon_alpha = combined.iloc[:,0].mean() - (beta * combined.iloc[:,1].mean())

            intraday = tk_engine.history(period="1d", interval="1m")
            vwap = (intraday['High'] + intraday['Low'] + intraday['Close'] / 3 * intraday['Volume']).sum() / intraday['Volume'].sum() if not intraday.empty else close
            vwap_signal = "🟢 Above VWAP" if close > vwap else "🔴 Below VWAP"

            results.append({
                "Ticker": ticker, "Subsector / Industry": subsector, "Price": round(close, 2), "Daily ATR": round(atr14, 2),
                "3-Day Tactical Signal": short_term_signal, "VWAP Intraday": vwap_signal, "Alpha (α)": f"{horizon_alpha:+.2%}",
                "Beta (β)": round(beta, 2), "vs 14MA": "🟢 Above" if close > ma14 else "🔴 Below",
                "vs 50MA": "🟢 Above" if close > ma50 else "🔴 Below", "vs 200MA": "🟢 Above" if close > ma200 else "🔴 Below"
            })
        except: pass
    return pd.DataFrame(results)

# --- INTERFACE LAYOUT STRUCTURE ---
col_main, col_sidebar = st.columns([3.3, 0.7])

with col_sidebar:
    st.markdown("##### ⚙️ Settings Desk")
    lookback_window = st.selectbox("Horizon:", options=["10d", "1mo", "3mo", "6mo", "1y"], index=1)
    st.markdown("---")
    
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = load_permanent_watchlist()
        
    with st.form("add_ticker_form", clear_on_submit=True):
        new_tk = st.text_input("Add Ticker:").strip().upper()
        if st.form_submit_button("Commit") and new_tk:
            if new_tk not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_tk)
                save_permanent_watchlist(st.session_state.watchlist)
                st.rerun()
                
    if st.button("Clear Board"):
        st.session_state.watchlist = []
        save_permanent_watchlist([])
        st.rerun()

# Run master core calculations
vix_v, spy_v, spy_50_v, spy_200_v, breadth_v, df_macro, df_cap_size, spy_returns_raw, spreads_v = get_unified_breadth_matrix(lookback_window)

with col_main:
    # ROW 1: PRIMARY INDEX BENCHMARKS 
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "VIX Volatility Index", 
        f"{vix_v:.2f}", 
        "Elevated Risk (>22)" if vix_v > 22 else "Normal Range"
    )
    m2.metric(
        "S&P 500 Proxy (SPY)", 
        f"${spy_v:.2f}", 
        f"Above 50MA (${spy_50_v:.1f}) & 200MA (${spy_200_v:.1f})" if spy_v > spy_200_v else "Down-trend Warning"
    )
    m3.metric(
        "Institutional Subsector Breadth", 
        f"{breadth_v:.1f}%", 
        "Healthy Expansion" if breadth_v > 50 else "Narrow Concentration"
    )
    
    # ROW 2: STRATEGY RADAR ROW
    st.markdown(f"###### 🔄 Style Rotation Matrix ({lookback_window} Options Playbook Router)")
    f1, f2 = st.columns(2)
    f1.metric(
        label=f"Mid-Cap Focus: {spreads_v['Mid_Cap']}", 
        value=spreads_v["Mid_Playbook"], 
        delta=spreads_v["Mid_Pct"]
    )
    f2.metric(
        label=f"Small-Cap Focus: {spreads_v['Small_Cap']}", 
        value=spreads_v["Small_Playbook"], 
        delta=spreads_v["Small_Pct"]
    )
    
    st.markdown("---")
    
    # --- DUAL WORKSPACE TAB CONTROLLER ENGINE ---
    tab1, tab2 = st.tabs(["🏛️ GICS Core Macro Sectors Matrix", "📊 Intermarket Cap-Size Breakdown Matrix"])
    
    # Unified view formatting array
    final_view_cols = [
        "Market Matrix Framework Structure", "Ticker", "Price", 
        "3-Day Tactical Signal", "vs 14MA", "Above 50MA", "Above 200MA", 
        "Alpha (α)", "Beta (β)"
    ]
    
    with tab1:
        if not df_macro.empty:
            df_m_sorted = df_macro.sort_values(by=["Sector Sorting Class", "Is Parent Class"], ascending=[True, False])
            st.dataframe(df_m_sorted[final_view_cols], hide_index=True, use_container_width=True, height=350)
            
    with tab2:
        if not df_cap_size.empty:
            # Sorted and printed with internal subsector hierarchy exactly like tab 1
            df_c_sorted = df_cap_size.sort_values(by=["Sector Sorting Class", "Is Parent Class"], ascending=[True, False])
            st.dataframe(df_c_sorted[final_view_cols], hide_index=True, use_container_width=True, height=350)
            
    st.markdown("---")
    
    # USER WATCHLIST TRACKER
    st.markdown(f"##### 📋 Watchlist Matrix ({lookback_window} Base)")
    if st.session_state.watchlist:
        df_ticker_analysis = analyze_ticker_suite(st.session_state.watchlist, lookback_window, spy_returns_raw)
        if not df_ticker_analysis.empty:
            st.dataframe(df_ticker_analysis, hide_index=True, use_container_width=True)
            
            for _, row in df_ticker_analysis.iterrows():
                if "Overextended Up" in row['3-Day Tactical Signal']:
                    st.warning(f"📈 **{row['Ticker']}:** Overextended Up. Look to deploy premium-selling strategies.")
                if "Momentum Bullish" in row['3-Day Tactical Signal'] and row['vs 14MA'] == "🟢 Above" and row['VWAP Intraday'] == "🟢 Above VWAP":
                    st.success(f"🔥 **{row['Ticker']}:** Momentum aligned. High conviction long entry conditions met.")
