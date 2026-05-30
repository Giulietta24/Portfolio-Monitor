import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide", page_title="Automated Options Watchlist")
st.title("🤖 Automated Options Hub & Ticker Scanner")

# --- CORE AUTOMATION ENGINE ---
@st.cache_data(ttl=300)
def analyze_watchlist(tickers):
    # Fetch Market Context
    vix = yf.Ticker("^VIX").history(period="5d")['Close'].iloc[-1]
    spy_data = yf.Ticker("SPY").history(period="6mo")
    spy_close = spy_data['Close'].iloc[-1]
    spy_ma50 = spy_data['Close'].rolling(window=50).mean().iloc[-1]
    spy_returns = spy_data['Close'].pct_change().dropna()
    
    results = []
    
    for ticker in tickers:
        try:
            asset_data = yf.Ticker(ticker).history(period="6mo")
            if asset_data.empty:
                continue
                
            asset_close = asset_data['Close'].iloc[-1]
            asset_ma50 = asset_data['Close'].rolling(window=50).mean().iloc[-1]
            asset_returns = asset_data['Close'].pct_change().dropna()
            
            # Align historical arrays for Alpha/Beta
            combined = pd.concat([asset_returns, spy_returns], axis=1).dropna()
            combined.columns = ['Asset', 'Market']
            
            covariance = np.cov(combined['Asset'], combined['Market'])[0][1]
            market_variance = np.var(combined['Market'])
            beta = covariance / market_variance
            alpha = (combined['Asset'].mean() - (beta * combined['Market'].mean())) * 252

            # --- AUTOMATED CHECKLIST RULES ---
            # Rule 1: High Volatility Protection (VIX Check)
            vix_check = "✅ Safe (<22)" if vix < 22 else "❌ High Risk (>22)"
            
            # Rule 2: Market Trend Check (SPY over 50MA)
            spy_check = "✅ Bullish" if spy_close > spy_ma50 else "❌ Bearish"
            
            # Rule 3: Asset Trend Alignment (Asset over 50MA)
            trend_check = "✅ Above 50MA" if asset_close > asset_ma50 else "❌ Below 50MA"
            
            # Rule 4: Systemic Risk Shield (Is it a high beta trap?)
            beta_check = "✅ Stable Asset" if beta < 1.3 else "⚠️ High Beta"

            # Rule 5: Alpha Generation Validation
            alpha_check = "✅ Positive α" if alpha > 0 else "❌ Negative α"

            results.append({
                "Ticker": ticker,
                "Price": round(asset_close, 2),
                "Beta (β)": round(beta, 2),
                "Alpha (α)": f"{alpha:.2%}",
                "VIX Shield": vix_check,
                "Market Index Trend": spy_check,
                "Asset Trend Match": trend_check,
                "Beta Stability": beta_check,
                "Alpha Validation": alpha_check
            })
        except Exception:
            pass # Skips invalid or restricted tickers cleanly
            
    return vix, spy_close, pd.DataFrame(results)

# --- RUNNING WORKSPACE ---
# Ticker inputs allowing ad-hoc strings to be created as items
st.subheader("🔍 Target Asset Definition")
default_watchlist = ["AAPL", "MSFT", "TSLA", "NVDA", "AMD"]
watchlist = st.multiselect(
    "Define custom ticker strings to batch run checks:", 
    options=default_watchlist, 
    default=default_watchlist,
    accept_new_options=True # Allows entering unique options symbols or companies
)

if watchlist:
    vix_index, spy_index, df_results = analyze_watchlist(watchlist)
    
    # Global Macro HUD
    st.markdown("### 🌐 Global Macro State")
    m1, m2 = st.columns(2)
    m1.metric("Live VIX Index Status", f"{vix_index:.2f}")
    m2.metric("S&P 500 Proxy (SPY)", f"${spy_index:.2f}")
    
    # Automated Grid Display
    st.markdown("### 📊 Live Positioning Verification Matrix")
    st.dataframe(
        df_results,
        hide_index=True,
        use_container_width=True
    )
    
    # Context-aware alerts based on calculations
    st.markdown("### 🚨 Strategic Checklist Advisories")
    failed_counts = (df_results.to_string().count("❌") + df_results.to_string().count("⚠️"))
    if failed_counts > 0:
        st.warning(f"Attention: There are **{failed_counts} flags** across your execution matrix. Confirm compliance before placing premium orders.")
else:
    st.info("Add or select ticker identifiers above to deploy automated system verification.")
