import requests
import pandas as pd
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_alert(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def get_symbols():
    url = "https://api.bybit.com/v5/market/instruments-info?category=linear"
    data = requests.get(url).json()
    return [s['symbol'] for s in data['result']['list'] if s['quoteCoin']=="USDT"]

def get_data(symbol):
    url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval=5"
    data = requests.get(url).json()
    closes = [float(x[4]) for x in data['result']['list']]
    return pd.DataFrame(closes, columns=['close'])

print("🚀 Scanner Started...")

while True:
    symbols = get_symbols()

    for symbol in symbols[:50]:
        try:
            df = get_data(symbol)
            df['change'] = df['close'].pct_change()

            last = df['change'].iloc[-1]

            if last > 0.05:
                send_alert(f"🚀 Pump: {symbol}")

            if last < -0.05:
                send_alert(f"🔻 Dump: {symbol}")

        except:
            continue

    print("Cycle complete, waiting...")
    time.sleep(60)
