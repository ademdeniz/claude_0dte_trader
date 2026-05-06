# 0DTE Options Trading System

## Project Overview

An AI-assisted trading system for 0DTE (zero days to expiration) options trading, built on Bill Fanter's 8-confirmation framework with integrated emotional discipline guardrails.

**Owner:** Adem (Software QA Engineer / SDET)  
**Strategy:** Bill Fanter's 0DTE Masterclass  
**Purpose:** Paper trading → Live trading with full discipline enforcement

---

## Architecture Rules

### 1. Naming Conventions

**Files:**
- Python modules: `snake_case.py`
- Skills: `kebab-case/SKILL.md`
- Hooks: `PascalCase.sh`
- Docs: `kebab-case.md`

**Database:**
- Tables: `snake_case` (trades, violations, pre_market_checklist)
- Columns: `snake_case` (entry_price, profit_loss_pct)

**Code:**
- Functions: `snake_case()` (calculate_vwap, check_confluence)
- Classes: `PascalCase` (Trade, Violation, MarketData)
- Constants: `UPPER_SNAKE_CASE` (MAX_TRADES_PER_DAY, STOP_LOSS_PCT)

### 2. Test Expectations

**Every module in src/ must have:**
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Minimum 80% code coverage

**Critical paths requiring tests:**
- Confluence logic (all 8 confirmations)
- Stop loss calculation
- Position sizing validation
- Database writes (trades, violations)

**Test execution:**
- `pytest` for all tests
- `pytest --cov` for coverage reports
- Pre-commit hook blocks commits if tests fail

### 3. Repository Map

```
claude_0dte_trader/
├── CLAUDE.md                    # THIS FILE - project constitution
├── README.md                    # Human-readable overview
├── .claude/
│   └── settings.json            # Claude Code configuration
├── docs/
│   ├── architecture.md          # System design decisions
│   ├── trading-strategy.md      # Bill's 8-confirmation framework
│   └── risk-management.md       # The 8 emotional traps + discipline rules
├── skills/
│   ├── morning-prep/SKILL.md    # Calculate PDH/PDL/PDC/VWAP
│   ├── confluence-check/SKILL.md # Validate 8 confirmations
│   ├── trade-journal/SKILL.md   # Log trades to database
│   ├── level-alert/SKILL.md     # Monitor proximity to key levels
│   └── generate-report/SKILL.md # Weekly/daily summaries
├── hooks/
│   ├── PreToolUse.sh            # Block trades if rules violated
│   ├── PostToolUse.sh           # Auto-log violations
│   ├── SessionStart.sh          # Load today's data
│   └── Stop.sh                  # End-of-day summary
├── src/
│   ├── api/
│   │   ├── market_data.py       # Alpaca/Polygon integration
│   │   └── notifications.py     # Twilio/Pushover alerts
│   ├── core/
│   │   ├── indicators.py        # VWAP, EMA, volume calculations
│   │   ├── confluence.py        # 8-confirmation logic
│   │   └── levels.py            # PDH/PDL/PDC/support/resistance
│   └── persistence/
│       ├── database.py          # SQLite connection + schema
│       └── models.py            # Trade, Violation, Checklist models
├── tools/
│   ├── scripts/
│   │   ├── morning_prep.py      # Standalone morning prep script
│   │   └── real_time_monitor.py # Streaming data handler
│   └── prompts/
│       ├── trade_entry.md       # Template for logging trades
│       └── violation_check.md   # Template for checking violations
└── tests/
    ├── unit/
    └── integration/
```

---

## Trading Strategy (8-Confirmation Framework)

### Core Principle
**Every trade requires ALL 8 confirmations. Missing even ONE = skip the trade.**

### The 8 Confirmations (in order)

#### 1. **Candles**
- **CALL:** Green candles (close > open), ideally Marubozu (fat body, bulls dominated)
- **PUT:** Red candles (close < open), ideally Marubozu (fat body, bears dominated)
- **SKIP:** Doji (tiny body = indecision), extreme wicking (waiting for news)

#### 2. **Volume**
- **Requirement:** High volume (current bar > 1.2x average of last 20 bars)
- **Why:** High volume = conviction. Low volume = fake move.
- **SKIP:** Low volume setups (even if other confirmations align)

#### 3. **VWAP (Volume-Weighted Average Price)**
- **CALL:** Price ABOVE VWAP (bulls control)
- **PUT:** Price BELOW VWAP (bears control)
- **Note:** VWAP acts as a magnet — price tends to revert to it

#### 4. **9 EMA (Fast Moving Average)**
- **CALL:** Price ABOVE 9 EMA (bullish momentum)
- **PUT:** Price BELOW 9 EMA (bearish momentum)

#### 5. **21 EMA (Slow Moving Average)**
- **CALL:** Price ABOVE 21 EMA (bullish trend)
- **PUT:** Price BELOW 21 EMA (bearish trend)

#### 6. **SPY (Market Direction)** — for index trading
- **CALL:** SPY bullish (green candles, above VWAP/EMAs)
- **PUT:** SPY bearish (red candles, below VWAP/EMAs)
- **For individual stocks:** Check if stock matches SPY direction

#### 7. **QQQ / Sector ETF (Confluence Check)**
- **Index trading:** QQQ must match SPY direction
- **Stock trading:** Sector ETF (XLK, XLY, XLF, etc.) must match stock direction
- **SKIP:** Divergence (SPY bullish but QQQ bearish = conflicting signals)

#### 8. **Support / Resistance (Clear or Breakout)**
- **Key levels:** PDH (prior day high), PDL (prior day low), PDC (prior day close), VWAP
- **CALL:** Either (a) clear of resistance OR (b) breakout confirmed (broke above with high volume)
- **PUT:** Either (a) clear of support OR (b) breakdown confirmed (broke below with high volume)
- **SKIP:** Approaching level without confirmation (wait for break or bounce)

### Perfect Bullish Stack (CALL)
```
Price > 9 EMA > 21 EMA > VWAP (all pointing up)
+ Green candles
+ High volume
+ SPY bullish
+ QQQ bullish (or sector ETF for stocks)
+ Clear of resistance
```

### Perfect Bearish Stack (PUT)
```
VWAP > 21 EMA > 9 EMA > Price (all pointing down)
+ Red candles
+ High volume
+ SPY bearish
+ QQQ bearish (or sector ETF for stocks)
+ Clear of support
```

---

## Risk Management (The 8 Discipline Rules)

### Daily Limits (HARD RULES — NEVER BREAK)

1. **Max 3 trades per day**
   - No exceptions
   - After 3rd trade, close charts and walk away

2. **2 losses in a row = STOP FOR THE DAY**
   - If Trade 1 = LOSS, Trade 2 = LOSS → Done
   - Close everything, come back tomorrow

3. **Daily loss limit: -$500 OR -20% of account** (set in settings)
   - Hit this number = done for the day
   - Protects against catastrophic losses

4. **Daily profit target: +25-30%** (optional stop)
   - If you hit this early, consider stopping
   - Greed kills accounts

### Position Sizing

**Rule:** Never risk more than 10-15% of total account per trade

**Examples:**
- $1,000 account → Max $100-150 per trade (1 contract)
- $5,000 account → Max $500-750 per trade (1-2 contracts)
- $10,000 account → Max $1,000-1,500 per trade (2-4 contracts)

### Stop Loss Rules

**SPY/QQQ (0DTE):** -15% stop loss  
**AAPL (moderate volatility):** -12% stop loss  
**NVDA/TSLA (high volatility):** -10% stop loss  

**Example:**
- Entry: $1.50
- Stop loss (-15%): Exit at $1.28 or lower
- **NO EXCEPTIONS:** If stop hit, exit immediately

### Profit Targets

**Target:** +25% to +50%  

**Scaling out (optional):**
- Sell 1/3 at +15%
- Sell 1/3 at +25%
- Let 1/3 run to +50% or close at end of day

### The 8 Emotional Traps (NEVER DO THESE)

1. **NO FOMO (Fear of Missing Out)**
   - If you missed the entry, skip it
   - Next clean setup coming in 30 min - 2 hours
   - Chasing = gambling

2. **NO OVERTRADING**
   - More trades ≠ more profit
   - 1-3 high-quality trades > 10 mediocre trades
   - Overtrading = giving back all gains

3. **NO REVENGE TRADING**
   - Took a loss? Accept it. Move on.
   - Don't try to "make it back" immediately
   - 2 losses in a row = STOP (see rule above)

4. **NO ADDING TO LOSERS (Averaging Down)**
   - Stop loss is FINAL
   - Don't buy more to "lower your average"
   - If the setup was wrong once, it's still wrong

5. **NO TRADING WITHOUT CHECKLIST**
   - Pre-market checklist MUST be complete before first trade
   - No checklist = No trades
   - Hooks enforce this automatically

6. **TRUST THE STRATEGY**
   - 1 winning trade ≠ you're a genius
   - 1 losing trade ≠ you're a failure
   - Even best traders lose 40-50% of trades
   - Your job: win more on winners than lose on losers

7. **CUT LOSERS, LET WINNERS RUN**
   - Exit at stop loss: -15%
   - Hold to profit target: +25-50%
   - Don't cut winners early out of fear
   - Don't let losers run hoping for reversal

8. **FULL ATTENTION ONLY**
   - No distractions (no Twitter, email, YouTube)
   - Can't focus? Don't trade that day
   - Phone on Do Not Disturb
   - 0DTE requires 100% focus

### When to Stay in CASH (Do NOT Trade)

- ❌ First 15 minutes (9:30-9:45 AM) — pump & dump zone
- ❌ Major news days (FOMC, CPI, jobs report)
- ❌ Earnings day (or ±1 day for individual stocks)
- ❌ Sideways/choppy market (no clear trend)
- ❌ Extreme wicking (waiting for news)
- ❌ No confluence (SPY/QQQ/Sector diverging)
- ❌ Missing confirmations (fewer than 8)
- ❌ Feeling emotional (frustrated, rushed, tilted)
- ❌ Can't give full attention (distracted, tired)

**Mantra:** Cash is a position. Patience = profitability.

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update tasks/lessons.md with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

---

## Task Management

1. **Plan First**: Write plan to tasks/todo.md with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to tasks/todo.md
6. **Capture Lessons**: Update tasks/lessons.md after corrections

---

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.

---

## Technology Stack

**Language:** Python 3.9+  
**Database:** SQLite (local, lightweight)  
**Market Data:** Alpaca (free tier) or Polygon.io ($29/month for real-time)  
**Notifications:** Twilio ($0.0075/SMS) or Pushover ($5 one-time)  
**Technical Indicators:** pandas-ta or ta-lib  
**Testing:** pytest + pytest-cov  

---

## Success Metrics

### Phase 1 (Paper Trading - Weeks 1-4)
- Complete 50 trades following ALL 8 confirmations
- Win rate: 55%+ 
- Discipline score: 90%+ (follow rules on 90%+ of trades)
- Zero violations in final week

### Phase 2 (Automation - Weeks 5-8)
- Morning Prep script running daily
- Pre-market checklist auto-populated
- Key levels calculated accurately
- Move to 100 paper trades

### Phase 3 (Real-Time Alerts - Weeks 9-12)
- Level Monitor sending accurate alerts
- Confluence Bot detecting high-probability setups
- Alert accuracy: 80%+ (80% of alerts are valid setups)

### Phase 4 (Live Trading - Month 4+)
- Start with $1,000 real money
- Same discipline rules apply
- Win rate maintained: 55%+
- Grow account: +10% per month target
