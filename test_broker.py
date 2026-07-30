import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

# טעינת המפתחות הסודיים מקובץ ה-.env
load_dotenv()

API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
BASE_URL = os.getenv('ALPACA_BASE_URL')

# יצירת אובייקט החיבור לברוקר
api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')

try:
    # משיכת פרטי חשבון המסחר (הווירטואלי)
    account = api.get_account()
    print("✅ החיבור ל-Alpaca בוצע בהצלחה!")
    print(f"סטטוס חשבון: {account.status}")
    print(f"כוח קנייה נוכחי למסחר: ${float(account.buying_power):,.2f}")
except Exception as e:
    print(f"❌ שגיאה בחיבור לברוקר: {e}")