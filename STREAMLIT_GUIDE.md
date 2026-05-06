# 🎯 Streamlit UI Guide - 0DTE Trading System

## 🚀 Quick Start

### Launch the Web Interface
```bash
cd claude_0dte_trader
python3 -m streamlit run app.py
```

The app will open automatically in your browser at: **http://localhost:8501**

---

## 📱 Features Overview

### 📊 Dashboard
- **Account overview**: Balance, daily P&L, trades remaining
- **Discipline status**: Checklist complete, loss streaks, limits
- **Recent trades**: Quick view of latest activity
- **Market status**: Real-time trading permission status

### 🌅 Morning Prep
- **Key levels entry**: PDH, PDL, PDC, VWAP
- **Market bias**: SPY bias (BULLISH/BEARISH/NEUTRAL)  
- **News tracking**: Economic events, earnings, etc.
- **One-click completion**: Saves to database, enables trading

### 📈 Trade Entry
- **Smart form**: Symbol, direction, entry price, quantity
- **Risk calculator**: Shows total risk vs account size
- **8-Confirmation analysis**: Real-time setup validation
- **Automatic blocking**: Won't allow weak setups or discipline violations
- **One-click logging**: Saves HIGH_PROBABILITY trades only

### 📚 Trade Journal
- **Complete history**: All trades with 8-confirmation status
- **Performance metrics**: Win rate, average return, total P&L
- **Visual charts**: Cumulative P&L over time
- **Detailed table**: Entry/exit prices, risk amounts, emotional states

### ⚙️ Settings
- **Account management**: Update account size
- **Risk parameters**: Daily limits, position sizing
- **Database tools**: Reset, stats, maintenance

---

## 🔒 Built-in Discipline Enforcement

The UI automatically enforces Bill Fanter's discipline rules:

### ❌ **Trade Entry Blocked When:**
- Pre-market checklist incomplete
- Already took 3 trades today
- 2 consecutive losses (forces day stop)
- Daily loss limit reached (-$500 default)
- Confluence analysis shows < 8/8 confirmations

### ✅ **Trade Entry Allowed When:**
- Morning prep complete
- All discipline rules passed
- Perfect 8/8 confirmation setup detected
- Position risk within account limits

---

## 🎯 Workflow Example

### 1. **Morning (9:25 AM)**
   - Open app → **Morning Prep** page
   - Enter PDH/PDL/PDC from yesterday
   - Set SPY bias and VIX level
   - Click **Complete Morning Prep** ✅

### 2. **Setup Detection (9:45 AM+)**
   - Go to **Trade Entry** page
   - Select SPY CALL (example)
   - Enter price: $2.15, quantity: 2
   - System analyzes 8 confirmations automatically
   - If 8/8 → Green "Log Trade Entry" button
   - If < 8/8 → Red "Trade Blocked" (shows reasons)

### 3. **Trade Management**
   - Monitor in **Dashboard**
   - Track P&L in **Trade Journal**
   - System prevents overtrading automatically

### 4. **End of Day**
   - Review **Trade Journal** performance
   - Check **Dashboard** for discipline score

---

## 🧪 Demo Mode Features

Currently running with **sample market data** for testing:

- ✅ **All UI components functional**
- ✅ **Database persistence working**  
- ✅ **Discipline enforcement active**
- ✅ **8-confirmation logic operational**
- ⏳ **Live market data** (Phase 2 - add Alpaca/Polygon API)

---

## 💡 Pro Tips

### **For Paper Trading:**
1. Use realistic prices (check current SPY/QQQ levels)
2. Enter actual emotional state (DISCIPLINED vs FOMO)
3. Follow the discipline rules - let system block weak setups
4. Track at least 50 trades before going live

### **Discipline Building:**
- **Green = Take the trade** (8/8 confirmations)
- **Yellow = Skip** (7/8 or weak setup)  
- **Red = Blocked** (< 6/8 or discipline violation)
- Trust the system - patience pays!

### **Risk Management:**
- Keep position risk ≤ 15% of account
- Stop trading after 2 losses in a row
- Complete morning prep EVERY day
- Log emotional state honestly

---

## 🔧 Next Phase (Live Data Integration)

```bash
# Future: Connect to live market data
pip install alpaca-py yfinance
# Add API keys to .env file
# Enable real-time 8-confirmation analysis
```

---

## 🎯 Ready to Trade!

The Streamlit UI gives you everything needed for disciplined 0DTE trading:

✅ **Morning prep workflow**  
✅ **8-confirmation validation**  
✅ **Automatic discipline enforcement**  
✅ **Complete trade journal**  
✅ **Performance analytics**

**Start with paper trading → Build discipline → Go live with small size**

🚀 **Happy Trading!**