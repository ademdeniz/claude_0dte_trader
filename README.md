# 0DTE Options Trading System

An AI-assisted trading system for 0DTE (zero days to expiration) options trading, built on **Bill Fanter's 8-confirmation framework** with integrated **emotional discipline guardrails**.

---

## What This Is

A **Claude Code project** that helps you:
1. **Trade with discipline** — Automated guardrails prevent you from breaking your own rules
2. **Eliminate emotion** — Pre-commit hooks block FOMO, revenge trading, and overtrading
3. **Track everything** — Every trade logged with full 8-confirmation checklist
4. **Improve systematically** — Weekly reports show which emotional traps you fall into most

---

## Quick Start

### Prerequisites
- Python 3.9+
- Claude Code (VS Code extension)
- Alpaca account (free tier) OR Polygon.io account ($29/month for real-time)

### Installation

```bash
# Clone or download this project
cd claude_0dte_trader

# Install dependencies
pip install -r requirements.txt

# Initialize database
python src/persistence/database.py

# Run morning prep (calculates PDH/PDL/PDC/VWAP)
python tools/scripts/morning_prep.py
```

### First Trade (Paper Trading)

```bash
# Open Claude Code in VS Code
code .

# Say to Claude:
"Run pre-market checklist"

# Claude will:
# 1. Check economic calendar for news
# 2. Calculate PDH/PDL/PDC/VWAP
# 3. Prompt you to complete checklist

# Once checklist is complete:
"Log a trade entry"

# Claude will:
# 1. Ask for ticker, direction, entry price
# 2. Validate all 8 confirmations
# 3. Check emotional state
# 4. Save to database

# When you exit:
"Log trade exit"

# Claude will:
# 1. Calculate P&L
# 2. Check if you followed stop loss/profit target
# 3. Update database
# 4. Check for violations
```

---

## The 8-Confirmation Framework

Every trade requires **ALL 8 confirmations**:

1. ✅ **Candles** — Green (CALL) or Red (PUT), preferably Marubozu
2. ✅ **Volume** — High (current > 1.2x average of last 20 bars)
3. ✅ **VWAP** — Price above (CALL) or below (PUT)
4. ✅ **9 EMA** — Price above (CALL) or below (PUT)
5. ✅ **21 EMA** — Price above (CALL) or below (PUT)
6. ✅ **SPY** — Matches direction (or stock matches SPY)
7. ✅ **QQQ / Sector ETF** — Matches direction (confluence)
8. ✅ **Support/Resistance** — Clear of levels OR breakout/breakdown confirmed

**Missing even ONE = skip the trade.**

---

## The 8 Discipline Rules (Enforced by Hooks)

1. ❌ **NO FOMO** — If you missed the entry, skip it
2. ❌ **NO OVERTRADING** — Max 3 trades per day
3. ❌ **NO REVENGE TRADING** — 2 losses in a row = STOP
4. ❌ **NO AVERAGING DOWN** — Stop loss is final
5. ❌ **NO TRADING WITHOUT CHECKLIST** — Complete pre-market first
6. ✅ **TRUST THE STRATEGY** — 1 win ≠ genius, 1 loss ≠ failure
7. ✅ **CUT LOSERS, LET WINNERS RUN** — Exit at -15%, hold to +25%
8. ✅ **FULL ATTENTION ONLY** — Can't focus? Don't trade

---

## Project Structure

```
claude_0dte_trader/
├── CLAUDE.md                    # Project constitution (read this first)
├── README.md                    # This file
├── docs/                        # Architecture & strategy docs
├── skills/                      # AI workflows (morning-prep, confluence-check, etc.)
├── hooks/                       # Guardrails (PreToolUse, PostToolUse, etc.)
├── src/                         # Core Python code
│   ├── api/                     # Market data & notifications
│   ├── core/                    # Indicators & confluence logic
│   └── persistence/             # Database & models
├── tools/                       # Standalone scripts & prompts
└── tests/                       # Unit & integration tests
```

---

## Phased Rollout

| Phase | What You're Doing | What Gets Built |
|-------|-------------------|-----------------|
| **Phase 1** (Weeks 1-4) | Paper trading manually, learning patterns | Trade journal + discipline tracker |
| **Phase 2** (Weeks 5-8) | Profitable on paper, want faster morning prep | Morning Prep Script |
| **Phase 3** (Weeks 9-12) | Consistent wins, want real-time alerts | Level Monitor + Confluence Bot |
| **Phase 4** (Month 4+) | Trading with real money | Full automation |

---

## Skills (AI Workflows)

### `morning-prep`
Calculates prior day levels before market open:
- PDH (prior day high)
- PDL (prior day low)
- PDC (prior day close)
- VWAP
- High-volume zones
- Support/resistance levels

**Usage:** *"Claude, run morning prep"*

### `confluence-check`
Validates all 8 confirmations for a given ticker:
- Checks candles, volume, VWAP, EMAs
- Checks SPY, QQQ (or sector ETF)
- Checks support/resistance
- Returns: HIGH-PROBABILITY CALL/PUT or SKIP

**Usage:** *"Claude, check confluence for SPY"*

### `trade-journal`
Logs trades to database:
- Entry/exit prices
- 8-confirmation checklist
- Emotional state
- Violations (FOMO, overtrading, etc.)

**Usage:** *"Claude, log a trade entry"*

### `level-alert`
Monitors proximity to key levels in real-time:
- Alerts when within $0.10 of resistance/support
- Alerts on breakout/breakdown confirmation

**Usage:** *"Claude, start level monitor"* (runs continuously)

### `generate-report`
Generates daily/weekly summaries:
- Win rate, net P/L
- Discipline score (% of trades following rules)
- Top violations (which emotional trap you fall into most)

**Usage:** *"Claude, generate weekly report"*

---

## Hooks (Guardrails)

### `PreToolUse.sh`
Runs BEFORE any tool is called:
- ✅ Checks if pre-market checklist complete
- ✅ Checks if 3 trades already taken today
- ✅ Checks if 2 losses in a row
- ❌ BLOCKS tool call if any condition fails

### `PostToolUse.sh`
Runs AFTER any tool is called:
- Logs violations (FOMO, overtrading, etc.)
- Updates discipline tracker
- Sends notification if violation detected

### `SessionStart.sh`
Runs when you start Claude Code:
- Loads today's key levels
- Checks economic calendar for news
- Displays daily limits reminder

### `Stop.sh`
Runs when you stop Claude Code:
- Generates end-of-day summary
- Shows: trades taken, win rate, violations
- Saves summary to file

---

## Contributing

This is a personal project, but if you want to adapt it for your own trading:

1. Fork the repo
2. Update `CLAUDE.md` with your own trading rules
3. Customize skills/hooks to match your strategy
4. Run `pytest` to ensure tests pass
5. Start paper trading

---

## License

MIT License — use at your own risk. This is for educational purposes only. Trading options involves significant risk of loss.

---

## Contact

**Author:** Adem  
**Strategy:** Bill Fanter's 0DTE Masterclass  
**Built with:** Claude Code by Anthropic
