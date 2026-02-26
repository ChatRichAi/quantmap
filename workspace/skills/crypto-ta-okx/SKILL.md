---
name: crypto-ta-okx
description: Fetch Crypto index candlestick data from OKX and perform quick technical analysis (trend, momentum, volatility, key levels). Use when the user asks for Crypto technical analysis via OKX index candles.
emoji: 📊
bins: [curl, jq]
---

# crypto-ta-okx

Use this skill when the user explicitly wants **Crypto technical analysis** based on **OKX index candlesticks**.

## 🔌 Data Source (OKX Index Candles)

Use the OKX REST endpoint:

```http
GET https://www.okx.com/api/v5/market/index-candles?instId=BTC-USD&bar=1H&limit=100
```

Key query parameters:
- `instId=BTC-USD` – BTC index in USD 💵
- `bar` – timeframe, e.g. `1m, 5m, 15m, 1H, 4H, 1D` ⏱
- `limit` – number of candles (max 100 per call)

Response `data` is an array of arrays (newest first):

```json
[
  [
    "ts",   // 0: open time (ms)
    "o",    // 1: open
    "h",    // 2: high
    "l",    // 3: low
    "c",    // 4: close
    "confirm" // 5: 0 = live candle, 1 = closed ✅
  ],
  ...
]
```

Always **ignore** unconfirmed candles (`confirm = "0"`) for final conclusions.

---

## 🧮 Workflow

1. **Fetch data**
   - If you can call HTTP directly: fetch from OKX with the desired `bar` and `limit`.
   - If not, ask the user to paste either:
     - The `data` array from OKX JSON, or
     - A small CSV/TSV with: `timestamp,open,high,low,close`.

2. **Parse & clean**
   - Ensure numeric conversion of `o,h,l,c`.
   - Drop entries where `confirm == "0"`.
   - Sort candles from **oldest → newest** for analysis.

3. **Compute basic metrics**
   - Recent trend:
     - Compare latest close vs close N candles ago (e.g., 20).
     - Compute simple moving averages: SMA(20), SMA(50) if enough data.
   - Volatility:
     - Average true range proxy: mean of `(high - low)` over recent N candles.
     - Note if current range is larger/smaller than recent average.
   - Price structure:
     - Identify recent swing highs/lows (local maxima/minima in close or high/low).
     - Use these as **support** and **resistance** zones.

4. **Qualitative analysis**
   In your natural-language output, include:
   - **Trend** 🧭 – bullish / bearish / sideways, and on which timeframe.
   - **Momentum** ⚡ – is price accelerating, stalling, or reversing?
   - **Volatility** 🌊 – calm vs elevated; mention recent ranges.
   - **Key levels** 🧱 – notable supports/resistances from swings & clusters.
   - **Candle behaviour** – long wicks, doji-like candles, strong body bars, etc.

5. **Communicate clearly (no signals)**
   - Describe **scenarios and levels**, not financial advice.
   - Avoid explicit trade calls ("buy/sell now").
   - Use wording like "bullish bias above X", "risk of deeper pullback below Y".

Use this example as a reference when reasoning about how the OKX endpoint works or when generating helper code for the user.

---

## 🧾 Output Template

When you finish analysis, structure your answer roughly as:

1. **Timeframe & data used** ⏱
2. **Trend summary** 🧭
3. **Momentum & candles** ⚡
4. **Volatility & ranges** 🌊
5. **Key support/resistance levels** 🧱
6. **Scenario commentary & risks** 🧠

Keep it concise but concrete, and always include numbers (prices, percentage moves, typical ranges) when possible.
