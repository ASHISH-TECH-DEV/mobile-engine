import yfinance as yf
import pandas as pd
import pandas_ta as ta
from flask import Flask, render_template_string, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
SYMBOLS = {
    "BITCOIN": "BTC-USD",
    "ETHEREUM": "ETH-USD",
    "GOLD (SPOT)": "GC=F",
    "GOLD (PAXG)": "PAXG-USD"
}

def fetch_signals(ticker):
    try:
        # 15 minute interval ka real data fetch kar rahe hain
        df = yf.download(ticker, period="2d", interval="15m", progress=False)
        if df.empty: return {"price": 0, "signal": "OFFLINE"}

        # Technical Analysis Indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_20'] = ta.ema(df['Close'], length=20)

        last_price = round(df['Close'].iloc[-1], 2)
        last_rsi = df['RSI'].iloc[-1]
        last_ema = df['EMA_20'].iloc[-1]

        # Actual Buy/Sell Logic (RSI + EMA Cross)
        signal = "SCANNING"
        entry, target, sl = 0, 0, 0

        if last_rsi < 35 and last_price > last_ema:
            signal = "BUY SIGNAL"
            entry = last_price
            target = round(last_price * 1.015, 2)
            sl = round(last_price * 0.99, 2)
        elif last_rsi > 65 and last_price < last_ema:
            signal = "SELL SIGNAL"
            entry = last_price
            target = round(last_price * 0.985, 2)
            sl = round(last_price * 1.01, 2)

        return {
            "price": last_price,
            "signal": signal,
            "entry": entry,
            "target": target,
            "sl": sl
        }
    except:
        return {"price": 0, "signal": "ERROR"}

# --- HTML DESIGN (Frontend) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Ashish Pro Terminal</title>
    <style>
        body { background: #000; color: #0f0; font-family: 'Courier New', monospace; text-align: center; }
        .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; padding: 20px; }
        .card { border: 2px solid #0f0; border-radius: 10px; padding: 15px; background: #050505; }
        .price { font-size: 24px; font-weight: bold; color: #fff; }
        .buy { color: #00ff00; font-weight: bold; animation: blink 1s infinite; }
        .sell { color: #ff0000; font-weight: bold; animation: blink 1s infinite; }
        @keyframes blink { 50% { opacity: 0; } }
    </style>
    <script>
        async function updateData() {
            const res = await fetch('/api/data');
            const data = await res.json();
            let html = '';
            for (let name in data) {
                const item = data[name];
                let sigClass = item.signal.includes('BUY') ? 'buy' : (item.signal.includes('SELL') ? 'sell' : '');
                html += `<div class="card">
                    <h2>${name}</h2>
                    <div class="${sigClass}">${item.signal}</div>
                    <div class="price">PRICE: ${item.price}</div>
                    <p>ENTRY: ${item.entry} | TARGET: ${item.target} | SL: ${item.sl}</p>
                </div>`;
            }
            document.getElementById('terminal-grid').innerHTML = html;
        }
        setInterval(updateData, 5000); // Har 5 second mein update
        window.onload = updateData;
    </script>
</head>
<body>
    <h1>🔥 ASHISH PRO TRADING TERMINAL 🔥</h1>
    <div id="terminal-grid" class="grid">LOADING REAL-TIME DATA...</div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data')
def api():
    results = {name: fetch_signals(ticker) for name, ticker in SYMBOLS.items()}
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)