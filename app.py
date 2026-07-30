import streamlit as st
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta

from trading_engine import (
    fetch_data,
    run_ai_analysis,
    run_portfolio_simulation,
    get_alpaca_account_info,
    execute_live_trade
)

st.set_page_config(page_title="Advanced Algorithmic Trading Dashboard", layout="wide")
st.title("Algorithmic Trading Dashboard: Models, Candlesticks & Portfolio Diversification")

st.sidebar.header("Broker Connection (Alpaca)")
account_info = get_alpaca_account_info()

if account_info:
    st.sidebar.success(f"Account Status: {account_info['status']}")
    st.sidebar.metric("Buying Power", f"${account_info['buying_power']:,.2f}")
    st.sidebar.metric("Cash Balance", f"${account_info['cash']:,.2f}")
    st.sidebar.metric("Total Portfolio Value", f"${account_info['portfolio_value']:,.2f}")
else:
    st.sidebar.error("No active connection to Alpaca (check keys in .env)")

st.sidebar.markdown("---")
st.sidebar.header("Stock Basket Settings")

num_stocks = st.sidebar.number_input("How many stocks to analyze?", min_value=1, max_value=10, value=4)
default_stocks = ["AAPL", "MSFT", "GOOGL", "SPY", "NVDA", "AMZN", "TSLA", "META", "NFLX", "AMD"]

tickers = []
for i in range(num_stocks):
    default_val = default_stocks[i] if i < len(default_stocks) else ""
    ticker = st.sidebar.text_input(f"Stock Ticker {i + 1}:", value=default_val, key=f"stock_{i}")

    if ticker.strip():
        tickers.append(ticker.strip().upper())

tickers_input = ",".join(tickers)

end_date = date.today()
start_date = end_date - relativedelta(years=5)


@st.cache_data
def get_ai_data(t):
    return run_ai_analysis(t)


@st.cache_data
def get_portfolio_data(t_list):
    return run_portfolio_simulation(t_list)


if not tickers:
    tickers = ["AAPL"]

for ticker in tickers:
    st.write(f"## Stock Analysis: `{ticker}`")

    data = fetch_data(ticker, start=start_date, end=end_date)
    if not data.empty:
        st.write(f"#### Price History (Candlestick Chart): {ticker}")
        fig_candle = go.Figure(data=[go.Candlestick(x=data.index,
                                                    open=data['Open'],
                                                    high=data['High'],
                                                    low=data['Low'],
                                                    close=data['Close'])])
        fig_candle.update_layout(xaxis_rangeslider_visible=False, height=400, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_candle, width='stretch')
    else:
        st.warning(f"No price data found for {ticker}.")

    sim_data = get_ai_data(ticker)

    if sim_data is not None:
        st.write(f"#### AI Model Warfare: {ticker}")
        final_bh = sim_data['Buy_Hold_Portfolio'].iloc[-1]
        final_rf = sim_data['RF_Portfolio'].iloc[-1]
        final_xgb = sim_data['XGB_Portfolio'].iloc[-1]
        final_hr = sim_data['HighRisk_Portfolio'].iloc[-1]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Buy & Hold", f"${final_bh:,.2f}")
        c2.metric("Conservative (RF)", f"${final_rf:,.2f}")
        c3.metric("Aggressive (XGB)", f"${final_xgb:,.2f}")
        c4.metric("High Risk", f"${final_hr:,.2f}")

        last_xgb_signal = sim_data['Pred_XGB'].iloc[-1]
        last_rf_signal = sim_data['Pred_RF'].iloc[-1]

        st.markdown("---")
        st.subheader("System Forecast & Recommendation for Today:")

        col_rec1, col_rec2 = st.columns(2)
        with col_rec1:
            if last_xgb_signal == 1:
                st.success(f"XGBoost Model (Aggressive): Positive trend. Recommended to buy/hold {ticker}.")
            else:
                st.warning(f"XGBoost Model (Aggressive): Negative or volatile trend. Recommended to wait/avoid buying {ticker} right now.")

        with col_rec2:
            if last_rf_signal == 1:
                st.success(f"Random Forest Model (Conservative): Identified a secure entry opportunity for {ticker}.")
            else:
                st.info(f"Random Forest Model (Conservative): No clear buy signal currently for {ticker}.")

        fig_ind = go.Figure()
        fig_ind.add_trace(
            go.Scatter(x=sim_data.index, y=sim_data['Buy_Hold_Portfolio'], mode='lines', name='Buy & Hold',
                       line=dict(color='gray', dash='dot')))
        fig_ind.add_trace(go.Scatter(x=sim_data.index, y=sim_data['RF_Portfolio'], mode='lines', name='Conservative (RF)',
                                     line=dict(color='green', width=2)))
        fig_ind.add_trace(go.Scatter(x=sim_data.index, y=sim_data['XGB_Portfolio'], mode='lines', name='Aggressive (XGB)',
                                     line=dict(color='blue', width=2)))
        fig_ind.add_trace(
            go.Scatter(x=sim_data.index, y=sim_data['HighRisk_Portfolio'], mode='lines', name='High Risk',
                       line=dict(color='red', width=2)))

        fig_ind.update_layout(title=f"Performance Comparison for {ticker} ($10k Starting Capital)", height=400,
                              margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified")
        st.plotly_chart(fig_ind, width='stretch')

        st.write(f"**Automated Trade Execution (Broker Integration):**")
        if st.button(f"Submit Buy Order (1 Share) for {ticker}", key=f"trade_{ticker}"):
            success, message = execute_live_trade(ticker, qty=1)
            if success:
                st.success(message)
            else:
                st.error(message)

    else:
        st.warning(f"Not enough data to run simulator for {ticker}.")

    st.write("---")

st.subheader("Portfolio Diversification Simulator")

sim_results = get_portfolio_data(tickers_input)

if sim_results is not None:
    final_div = sim_results['Diversified_Portfolio'].iloc[-1]
    final_single = sim_results['Single_Stock_Benchmark'].iloc[-1]

    col1, col2 = st.columns(2)
    col1.metric("Diversified Portfolio (Full Basket)", f"${final_div:,.2f}")
    col2.metric("Single Stock Benchmark", f"${final_single:,.2f}")

    fig_div = go.Figure()
    fig_div.add_trace(
        go.Scatter(x=sim_results.index, y=sim_results['Diversified_Portfolio'], mode='lines', name='Diversified Portfolio',
                   line=dict(color='purple', width=3)))
    fig_div.add_trace(go.Scatter(x=sim_results.index, y=sim_results['Single_Stock_Benchmark'], mode='lines',
                                 name='Single Stock Benchmark', line=dict(color='gray', dash='dot')))

    fig_div.update_layout(
        title="Overall Performance Comparison: Diversified Portfolio vs. Single Stock ($10,000 Start)",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode="x unified"
    )
    st.plotly_chart(fig_div, width='stretch')
