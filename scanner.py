import requests
import pandas as pd
import time
import os

# 🔐 ENV VARIABLES
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 🌐 HEADERS (FIX 403 ERROR)
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

# 🔔 TELEGRAM ALERT
def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# 📊 GET ALL SYMBOLS
def get_symbols():
    url = "https://api.bytick.com/v5/market/instruments-info?category=linear"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)

        if res.status_code != 200:
            print("Symbol API error:", res.status_code)
            return []

        data = res.json()

        if "result" not in data:
            print("Invalid symbol response")
            return []

        symbols = [
            s['symbol']
            for s in data['result']['list']
            if s['quoteCoin'] == "USDT"
        ]

        print(f"Loaded {len(symbols)} symbols")
        return symbols

    except Exception as e:
        print("Symbol fetch error:", e)
        return []

# 📉 GET PRICE DATA
def get_data(symbol):
    url = f"https://api.bytick.com/v5/market/kline?category=linear&symbol={symbol}&interval=5"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)

        if res.status_code != 200:
            return None

        data = res.json()

        if "result" not in data:
            return None

        closes = [float(x[4]) for x in data['result']['list']]

        if len(closes) < 2:
            return None

        return pd.DataFrame(closes, columns=['close'])

    except:
        return None

# 🚀 START BOT
print("🚀 Scanner Started...")

while True:
    symbols = get_symbols()

    if not symbols:
        print("No symbols, retrying in 60 sec...")
        time.sleep(60)
        continue

    # 🔥 LIMIT FOR SAFETY
    for symbol in symbols[:50]:
        try:
            df = get_data(symbol)

            if df is None:
                continue

            # 📊 SIMPLE SIGNAL (can replace with TDFI later)
            df['change'] = df['close'].pct_change()
            last = df['change'].iloc[-1]

            # 🚀 BUY SIGNAL
            if last > 0.05:
                msg = f"🚀 Pump: {symbol} ({round(last*100,2)}%)"
                print(msg)
                send_alert(msg)

            # 🔻 SELL SIGNAL
            elif last < -0.05:
                msg = f"🔻 Dump: {symbol} ({round(last*100,2)}%)"
                print(msg)
                send_alert(msg)

            # ⏱️ DELAY (IMPORTANT)
            time.sleep(0.2)

        except Exception as e:
            print("Error:", symbol, e)
            continue

    print("✅ Cycle complete... waiting 60 sec\n")
    time.sleep(60)
