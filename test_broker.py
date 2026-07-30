import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

# Load secret keys from the .env file
load_dotenv()

API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
BASE_URL = os.getenv('ALPACA_BASE_URL')

# Create the connection object to the broker
api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')

try:
    # Fetch trading account details (paper trading)
    account = api.get_account()
    print("Connection to Alpaca established successfully!")
    print(f"Account Status: {account.status}")
    print(f"Current Buying Power: ${float(account.buying_power):,.2f}")
except Exception as e:
    print(f"Error connecting to broker: {e}")
