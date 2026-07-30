import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
import os
from dotenv import load_dotenv

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Load environment variables
load_dotenv()
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

try:
    trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
    account = trading_client.get_account()
    print(f"Alpaca Connected! Buying Power: ${float(account.buying_power):,.2f}")
except Exception as e:
    trading_client = None
    print(f"Alpaca connection error: {e}")


def get_alpaca_account_info():
    if trading_client is None:
        return None
    try:
        account = trading_client.get_account()
        return {
            "status": account.status,
            "buying_power": float(account.buying_power),
            "cash": float(account.cash),
            "portfolio_value": float(account.portfolio_value)
        }
    except Exception as e:
        print(f"Error fetching account info: {e}")
        return None


def execute_live_trade(ticker, qty=1):
    if trading_client is None:
        return False, "No active connection to Alpaca"

    try:
        market_order_data = MarketOrderRequest(
            symbol=ticker,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC
        )
        order = trading_client.submit_order(order_data=market_order_data)
        return True, f"Order executed successfully! ID: {order.id}"
    except Exception as e:
        return False, f"Error executing order: {str(e)}"


def fetch_data(ticker, start="2020-01-01", end=None):
    data = yf.download(ticker, start=start, end=end)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    return data


def simulate_risk_managed_trading(prices, signals, volatility, risk_regime, daily_returns, fee_rate=0.001):
    capital = 10000.0
    portfolio = []
    in_position = False
    risk_free_daily = 0.04 / 252

    for i in range(len(prices)):
        signal = signals.iloc[i]
        vol = volatility.iloc[i]
        regime = risk_regime.iloc[i]
        daily_ret = daily_returns.iloc[i]

        is_panic_market = vol > (regime * 1.5)

        if in_position:
            if is_panic_market:
                in_position = False
                capital = capital * (1 - fee_rate)
            else:
                capital = capital * (1 + daily_ret)
                if signal == 0:
                    in_position = False
                    capital = capital * (1 - fee_rate)
        else:
            capital = capital * (1 + risk_free_daily)
            if signal == 1 and not is_panic_market:
                in_position = True
                capital = capital * (1 - fee_rate)

        portfolio.append(capital)
    return portfolio


def simulate_high_risk_trading(prices, signals, daily_returns, fee_rate=0.001):
    capital = 10000.0
    portfolio = []
    in_position = False

    for i in range(len(prices)):
        signal = signals.iloc[i]
        daily_ret = daily_returns.iloc[i]

        if in_position:
            capital = capital * (1 + daily_ret)
            if signal == 0:
                in_position = False
                capital = capital * (1 - fee_rate)
        else:
            if signal == 1:
                in_position = True
                capital = capital * (1 - fee_rate)
            else:
                capital = capital * (1 + (daily_ret * 0.1))
        portfolio.append(capital)
    return portfolio


def run_ai_analysis(ticker_symbol):
    if not isinstance(ticker_symbol, str):
        ticker_symbol = str(ticker_symbol)

    df = fetch_data(ticker_symbol, start="2020-01-01")
    if df.empty or len(df) < 100:
        return None

    df['Daily_Return'] = df['Close'].pct_change()
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['Volatility'] = df['Daily_Return'].rolling(window=10).std()

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50)

    df['Momentum_5D'] = df['Close'].pct_change(periods=5)
    df['Momentum_14D'] = df['Close'].pct_change(periods=14)

    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26

    df['Market_Risk_Regime'] = df['Volatility'].rolling(window=50).mean()

    features = ['Daily_Return', 'SMA_10', 'SMA_50', 'SMA_200', 'Volatility', 'Volume', 'RSI', 'Momentum_5D',
                'Momentum_14D', 'MACD', 'Market_Risk_Regime']

    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    train_df = df.dropna()

    if train_df.empty:
        return None

    X = train_df[features]
    y = train_df['Target']

    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    model_rf = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
    model_rf.fit(X_train, y_train)

    model_xgb = XGBClassifier(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42)
    model_xgb.fit(X_train, y_train)

    test_data = train_df.iloc[split:].copy()

    buy_threshold = 0.50
    prob_rf = model_rf.predict_proba(X_test)[:, 1]
    prob_xgb = model_xgb.predict_proba(X_test)[:, 1]

    test_data['Pred_RF'] = (prob_rf > buy_threshold).astype(int)
    test_data['Pred_XGB'] = (prob_xgb > buy_threshold).astype(int)
    test_data['Pred_HighRisk'] = (test_data['MACD'] > 0).astype(int)

    prices = test_data['Close']
    daily_returns = test_data['Daily_Return']
    volatility = test_data['Volatility']
    risk_regime = test_data['Market_Risk_Regime']

    test_data['RF_Portfolio'] = simulate_risk_managed_trading(prices, test_data['Pred_RF'], volatility, risk_regime,
                                                             daily_returns)
    test_data['XGB_Portfolio'] = simulate_risk_managed_trading(prices, test_data['Pred_XGB'], volatility, risk_regime,
                                                              daily_returns)
    test_data['HighRisk_Portfolio'] = simulate_high_risk_trading(prices, test_data['Pred_HighRisk'], daily_returns)

    initial_capital_after_fee = 10000 * (1 - 0.001)
    test_data['Buy_Hold_Portfolio'] = initial_capital_after_fee * (1 + test_data['Daily_Return']).cumprod()

    return test_data


def run_portfolio_simulation(tickers_list):
    tickers = [t.strip().upper() for t in tickers_list.split(",") if t.strip()]
    if not tickers:
        tickers = ["AAPL"]

    portfolio_df = pd.DataFrame()
    for ticker in tickers:
        df = fetch_data(ticker, start="2020-01-01")
        if not df.empty:
            portfolio_df[ticker] = df['Close']

    portfolio_df = portfolio_df.dropna()
    if portfolio_df.empty:
        return None

    returns_df = portfolio_df.pct_change().dropna()
    weights = np.array([1.0 / len(tickers)] * len(tickers))

    portfolio_returns = returns_df.dot(weights)
    initial_capital = 10000.0
    capital_series = initial_capital * (1 + portfolio_returns).cumprod()
    single_stock_returns = initial_capital * (1 + returns_df.iloc[:, 0]).cumprod()

    result_df = pd.DataFrame({
        'Diversified_Portfolio': capital_series,
        'Single_Stock_Benchmark': single_stock_returns
    }, index=returns_df.index)

    return result_df
