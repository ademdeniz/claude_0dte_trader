#!/bin/bash
# PreToolUse.sh
# Runs BEFORE any tool is called
# Enforces discipline rules (blocks trades if rules violated)

set -e

DB_PATH="/home/claude/claude_0dte_trader/trades.db"
TODAY=$(date +%Y-%m-%d)

echo "🔍 Pre-flight checks..."

# ==================================================
# CHECK 1: Pre-market checklist complete?
# ==================================================
CHECKLIST_STATUS=$(sqlite3 "$DB_PATH" "SELECT checklist_complete FROM pre_market_checklist WHERE date='$TODAY'" 2>/dev/null || echo "0")

if [ "$CHECKLIST_STATUS" != "1" ]; then
  echo ""
  echo "❌ BLOCKED: You haven't completed your pre-market checklist today."
  echo ""
  echo "Required actions:"
  echo "  1. Run: 'Claude, run morning prep'"
  echo "  2. Complete pre-market checklist"
  echo ""
  echo "You cannot log trades until checklist is complete."
  exit 1
fi

# ==================================================
# CHECK 2: Have you already taken 3 trades today?
# ==================================================
TRADE_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM trades WHERE date='$TODAY'" 2>/dev/null || echo "0")

if [ "$TRADE_COUNT" -ge 3 ]; then
  echo ""
  echo "❌ BLOCKED: You've already taken 3 trades today (daily limit)."
  echo ""
  echo "RULE: Max 3 trades per day"
  echo "Close your charts and walk away."
  echo "Come back tomorrow."
  exit 1
fi

# ==================================================
# CHECK 3: Did you take 2 losses in a row?
# ==================================================
LAST_TWO=$(sqlite3 "$DB_PATH" "SELECT result FROM trades WHERE date='$TODAY' ORDER BY exit_time DESC LIMIT 2" 2>/dev/null || echo "")

if [ "$LAST_TWO" = "$(printf 'LOSS\nLOSS')" ]; then
  echo ""
  echo "❌ BLOCKED: You took 2 losses in a row."
  echo ""
  echo "RULE: 2 losses in a row = STOP FOR THE DAY"
  echo "Your brain is tilted. You WILL make bad decisions if you continue."
  echo ""
  echo "Close your charts. Come back tomorrow."
  exit 1
fi

# ==================================================
# CHECK 4: Have you hit your daily loss limit?
# ==================================================
DAILY_PL=$(sqlite3 "$DB_PATH" "SELECT COALESCE(SUM(profit_loss_dollar), 0) FROM trades WHERE date='$TODAY'" 2>/dev/null || echo "0")

# Get user's daily loss limit from settings (default: -500)
DAILY_LOSS_LIMIT=$(sqlite3 "$DB_PATH" "SELECT value FROM settings WHERE key='daily_loss_limit'" 2>/dev/null || echo "-500")

# Convert to absolute value for comparison
DAILY_PL_ABS=$(echo "$DAILY_PL" | tr -d '-')
DAILY_LOSS_LIMIT_ABS=$(echo "$DAILY_LOSS_LIMIT" | tr -d '-')

if (( $(echo "$DAILY_PL < 0" | bc -l) )) && (( $(echo "$DAILY_PL_ABS >= $DAILY_LOSS_LIMIT_ABS" | bc -l) )); then
  echo ""
  echo "❌ BLOCKED: You've hit your daily loss limit."
  echo ""
  echo "Daily P/L: \$$DAILY_PL"
  echo "Loss limit: \$$DAILY_LOSS_LIMIT"
  echo ""
  echo "RULE: Daily loss limit protects against catastrophic losses"
  echo "Close your charts. Come back tomorrow."
  exit 1
fi

# ==================================================
# CHECK 5: Is it within the first 15 minutes? (9:30-9:45 AM)
# ==================================================
CURRENT_TIME=$(date +%H:%M)

if [[ "$CURRENT_TIME" > "09:30" && "$CURRENT_TIME" < "09:45" ]]; then
  echo ""
  echo "⚠️  WARNING: It's currently $CURRENT_TIME (first 15 minutes)"
  echo ""
  echo "RECOMMENDATION: Avoid trading 9:30-9:45 AM (pump & dump zone)"
  echo ""
  read -p "Do you still want to proceed? (yes/no): " PROCEED
  
  if [ "$PROCEED" != "yes" ]; then
    echo "Trade blocked. Wait until 9:45 AM."
    exit 1
  fi
  
  echo "⚠️  Proceeding at your own risk..."
fi

# ==================================================
# ALL CHECKS PASSED
# ==================================================
echo "✅ Pre-flight checks passed"
echo "✅ Pre-market checklist: Complete"
echo "✅ Trades today: $TRADE_COUNT / 3"
echo "✅ Daily P/L: \$$DAILY_PL"
echo ""
echo "Proceeding..."
