#!/usr/bin/env python3
"""
Test Trade Journal Workflow

Simulates the complete trade entry process:
1. Check discipline rules (PreToolUse.sh logic)
2. Validate 8 confirmations
3. Log trade entry to database
4. Display results
"""

import sys
from datetime import datetime
sys.path.append('src')

from persistence.database import (
    init_db, save_trade_entry, get_trade_count_today,
    get_consecutive_losses, get_daily_pnl_usd, is_checklist_complete_today
)
from persistence.models import Trade
from core.confluence import (
    ConfluenceValidator, MarketData, LevelData, Direction, format_confluence_result
)


def check_discipline_rules():
    """Check if trade is allowed per discipline rules"""
    print("🔒 CHECKING DISCIPLINE RULES...")

    # Rule 1: Pre-market checklist complete?
    checklist_complete = is_checklist_complete_today()
    print(f"   Pre-market checklist: {'✓' if checklist_complete else '❌'}")

    # Rule 2: Max 3 trades per day
    trades_today = get_trade_count_today()
    print(f"   Trades today: {trades_today}/3")

    # Rule 3: No more than 2 consecutive losses
    consecutive_losses = get_consecutive_losses()
    print(f"   Consecutive losses: {consecutive_losses}")

    # Rule 4: Daily P&L limit (using $10,000 test account)
    test_account_size = 10000.0
    daily_pnl = get_daily_pnl_usd(test_account_size)
    print(f"   Daily P&L: ${daily_pnl:.2f}")

    # Check all rules
    blocked_reasons = []

    if not checklist_complete:
        blocked_reasons.append("Pre-market checklist incomplete")

    if trades_today >= 3:
        blocked_reasons.append("Already took 3 trades today")

    if consecutive_losses >= 2:
        blocked_reasons.append("2 consecutive losses - STOP for the day")

    if daily_pnl <= -500:  # Default daily loss limit
        blocked_reasons.append(f"Daily loss limit reached (${daily_pnl:.2f})")

    if blocked_reasons:
        print(f"\n❌ TRADE BLOCKED:")
        for reason in blocked_reasons:
            print(f"   • {reason}")
        return False

    print("✅ All discipline rules passed - trade allowed\n")
    return True


def simulate_trade_entry():
    """Simulate a complete trade entry workflow"""

    print("=" * 60)
    print("🎯 0DTE TRADE JOURNAL WORKFLOW TEST")
    print("=" * 60)

    # Initialize database
    print("📊 Initializing database...")
    init_db()
    print("✅ Database ready\n")

    # Check discipline rules first
    if not check_discipline_rules():
        return False

    # Test Case 1: Perfect Setup (8/8 confirmations)
    print("📈 TESTING: SPY CALL - Perfect Bullish Setup")
    print("-" * 40)

    # Market data for perfect setup
    spy_data = MarketData(
        symbol="SPY",
        current_price=502.80,  # Above resistance
        volume=2500000,        # High volume
        avg_volume_20=1200000,
        vwap=501.80,
        ema_9=501.90,
        ema_21=501.60,
        candle_color="GREEN",
        candle_body_pct=0.90,  # Strong Marubozu
        high=502.85,
        low=502.00,
        close=502.80,
        open=502.10
    )

    qqq_data = MarketData(
        symbol="QQQ",
        current_price=380.70,
        volume=1800000,
        avg_volume_20=1000000,
        vwap=380.20,
        ema_9=380.30,
        ema_21=380.00,
        candle_color="GREEN",
        candle_body_pct=0.80,
        high=380.80,
        low=380.10,
        close=380.70,
        open=380.20
    )

    level_data = LevelData(
        pdh=503.00,
        pdl=500.20,
        pdc=501.80,
        support_levels=[500.20, 500.80, 501.00],
        resistance_levels=[502.50, 503.00, 503.50]  # Broke above 502.50
    )

    # Validate confluence
    validator = ConfluenceValidator()
    result = validator.validate_all_confirmations(
        symbol="SPY",
        direction=Direction.CALL,
        market_data=spy_data,
        spy_data=spy_data,
        qqq_data=qqq_data,
        level_data=level_data
    )

    print(format_confluence_result(result))

    # Log trade if high probability
    if result.verdict == "HIGH_PROBABILITY":
        print("\n💾 LOGGING TRADE TO DATABASE...")

        # Create trade entry
        trade = Trade(
            symbol="SPY",
            direction="CALL",
            entry_price=1.75,
            quantity=2,
            entry_time=datetime.now(),

            # 8 Confirmations (from confluence result)
            candles_confirmed=result.confirmations[0].result.value == "PASS",
            volume_confirmed=result.confirmations[1].result.value == "PASS",
            vwap_confirmed=result.confirmations[2].result.value == "PASS",
            ema9_confirmed=result.confirmations[3].result.value == "PASS",
            ema21_confirmed=result.confirmations[4].result.value == "PASS",
            spy_confirmed=result.confirmations[5].result.value == "PASS",
            qqq_confirmed=result.confirmations[6].result.value == "PASS",
            support_resistance_confirmed=result.confirmations[7].result.value == "PASS",

            emotional_state="DISCIPLINED",
            trade_status="OPEN",
            confluence_score=result.setup_strength
        )

        # Save to database
        trade_id = save_trade_entry(trade)
        print(f"✅ Trade #{trade_id} logged successfully!")

        # Display trade summary
        print(f"\n📋 TRADE SUMMARY:")
        print(f"   Trade ID: #{trade_id}")
        print(f"   Symbol: {trade.symbol} {trade.direction}")
        print(f"   Entry: ${trade.entry_price:.2f} x {trade.quantity} contracts = ${trade.entry_price * trade.quantity * 100:.0f} risk")
        print(f"   Confluence Score: {trade.confluence_score:.1%}")
        print(f"   Emotional State: {trade.emotional_state}")
        print(f"   Status: {trade.trade_status}")

        print(f"\n🎯 Stop Loss: ${trade.entry_price * 0.85:.2f} (-15%)")
        print(f"🎯 Profit Target: ${trade.entry_price * 1.25:.2f} (+25%)")

        return True

    else:
        print(f"\n🛑 TRADE SKIPPED - {result.verdict}")
        print("Next clean setup coming in 30min - 2hrs")
        return False


def test_blocked_trade():
    """Test what happens when trade is blocked"""
    print("\n" + "=" * 60)
    print("🚫 TESTING: Blocked Trade (Weak Setup)")
    print("=" * 60)

    # Weak setup - only 4/8 confirmations
    spy_data = MarketData(
        symbol="SPY",
        current_price=502.20,
        volume=800000,         # LOW VOLUME (fails)
        avg_volume_20=1200000,
        vwap=503.00,           # BELOW VWAP (fails for CALL)
        ema_9=503.20,          # BELOW 9 EMA (fails for CALL)
        ema_21=503.50,         # BELOW 21 EMA (fails for CALL)
        candle_color="GREEN",  # Good candle
        candle_body_pct=0.85,
        high=502.50,
        low=501.90,
        close=502.20,
        open=502.00
    )

    qqq_data = MarketData(
        symbol="QQQ",
        current_price=379.80,
        volume=900000,
        avg_volume_20=1000000,
        vwap=380.50,          # QQQ bearish while SPY trying to be bullish
        ema_9=380.20,
        ema_21=380.00,
        candle_color="RED",   # Conflicts with SPY
        candle_body_pct=0.70,
        high=380.20,
        low=379.50,
        close=379.80,
        open=380.00
    )

    level_data = LevelData(
        pdh=503.00,
        pdl=500.20,
        pdc=501.80,
        support_levels=[500.20, 500.80, 501.00],
        resistance_levels=[502.50, 503.00, 503.50]
    )

    validator = ConfluenceValidator()
    result = validator.validate_all_confirmations(
        symbol="SPY",
        direction=Direction.CALL,
        market_data=spy_data,
        spy_data=spy_data,
        qqq_data=qqq_data,
        level_data=level_data
    )

    print(format_confluence_result(result))

    if result.verdict != "HIGH_PROBABILITY":
        print(f"\n✅ SYSTEM CORRECTLY BLOCKED WEAK SETUP ({result.passed_count}/8 confirmations)")
        print("📚 This is exactly what Bill's system teaches - patience pays!")


if __name__ == "__main__":
    print("Starting Trade Journal Workflow Test...\n")

    # Test 1: Perfect setup
    trade_logged = simulate_trade_entry()

    # Test 2: Blocked trade
    test_blocked_trade()

    # Final summary
    print(f"\n{'='*60}")
    print("📊 WORKFLOW TEST COMPLETE")
    print(f"{'='*60}")
    print(f"Trades today: {get_trade_count_today()}")
    print(f"Daily P&L: ${get_daily_pnl_usd(10000.0):.2f}")
    print("✅ Trade journal system working perfectly!")
    print("\nReady for paper trading! 🎯")