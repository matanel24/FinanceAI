# FinanceAI - Advanced Algorithmic Trading Dashboard

An advanced, interactive algorithmic trading and portfolio management system built in Python. The application integrates machine learning models, technical indicators, and a live connection to the **Alpaca API** for paper trading execution, wrapped in a sleek **Streamlit** web dashboard.

---

## Key Features

* **AI Model Warfare:** Compares multiple prediction strategies side-by-side:
  * **XGBoost Classifier (`XGBRegressor/Classifier`):** Aggressive machine learning model optimized for directional trend capture.
  * **Random Forest Classifier:** Conservative, risk-managed predictive modeling.
  * **High-Risk Momentum Strategy:** MACD-based fast tactical entries.
* **Interactive Visualizations:** Built with **Plotly** to render detailed candlestick price charts and performance equity curves starting from a $10k benchmark.
* **Portfolio Diversification Simulator:** Evaluates and contrasts a diversified asset basket against single-stock benchmarks over multi-year historical data.
* **Real-Time Broker Integration (Alpaca):** Securely connects to the Alpaca Paper Trading environment via environment variables (`.env`). Displays live account metrics (Buying Power, Cash, Total Portfolio Value) and allows one-click execution of live market orders.
* **Smart Signal Recommendations:** Automatically evaluates the latest market data to provide real-time, actionable buying or holding advice.

---

## Tech Stack

* **Language:** Python 3.14+
* **Frontend/UI:** Streamlit & Plotly
* **Machine Learning:** Scikit-Learn, XGBoost
* **Financial Data:** yFinance (`yfinance`)
* **Broker API:** Alpaca-Py (`alpaca-py`)
* **Environment & Security:** Python-Dotenv

---

## Project Architecture

```text
FinanceAI/
│
├── app.py               # Streamlit frontend dashboard & UI controls
├── trading_engine.py    # Core backend: ML pipelines, simulations, & Alpaca integration
├── requirements.txt     # Project dependencies
├── .env                 # API credentials (ignored in Git for security)
└── .gitignore           # Git exclusion rules
Installation & Setup
Clone the repository:

Bash
git clone [https://github.com/matanel24/FinanceAI.git](https://github.com/matanel24/FinanceAI.git)
cd FinanceAI
Install dependencies:

Bash
pip install -r requirements.txt
Configure your environment variables:
Create a .env file in the root directory and add your Alpaca API keys:

Code snippet
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
Run the Dashboard:

Bash
python -m streamlit run app.py
Security Note
This project uses .gitignore to ensure that sensitive files like .env (containing broker API keys) are never exposed publicly on GitHub.
