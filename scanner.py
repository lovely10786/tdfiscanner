import requests
import pandas as pd
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        print("Telegram error")

def get_symbols():
    url = "https://api.bybit.com/v5/market/instruments-info?category=linear"
    
    try:
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            print("Symbol API error:", res.status_code)
            return []

        data = res.json()

        if "result" not in data:
            print("Invalid symbol data")
            return []

        return [s['symbol'] for s in data['result']['list'] if s['quoteCoin']=="USDT"]

    except Exception as e:
        print("Symbol fetch error:", e)
        return []

def get_data(symbol):
    url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval=5"

    try:
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            return None

        data = res.json()

        if "result" not in data:
            return None

        closes = [float(x[4]) for x in data['result']['list']]
        return pd.DataFrame(closes, columns=['close'])

    except:
        return None

print("🚀 Scanner Started...")

while True:
    symbols = get_symbols()

    if not symbols:
        print("No symbols, retrying...")
        time.sleep(60)
        continue

    for symbol in symbols[:50]:   # limit for safety
        try:
            df = get_data(symbol)

            if df is None or len(df) < 2:
                continue

            df['change'] = df['close'].pct_change()
            last = df['change'].iloc[-1]

            if last > 0.05:
                send_alert(f"🚀 Pump: {symbol}")

            if last < -0.05:
                send_alert(f"🔻 Dump: {symbol}")

            time.sleep(0.2)  # prevent API block

        except Exception as e:
            print("Error:", symbol, e)
            continue

    print("Cycle complete... waiting")
    time.sleep(60)
