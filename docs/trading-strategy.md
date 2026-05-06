# Bill Fanter's 0DTE Trading Strategy

Complete documentation of the 8-confirmation framework for zero days to expiration (0DTE) options trading.

---

## Table of Contents

1. [Strategy Overview](#strategy-overview)
2. [The 8 Confirmations (Detailed)](#the-8-confirmations-detailed)
3. [Perfect Setups](#perfect-setups)
4. [When to Skip](#when-to-skip)
5. [Trade Examples](#trade-examples)

---

## Strategy Overview

**Core Principle:**  
Every trade requires ALL 8 confirmations. Missing even ONE = skip the trade.

**Why This Works:**
- Reduces false signals (high win rate: 55-65%)
- Eliminates emotional trading (clear rules)
- Forces patience (only 5-10 clean setups per week)

**Time Frame:**  
5-minute candles (optimal for 0DTE)

**Trading Window:**  
9:45 AM - 12:00 PM ET (avoid first 15 minutes)

---

## The 8 Confirmations (Detailed)

### 1. Candles — Direction & Control

**What to look for:**

**CALL Setup:**
- Green candles (close > open)
- Preferably **Marubozu** (fat body, tiny wicks)
  - Fat body = one side dominated the entire period
  - Bulls controlled price from open to close
- Ideally 2-3 green candles in a row

**PUT Setup:**
- Red candles (close < open)
- Preferably **Marubozu** (fat body, tiny wicks)
  - Bears controlled price from open to close
- Ideally 2-3 red candles in a row

**SKIP:**
- **Doji** (tiny body, long wicks on both sides)
  - Indecision = neither bulls nor bears in control
- **Extreme wicking** (huge wicks, small body)
  - Market waiting for news (FOMC, earnings)
  - Stay in cash until clarity

**Visual Example:**
```
CALL (Good):          PUT (Good):          SKIP (Doji):
    |                     |                    |--|
    |                     |                  --|  |--
  [####]                [####]                 |  |
    |                   |   |                  |--|
    |                   |   |
```

**Master Template:**
```
Candles → Control → Direction → CALL or PUT
```

---

### 2. Volume — Conviction Check

**What to look for:**

**High Volume = Trust the Move**
- Current bar volume > 1.2x average of last 20 bars
- Tall volume bars = conviction
- Institutions are participating

**Low Volume = Skip the Setup**
- Even if other confirmations align
- Low volume = weak move, likely to reverse
- Retail-only participation

**Calculation:**
```python
avg_volume = sum(last_20_bars.volume) / 20
current_volume = current_bar.volume

if current_volume > (avg_volume * 1.2):
    print("✓ High volume confirmed")
else:
    print("✗ Low volume - SKIP")
```

**Why This Matters:**
Volume is the #1 lie detector. Price can fake moves, but volume reveals institutional intent.

---

### 3. VWAP — The Magnet

**What is VWAP?**
Volume-Weighted Average Price — the "fair value" for the day.

**How it acts:**
- **Magnet effect** — Price tends to revert to VWAP
- **Support/Resistance** — Acts as dynamic S/R level
- **Institutional benchmark** — Big money uses VWAP to measure execution quality

**CALL Setup:**
- Price ABOVE VWAP (bulls control)
- VWAP acts as support

**PUT Setup:**
- Price BELOW VWAP (bears control)
- VWAP acts as resistance

**Visual:**
```
Price above VWAP (bullish):    Price below VWAP (bearish):
         ___                            ___
    ____/                                  \____
   /     VWAP                          VWAP     \
  /                                               \
```

**Key Insight:**
If price is above VWAP but tangled with it (crossing back and forth), SKIP. Wait for clear separation.

---

### 4. 9 EMA — Fast Momentum

**What is 9 EMA?**
Exponential Moving Average of the last 9 periods (5-min candles).

**Why 9?**
Fast enough to catch momentum, slow enough to filter noise.

**CALL Setup:**
- Price ABOVE 9 EMA (bullish momentum)
- 9 EMA sloping UP

**PUT Setup:**
- Price BELOW 9 EMA (bearish momentum)
- 9 EMA sloping DOWN

**SKIP:**
- Price tangled with 9 EMA (crossing back and forth)
- 9 EMA flat (no momentum)

---

### 5. 21 EMA — Slow Trend

**What is 21 EMA?**
Exponential Moving Average of the last 21 periods.

**Why 21?**
Slower than 9 EMA = confirms the underlying trend.

**CALL Setup:**
- Price ABOVE 21 EMA (bullish trend)
- 21 EMA sloping UP

**PUT Setup:**
- Price BELOW 21 EMA (bearish trend)
- 21 EMA sloping DOWN

**SKIP:**
- Price tangled with 21 EMA
- 21 EMA flat

**Key Insight:**
9 EMA = momentum (short-term), 21 EMA = trend (longer-term). Both must align.

---

### 6. SPY — Market Direction

**Why SPY?**
SPY is the S&P 500 ETF — the "market itself."

**For index trading (SPY/QQQ):**
- If trading SPY → check QQQ (confirmation 7)
- If trading QQQ → check SPY

**For individual stock trading (AAPL, TSLA, etc.):**
- Stock MUST match SPY direction
- Why? Individual stocks rarely move against the market
- If SPY bearish but AAPL bullish = divergence = SKIP

**CALL Setup:**
- SPY bullish (green candles, above VWAP/EMAs)

**PUT Setup:**
- SPY bearish (red candles, below VWAP/EMAs)

---

### 7. QQQ / Sector ETF — Confluence Check

**For index trading:**
- Check QQQ (Nasdaq 100 ETF)
- SPY + QQQ must match direction
- If SPY bullish but QQQ bearish = conflicting signals = SKIP

**For individual stock trading:**
- Check the stock's **Sector ETF**
- Example: Trading AAPL (tech) → check XLK (Technology Sector ETF)
- Stock + Sector ETF must match direction

**Sector ETF Reference:**
- **XLK** — Technology (AAPL, MSFT, NVDA, GOOGL)
- **XLY** — Consumer Discretionary (TSLA, AMZN, HD)
- **XLF** — Financials (JPM, BAC, GS)
- **XLE** — Energy (XOM, CVX)
- **XLV** — Healthcare (JNJ, PFE, UNH)
- **XLI** — Industrials (BA, CAT)
- **XLP** — Consumer Staples (PG, KO, WMT)
- **XLC** — Communication Services (GOOGL, META, DIS)

**Why This Matters:**
If the sector is selling off, your stock is unlikely to go up alone.

---

### 8. Support / Resistance — Clear or Breakout

**Key Levels to Mark:**
- **PDH** (Prior Day High) — resistance
- **PDL** (Prior Day Low) — support
- **PDC** (Prior Day Close) — psychological level
- **VWAP** — dynamic S/R

**CALL Setup (two scenarios):**

**Scenario A: Clear of Resistance**
- Price is $0.50+ away from next resistance
- Example: Price at $501.50, resistance at $502.50 = clear
- Safe to enter

**Scenario B: Breakout Confirmed**
- Price broke ABOVE resistance with HIGH VOLUME
- Candle closed above resistance (not just a wick)
- Resistance now becomes support

**PUT Setup (two scenarios):**

**Scenario A: Clear of Support**
- Price is $0.50+ away from next support
- Example: Price at $501.50, support at $500.50 = clear
- Safe to enter

**Scenario B: Breakdown Confirmed**
- Price broke BELOW support with HIGH VOLUME
- Candle closed below support
- Support now becomes resistance

**SKIP:**
- Price within $0.25 of a key level (wait for break or bounce)
- Breakout/breakdown on LOW VOLUME (fake move)

---

## Perfect Setups

### Perfect CALL Setup

```
✓ Green Marubozu candles (3 in a row)
✓ Volume: 1.8M (avg: 1.2M) → High volume
✓ Price: $501.80, VWAP: $501.20 → Above VWAP
✓ 9 EMA: $501.50 → Price above 9 EMA
✓ 21 EMA: $500.90 → Price above 21 EMA
✓ SPY: Green candles, above VWAP/EMAs → Bullish
✓ QQQ: Green candles, above VWAP/EMAs → Bullish
✓ Resistance: $502.50 (70 cents away) → Clear

BULLISH STACK: Price > 9 EMA > 21 EMA > VWAP (all pointing up)

VERDICT: HIGH-PROBABILITY CALL
Entry: $501.75 - $502.00
Target: +25% ($502.50 resistance test)
Stop: -15% if breaks below VWAP ($501.20)
```

### Perfect PUT Setup

```
✓ Red Marubozu candles (3 in a row)
✓ Volume: 2.1M (avg: 1.3M) → High volume
✓ Price: $500.40, VWAP: $501.00 → Below VWAP
✓ 9 EMA: $500.60 → Price below 9 EMA
✓ 21 EMA: $501.10 → Price below 21 EMA
✓ SPY: Red candles, below VWAP/EMAs → Bearish
✓ QQQ: Red candles, below VWAP/EMAs → Bearish
✓ Support: $500.20 (20 cents away) → About to test

BEARISH STACK: VWAP > 21 EMA > 9 EMA > Price (all pointing down)

VERDICT: HIGH-PROBABILITY PUT
Entry: $500.30 - $500.45
Target: +25% (breakdown below PDL $500.20)
Stop: -15% if breaks above VWAP ($501.00)
```

---

## When to Skip

**ALWAYS skip if:**
1. Missing ANY of the 8 confirmations
2. First 15 minutes of trading day (9:30-9:45 AM)
3. Major news day (FOMC, CPI, jobs report, earnings)
4. Sideways/choppy market (no clear trend)
5. Extreme wicking (waiting for news)
6. Divergence (SPY bullish but QQQ bearish)
7. Low volume setup
8. Approaching resistance/support without breakout/breakdown confirmation

**Cash is a position.** Skipping bad setups is how you stay profitable.

---

## Trade Examples

### Example 1: Clean CALL Setup

**Time:** 10:15 AM  
**Ticker:** SPY  
**Price:** $501.80

**Checklist:**
1. ✓ Candles: 3 green Marubozus
2. ✓ Volume: 1.9M (avg 1.3M) = 1.46x average
3. ✓ VWAP: Price $501.80, VWAP $501.10 = above
4. ✓ 9 EMA: Price above $501.40
5. ✓ 21 EMA: Price above $500.90
6. ✓ SPY: Bullish (primary ticker)
7. ✓ QQQ: Green candles, above VWAP/EMAs
8. ✓ S/R: Next resistance $502.50 (70 cents away) = clear

**Decision:** BUY CALL  
**Entry:** SPY 502C at $1.50  
**Stop:** -15% = $1.28  
**Target:** +25% = $1.88  

**Result:** Exited at $1.90 (+26.7%) ✅

---

### Example 2: Divergence (SKIP)

**Time:** 11:00 AM  
**Ticker:** SPY  
**Price:** $502.10

**Checklist:**
1. ✓ Candles: 2 green candles
2. ✓ Volume: 1.6M (avg 1.2M) = high
3. ✓ VWAP: Price above VWAP
4. ✓ 9 EMA: Price above
5. ✓ 21 EMA: Price above
6. ✓ SPY: Bullish (primary ticker)
7. ✗ QQQ: Red candles, below VWAP = **BEARISH**
8. ? S/R: Clear

**Decision:** SKIP — Divergence detected  
**Reason:** SPY bullish but QQQ bearish = conflicting signals

**What happened:** SPY reversed 10 minutes later. Would have been a loss.

---

### Example 3: Low Volume (SKIP)

**Time:** 2:30 PM  
**Ticker:** SPY  
**Price:** $501.50

**Checklist:**
1. ✓ Candles: Green candles
2. ✗ Volume: 0.8M (avg 1.2M) = **LOW** (0.67x average)
3. ✓ VWAP: Price above
4. ✓ 9 EMA: Price above
5. ✓ 21 EMA: Price above
6. ✓ SPY: Bullish
7. ✓ QQQ: Bullish
8. ✓ S/R: Clear

**Decision:** SKIP — Low volume  
**Reason:** Even though 7/8 confirmations, low volume = weak move

**What happened:** Price drifted sideways for 30 minutes, then reversed. No conviction.

---

## Key Takeaways

1. **ALL 8 confirmations required** — No exceptions
2. **Volume is the lie detector** — High volume = trust the move
3. **Confluence prevents fake moves** — SPY + QQQ must align
4. **Support/Resistance = patience** — Wait for clear or breakout
5. **5-10 clean setups per week** — That's normal, don't force trades
6. **Cash is a position** — Skipping bad setups = staying profitable

---

## Additional Resources

- **Bill Fanter's Course:** 0DTE Masterclass (Sessions 1-6)
- **TradingView Template:** https://www.tradingview.com/chart/0fz7lFBr/
- **Practice:** 50-100 paper trades before live trading
