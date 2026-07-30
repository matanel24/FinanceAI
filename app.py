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

st.set_page_config(page_title="דאשבורד מסחר אלגוריתמי מתקדם", layout="wide")
st.title("📈 דאשבורד מסחר אלגוריתמי: מודלים, נרות ופיזור תיקים")

st.sidebar.header("💼 חיבור לברוקר (Alpaca)")
account_info = get_alpaca_account_info()

if account_info:
    st.sidebar.success(f"סטטוס חשבון: {account_info['status']}")
    st.sidebar.metric("כוח קנייה (Buying Power)", f"${account_info['buying_power']:,.2f}")
    st.sidebar.metric("יתרת מזומן", f"${account_info['cash']:,.2f}")
    st.sidebar.metric("שווי תיק כולל", f"${account_info['portfolio_value']:,.2f}")
else:
    st.sidebar.error("❌ אין חיבור פעיל ל-Alpaca (בדוק את המפתחות בקובץ .env)")

st.sidebar.markdown("---")
st.sidebar.header("הגדרות סל מניות")

num_stocks = st.sidebar.number_input("כמה מניות תרצה לנתח?", min_value=1, max_value=10, value=4)
default_stocks = ["AAPL", "MSFT", "GOOGL", "SPY", "NVDA", "AMZN", "TSLA", "META", "NFLX", "AMD"]

tickers = []
for i in range(num_stocks):
    default_val = default_stocks[i] if i < len(default_stocks) else ""
    ticker = st.sidebar.text_input(f"סימול מניה {i + 1}:", value=default_val, key=f"stock_{i}")

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
    st.write(f"## ניתוח מניה: `{ticker}`")

    data = fetch_data(ticker, start=start_date, end=end_date)
    if not data.empty:
        st.write(f"#### 📊 היסטוריית מחירים (גרף נרות): {ticker}")
        fig_candle = go.Figure(data=[go.Candlestick(x=data.index,
                                                    open=data['Open'],
                                                    high=data['High'],
                                                    low=data['Low'],
                                                    close=data['Close'])])
        fig_candle.update_layout(xaxis_rangeslider_visible=False, height=400, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_candle, width='stretch')
    else:
        st.warning(f"לא נמצאו נתוני מחירים עבור {ticker}.")

    sim_data = get_ai_data(ticker)

    if sim_data is not None:
        st.write(f"#### ⚔️ מלחמת מודלי ה-AI: {ticker}")
        final_bh = sim_data['Buy_Hold_Portfolio'].iloc[-1]
        final_rf = sim_data['RF_Portfolio'].iloc[-1]
        final_xgb = sim_data['XGB_Portfolio'].iloc[-1]
        final_hr = sim_data['HighRisk_Portfolio'].iloc[-1]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("קנה והחזק", f"${final_bh:,.2f}")
        c2.metric("מודל שמרן (RF)", f"${final_rf:,.2f}")
        c3.metric("מודל אגרסיבי (XGB)", f"${final_xgb:,.2f}")
        c4.metric("🔥 סיכון גבוה", f"${final_hr:,.2f}")

        # חילוץ ההמלצה האחרונה מהמודל עבור היום הנוכחי
        last_xgb_signal = sim_data['Pred_XGB'].iloc[-1]
        last_rf_signal = sim_data['Pred_RF'].iloc[-1]

        # תצוגת שורת ההמלצה החכמה
        st.markdown("---")
        st.subheader("💡 תחזית והמלצת מערכת להיום:")

        col_rec1, col_rec2 = st.columns(2)
        with col_rec1:
            if last_xgb_signal == 1:
                st.success(f"🚀 **מודל XGBoost (אגרסיבי):** המגמה חיובית. **מומלץ לקנות / להחזיק** את {ticker}.")
            else:
                st.warning(f"🛡️ **מודל XGBoost (אגרסיבי):** המגמה שלילית או תנודתית. **מומלץ להמתין / לא לקנות** כרגע.")

        with col_rec2:
            if last_rf_signal == 1:
                st.success(f"טקטית **מודל Random Forest (שמרן):** זיהה הזדמנות כניסה בטוחה ל-{ticker}.")
            else:
                st.info(f"💤 **מודל Random Forest (שמרן):** אין איתות קנייה ברור כרגע ל-{ticker}.")

        fig_ind = go.Figure()
        fig_ind.add_trace(
            go.Scatter(x=sim_data.index, y=sim_data['Buy_Hold_Portfolio'], mode='lines', name='Buy & Hold',
                       line=dict(color='gray', dash='dot')))
        fig_ind.add_trace(go.Scatter(x=sim_data.index, y=sim_data['RF_Portfolio'], mode='lines', name='שמרן (RF)',
                                     line=dict(color='green', width=2)))
        fig_ind.add_trace(go.Scatter(x=sim_data.index, y=sim_data['XGB_Portfolio'], mode='lines', name='אגרסיבי (XGB)',
                                     line=dict(color='blue', width=2)))
        fig_ind.add_trace(
            go.Scatter(x=sim_data.index, y=sim_data['HighRisk_Portfolio'], mode='lines', name='סיכון גבוה',
                       line=dict(color='red', width=2)))

        fig_ind.update_layout(title=f"השוואת ביצועים עבור {ticker} ($10k התחלה)", height=400,
                              margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified")
        st.plotly_chart(fig_ind, width='stretch')

        # כפתור שליחת פקודת מסחר אמיתית לאלפקה
        st.write(f"🤖 **פעולת מסחר אוטומטית (חיבור לברוקר):**")
        if st.button(f"שגר פקודת קנייה (1 מניה) ל-{ticker}", key=f"trade_{ticker}"):
            success, message = execute_live_trade(ticker, qty=1)
            if success:
                st.success(message)
            else:
                st.error(message)

    else:
        st.warning(f"אין מספיק נתונים להרצת סימולטור עבור {ticker}.")

    st.write("---")

st.subheader("🌐 סימולטור תיק מניות מבוזר (Portfolio Diversification)")

sim_results = get_portfolio_data(tickers_input)

if sim_results is not None:
    final_div = sim_results['Diversified_Portfolio'].iloc[-1]
    final_single = sim_results['Single_Stock_Benchmark'].iloc[-1]

    col1, col2 = st.columns(2)
    col1.metric("תיק מבוזר משולב (כל הסל)", f"${final_div:,.2f}")
    col2.metric("השקעה במניה הראשונה בלבד", f"${final_single:,.2f}")

    fig_div = go.Figure()
    fig_div.add_trace(
        go.Scatter(x=sim_results.index, y=sim_results['Diversified_Portfolio'], mode='lines', name='תיק מבוזר (כל הסל)',
                   line=dict(color='purple', width=3)))
    fig_div.add_trace(go.Scatter(x=sim_results.index, y=sim_results['Single_Stock_Benchmark'], mode='lines',
                                 name='מניה בודדת בנצ\'מרק', line=dict(color='gray', dash='dot')))

    fig_div.update_layout(
        title="השוואת ביצועים כוללת: תיק מבוזר מול מניה בודדת ($10,000 התחלה)",
        xaxis_title="תאריך",
        yaxis_title="שווי תיק ($)",
        hovermode="x unified"
    )
    st.plotly_chart(fig_div, width='stretch')