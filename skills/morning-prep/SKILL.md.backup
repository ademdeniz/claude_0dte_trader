# Morning Prep Skill

## Description
Calculate prior day levels and high-volume zones before market open (9:25 AM).

## When to Invoke
- User says: "run morning prep", "calculate levels", "morning prep", "get PDH PDL"
- Automatically at 9:25 AM ET (if SessionStart hook enabled)
- Before first trade of the day (enforced by PreToolUse hook)

## What This Skill Does

1. Pull SPY data from yesterday (9:30 AM - 4:00 PM), 5-minute bars
2. Calculate key levels:
   - **PDH** (Prior Day High) — max price from yesterday
   - **PDL** (Prior Day Low) — min price from yesterday
   - **PDC** (Prior Day Close) — last 5-min bar close from yesterday
   - **VWAP** — volume-weighted average price for yesterday
3. Find high-volume zones:
   - Group 5-min bars by price level (round to nearest $0.50)
   - Sum volume at each level
   - Identify top 3 price levels with highest volume
4. Identify support/resistance:
   - Find prices where reversals happened (price touched level 2+ times and bounced)
   - Flag these as S/R zones
5. Output to:
   - Terminal (print to screen)
   - Text file: `/output/morning_prep_YYYY-MM-DD.txt`
   - Database: Update `pre_market_checklist` table with levels

## Context Needed
- Today's date
- Market data API credentials (Alpaca or Yahoo Finance)

## Tools Used
- `tools/scripts/morning_prep.py` (Python script)
- Alpaca API or Yahoo Finance (yfinance library)
- SQLite database (`src/persistence/database.py`)

## Output Format

```
SPY MORNING PREP — May 5, 2026
================================
Prior Day High:    $502.50
Prior Day Low:     $500.20
Prior Day Close:   $501.80
Prior Day VWAP:    $501.35

High-Volume Zones:
  $501.00 - $501.50  (Volume: 2.3M)
  $502.00 - $502.50  (Volume: 1.8M)
  $500.00 - $500.50  (Volume: 1.5M)

Support Levels:
  $500.20 (tested 3 times yesterday, held)
  $500.80 (tested 2 times, bounced)

Resistance Levels:
  $502.50 (tested 2 times, rejected)
  $503.00 (prior week high, untested)

================================
✓ Levels calculated and saved
✓ Pre-market checklist updated
```

## Follow-Up Actions

After running this skill, Claude should:
1. Ask: "Should I auto-fill your pre-market checklist with these levels?"
2. If yes: Update `pre_market_checklist` table with:
   - `marked_pdh_pdl_pdc = TRUE`
   - `checked_spy_qqq_vix = TRUE` (if overnight trend analyzed)
3. Remind user to complete remaining checklist items:
   - Check economic calendar
   - Set stop loss and profit target for today
   - Set daily limits

## Error Handling

**If market data API fails:**
```
❌ ERROR: Unable to fetch yesterday's SPY data
Possible causes:
1. API key not set (check .env file)
2. Market was closed yesterday (weekend/holiday)
3. API rate limit exceeded

Fallback: Use TradingView to manually mark levels
```

**If it's a weekend/holiday:**
```
⚠️ Market was closed yesterday
Using last trading day (Friday May 2, 2026)
```

## Validation

Before outputting results, validate:
- PDH > PDL (high must be greater than low)
- PDC between PDL and PDH
- VWAP between PDL and PDH
- High-volume zones make sense (not all at same price level)

If validation fails, alert user and DO NOT save to database.

## Dependencies

- Python 3.9+
- `yfinance` library (free) OR `alpaca-py` (requires API key)
- `pandas` for data manipulation
- `datetime` for date handling
- SQLite database connection

## Estimated Runtime

2-5 seconds (depends on API response time)

## Cost

$0 (if using Yahoo Finance free tier)

## Next Steps After This Skill

1. User completes remaining pre-market checklist items
2. User is now ready to start trading at 9:45 AM
3. `PreToolUse.sh` hook will verify checklist complete before allowing trade logging
