# Trade Journal Skill

## Description
Log trades to the database with ALL 8 confirmations validated. Enforces Bill Fanter's discipline rules before allowing any trade entry.

## When to Invoke
- User says: "log trade", "trade journal", "enter trade", "record trade"
- User provides trade details (symbol, direction, price, confirmations)
- Before executing any real trade (paper or live)

## What This Skill Does

### Trade Entry Logging
1. **Collect Trade Details:**
   - Symbol (SPY, QQQ, AAPL, etc.)
   - Direction (CALL or PUT)
   - Entry price ($1.50, $2.25, etc.)
   - Quantity (number of contracts)
   - Emotional state (DISCIPLINED, FOMO, REVENGE, etc.)

2. **Validate ALL 8 Confirmations:**
   - **Candles:** Green (bullish) or Red (bearish) with conviction
   - **Volume:** >1.2x average volume (high conviction)
   - **VWAP:** Price above (CALL) or below (PUT) VWAP
   - **9 EMA:** Price above (CALL) or below (PUT) 9 EMA
   - **21 EMA:** Price above (CALL) or below (PUT) 21 EMA  
   - **SPY:** Matches trade direction (bullish for CALL, bearish for PUT)
   - **QQQ/Sector:** Matches SPY direction (confluence)
   - **Support/Resistance:** Clear of key levels or confirmed breakout

3. **Enforce Discipline Rules:**
   - ❌ **BLOCK** if pre-market checklist incomplete
   - ❌ **BLOCK** if already took 3 trades today
   - ❌ **BLOCK** if 2 consecutive losses today  
   - ❌ **BLOCK** if daily loss limit reached (-$500 or -20%)
   - ❌ **BLOCK** if ANY confirmation missing

4. **Save to Database:**
   - Log entry to `trades` table with all confirmation flags
   - Set `trade_status = 'OPEN'`
   - Calculate position size validation (max 10-15% of account)

### Trade Exit Logging
1. **Update Existing Trade:**
   - Find open trade by symbol and timestamp
   - Log exit price and timestamp
   - Calculate profit/loss percentage and USD amount
   - Set `trade_status = 'CLOSED'`
   - Log exit reason (STOP_LOSS, PROFIT_TARGET, EOD, MANUAL)

2. **Update Daily Metrics:**
   - Increment win/loss count
   - Update daily P&L running total
   - Check if new daily/account highs or lows

## Context Needed
- Current market data (price, volume, EMAs, VWAP)
- Today's pre-market checklist status
- Today's trade count and P&L
- Account balance (for position sizing validation)

## Tools Used
- `src/persistence/database.py` (save_trade_entry, save_trade_exit)
- Market data API (current price/volume for validation)
- `src/core/confluence.py` (8-confirmation validation)

## Input Format

### For Trade Entry:
```
Symbol: SPY
Direction: CALL
Entry Price: $1.50
Quantity: 2
Emotional State: DISCIPLINED

Confirmations:
✓ Candles: Green Marubozu (strong bull conviction)
✓ Volume: 2.1M (1.8x average, high conviction)  
✓ VWAP: Price $502.20 > VWAP $501.80
✓ 9 EMA: Price $502.20 > 9EMA $501.90
✓ 21 EMA: Price $502.20 > 21EMA $501.60
✓ SPY: Bullish (green candles, above VWAP)
✓ QQQ: Bullish (matches SPY direction)
✓ S/R: Clear above resistance at $502.00
```

### For Trade Exit:
```
Exit Symbol: SPY
Exit Price: $1.88
Exit Reason: PROFIT_TARGET
Notes: Hit +25% target, excellent setup
```

## Output Format

### Successful Entry Log:
```
TRADE LOGGED ✓
===========================================
Trade ID: #47
Symbol: SPY CALL
Entry: $1.50 x 2 contracts = $300 risk
Time: 2026-05-05 10:23:15 AM
Position Size: 15% of account (✓ within 15% limit)

All 8 Confirmations PASSED ✓
- Candles: Green Marubozu ✓
- Volume: 2.1M (1.8x avg) ✓  
- VWAP: Above ($502.20 > $501.80) ✓
- 9 EMA: Above ($502.20 > $501.90) ✓
- 21 EMA: Above ($502.20 > $501.60) ✓
- SPY: Bullish ✓
- QQQ: Bullish ✓
- S/R: Clear above $502.00 ✓

Daily Status:
- Trades today: 1/3
- Daily P&L: -$45 (within -$500 limit)
- Consecutive losses: 0

🎯 Ready to monitor for exit signals
Stop Loss: $1.28 (-15%)
Profit Target: $1.88 (+25%)
===========================================
```

### Blocked Trade Example:
```
TRADE BLOCKED ❌
===========================================
Reason: Missing confirmations

Failed Confirmations:
❌ Volume: 0.8M (only 0.6x average - LOW CONVICTION)
❌ QQQ: Bearish (conflicts with bullish SPY)
❌ S/R: Approaching resistance at $502.50 (wait for break)

Passed Confirmations: 5/8
- Candles: Green ✓
- VWAP: Above ✓
- 9 EMA: Above ✓
- 21 EMA: Above ✓
- SPY: Bullish ✓

💡 SKIP THIS TRADE
Next clean setup coming in 30min - 2hrs
===========================================
```

### Successful Exit Log:
```
TRADE CLOSED ✓
===========================================
Trade ID: #47 - SPY CALL
Entry: $1.50 → Exit: $1.88
Profit: +$76 (+25.3%)
Duration: 1h 23min
Exit Reason: PROFIT_TARGET

Daily Update:
- Trades today: 1/3 (33% win rate today)
- Daily P&L: +$31 (+$76 this trade, -$45 previous)
- Account P&L: +2.1% (within +30% daily target)

✓ Excellent execution! Stuck to plan.
===========================================
```

## Discipline Enforcement

### Pre-Trade Validation (BLOCKS):
```python
# These conditions BLOCK trade logging:
1. Pre-market checklist incomplete
2. Already took 3 trades today  
3. 2 consecutive losses today
4. Daily loss >= $500 OR >= 20% account
5. Any of 8 confirmations missing
6. Position size > 15% of account
7. Market closed or first 15min (9:30-9:45)
```

### Violation Logging:
If user tries to log a blocked trade, save violation to database:
```python
save_violation(
    violation_type="MISSING_CONFIRMATIONS",  # or OVERTRADING, REVENGE, etc.
    description="Attempted trade with 3/8 confirmations",
    context=f"SPY CALL at $1.50, missing volume/QQQ/S&R"
)
```

## Error Handling

**If database save fails:**
```
❌ ERROR: Unable to save trade to database
Check: Database connection, disk space, permissions
Trade details saved to backup: /tmp/trade_backup_TIMESTAMP.json
```

**If missing required fields:**
```
❌ ERROR: Missing required trade details
Required: Symbol, Direction, Entry Price, All 8 Confirmations
Provided: SPY, CALL, $1.50
Missing: Volume confirmation, QQQ confirmation
```

**If market data unavailable:**
```
❌ ERROR: Cannot validate confirmations without market data
Fallback: Manual confirmation entry (use with EXTREME caution)
```

## Follow-Up Actions

After logging trade entry:
1. Set alerts for stop loss (-15%) and profit target (+25%)
2. Add trade to monitoring watchlist
3. Remind user of exit discipline rules
4. Update daily trade count

After logging trade exit:
1. Calculate win rate and average R-multiple
2. Check if daily limits reached (3 trades or profit target)
3. Update weekly/monthly performance metrics
4. If 2 losses in a row → remind user to STOP for the day

## Validation Rules

### Entry Validation:
- All 8 confirmations must be explicitly validated (no assumptions)
- Entry price must be reasonable (within 5% of current market price)
- Position size must be ≤ 15% of account balance
- Symbol must be tradeable (SPY, QQQ, major stocks)
- Market must be open (9:45 AM - 3:45 PM ET on trading days)

### Exit Validation:  
- Must have matching open trade
- Exit price must be reasonable vs entry price
- P&L calculation must be mathematically correct

## Dependencies

- `src/persistence/database.py` (database functions)
- `src/persistence/models.py` (Trade dataclass)
- `src/core/confluence.py` (8-confirmation validation) — TO BE BUILT
- `src/api/market_data.py` (real-time price/volume) — TO BE BUILT
- Market data API (Alpaca or Polygon)

## Integration with Hooks

**PreToolUse.sh validates BEFORE this skill runs:**
- Pre-market checklist complete
- Daily trade limits not exceeded  
- Not in loss streak

**PostToolUse.sh runs AFTER this skill:**
- Auto-logs violations if rules broken
- Updates daily P&L tracking
- Sends alerts if limits approached

## Next Steps After Logging Trade

1. **Monitor trade in real-time** (level-alert skill)
2. **Wait for exit signals** (stop loss, profit target, EOD)
3. **Log exit when triggered** (call this skill again for exit)
4. **Review performance** (generate-report skill)

## Estimated Runtime

1-3 seconds (database write + validation)

## Testing

Test scenarios to validate:
- ✅ Clean 8/8 confirmations → trade logged
- ❌ Missing confirmations → trade blocked  
- ❌ 3 trades today → trade blocked
- ❌ 2 losses in a row → trade blocked
- ❌ Checklist incomplete → trade blocked
- ✅ Valid exit → P&L calculated correctly