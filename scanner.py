import requests
import pandas as pd
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ✅ STRONG HEADERS (ANTI-BLOCK)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Referer": "https://www.bybit.com/",
    "Origin": "https://www.bybit.com"
}

# 🔁 TRY BOTH DOMAINS
BASE_URLS = [
    "https://api.bytick.com",
    "https://api.bybit.com"
]

def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# 🔄 FETCH SYMBOLS (WITH RETRY)
def get_symbols():
    for base in BASE_URLS:
        url = f"{base}/v5/market/instruments-info?category=linear"
        
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)

            if res.status_code == 200:
                data = res.json()

                if "result" in data:
                    symbols = [
                        s['symbol']
                        for s in data['result']['list']
                        if s['quoteCoin'] == "USDT"
                    ]

                    print(f"Loaded {len(symbols)} symbols from {base}")
                    return symbols

            else:
                print(f"{base} blocked:", res.status_code)

        except Exception as e:
            print(f"{base} error:", e)

    return []

# 🔄 FETCH DATA (WITH RETRY)
def get_data(symbol):
    for base in BASE_URLS:
        url = f"{base}/v5/market/kline?category=linear&symbol={symbol}&interval=5"

        try:
            res = requests.get(url, headers=HEADERS, timeout=10)

            if res.status_code == 200:
                data = res.json()

                if "result" in data:
                    closes = [float(x[4]) for x in data['result']['list']]

                    if len(closes) >= 2:
                        return pd.DataFrame(closes, columns=['close'])

        except:
            continue

    return None

print("🚀 Scanner Started...")

while True:
    symbols = get_symbols()

    if not symbols:
        print("❌ No symbols (blocked). Retrying in 60 sec...")
        time.sleep(60)
        continue

    for symbol in symbols[:50]:
        try:
            df = get_data(symbol)

            if df is None:
                continue

            df['change'] = df['close'].pct_change()
            last = df['change'].iloc[-1]

            if last > 0.05:
                msg = f"🚀 Pump: {symbol} ({round(last*100,2)}%)"
                print(msg)
                send_alert(msg)

            elif last < -0.05:
                msg = f"🔻 Dump: {symbol} ({round(last*100,2)}%)"
                print(msg)
                send_alert(msg)

            time.sleep(0.3)

        except Exception as e:
            print("Error:", symbol, e)

    print("✅ Cycle done... waiting 60 sec\n")
    time.sleep(60)
