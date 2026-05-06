#!/usr/bin/env python3
"""
0DTE Trading System - Streamlit Web UI

A comprehensive web interface for Bill Fanter's 8-confirmation trading system.
Provides morning prep, trade entry, journal, and analytics in a user-friendly UI.

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.append('src')

from persistence.database import (
    init_db, save_trade_entry, save_checklist, get_trade_count_today,
    get_consecutive_losses, get_daily_pnl_usd, is_checklist_complete_today,
    get_checklist_today, get_connection
)
from persistence.models import Trade, PreMarketChecklist
from core.confluence import (
    ConfluenceValidator, MarketData, LevelData, Direction,
    format_confluence_result, ConfirmationResult
)
from core.indicators import calculate_vwap, calculate_ema, get_current_market_snapshot

# Page configuration
st.set_page_config(
    page_title="0DTE Trading System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    text-align: center;
    color: #2E86C1;
    margin-bottom: 2rem;
}
.metric-card {
    background-color: #F8F9FA;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #2E86C1;
}
.success-card {
    background-color: #D5F4E6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #28A745;
}
.warning-card {
    background-color: #FFF3CD;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #FFC107;
}
.danger-card {
    background-color: #F8D7DA;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #DC3545;
}
.confirmation-pass {
    color: #28A745;
    font-weight: bold;
}
.confirmation-fail {
    color: #DC3545;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

def initialize_app():
    """Initialize the application and database"""
    if 'initialized' not in st.session_state:
        init_db()
        st.session_state.initialized = True
        st.session_state.account_size = 10000.0  # Default account size

def get_sample_market_data(symbol: str) -> MarketData:
    """
    Generate sample market data for demo purposes
    In production, this would connect to Alpaca/Polygon API
    """
    # Sample data that varies by symbol
    base_prices = {"SPY": 502.0, "QQQ": 380.0, "AAPL": 175.0, "TSLA": 250.0, "NVDA": 880.0}
    base_price = base_prices.get(symbol, 500.0)

    # Add some random variation
    current_price = base_price + np.random.normal(0, 2)

    return MarketData(
        symbol=symbol,
        current_price=current_price,
        volume=int(np.random.normal(2000000, 500000)),
        avg_volume_20=int(np.random.normal(1500000, 200000)),
        vwap=current_price + np.random.normal(0, 1),
        ema_9=current_price + np.random.normal(-0.5, 0.8),
        ema_21=current_price + np.random.normal(-1.0, 1.2),
        candle_color=np.random.choice(["GREEN", "RED", "DOJI"], p=[0.5, 0.4, 0.1]),
        candle_body_pct=np.random.uniform(0.3, 0.9),
        high=current_price + abs(np.random.normal(0, 1.5)),
        low=current_price - abs(np.random.normal(0, 1.5)),
        close=current_price,
        open=current_price + np.random.normal(0, 1)
    )

def get_sample_levels_data() -> LevelData:
    """Generate sample levels data"""
    return LevelData(
        pdh=503.50,
        pdl=499.80,
        pdc=501.20,
        support_levels=[499.80, 500.50, 501.00],
        resistance_levels=[502.50, 503.50, 504.00]
    )

def display_dashboard():
    """Main dashboard page"""
    st.markdown('<div class="main-header">🎯 0DTE Trading Dashboard</div>', unsafe_allow_html=True)

    # Account overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Account Size", f"${st.session_state.account_size:,.0f}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        trades_today = get_trade_count_today()
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Trades Today", f"{trades_today}/3")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        daily_pnl = get_daily_pnl_usd(st.session_state.account_size)
        color = "success-card" if daily_pnl >= 0 else "danger-card"
        st.markdown(f'<div class="{color}">', unsafe_allow_html=True)
        st.metric("Daily P&L", f"${daily_pnl:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        consecutive_losses = get_consecutive_losses()
        color = "danger-card" if consecutive_losses >= 2 else "metric-card"
        st.markdown(f'<div class="{color}">', unsafe_allow_html=True)
        st.metric("Consecutive Losses", consecutive_losses)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Market status
    st.subheader("📊 Market Status")

    # Check if checklist is complete
    checklist_complete = is_checklist_complete_today()

    if checklist_complete:
        st.markdown('<div class="success-card">✅ Pre-market checklist complete - Ready to trade!</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="warning-card">⚠️ Pre-market checklist incomplete - Complete morning prep first</div>', unsafe_allow_html=True)

    # Discipline status
    st.subheader("🔒 Discipline Status")

    discipline_checks = []

    # Check all discipline rules
    if not checklist_complete:
        discipline_checks.append("❌ Pre-market checklist incomplete")
    else:
        discipline_checks.append("✅ Pre-market checklist complete")

    if trades_today >= 3:
        discipline_checks.append("❌ Daily trade limit reached (3/3)")
    else:
        discipline_checks.append(f"✅ Daily trades: {trades_today}/3")

    if consecutive_losses >= 2:
        discipline_checks.append("❌ 2+ consecutive losses - STOP trading")
    else:
        discipline_checks.append(f"✅ Consecutive losses: {consecutive_losses}")

    if daily_pnl <= -500:
        discipline_checks.append(f"❌ Daily loss limit reached (${daily_pnl:.2f})")
    else:
        discipline_checks.append(f"✅ Daily P&L: ${daily_pnl:.2f}")

    for check in discipline_checks:
        st.write(check)

    # Recent trades summary
    st.subheader("📈 Recent Trades")

    with get_connection() as conn:
        recent_trades = conn.execute("""
            SELECT ticker, direction, entry_price, profit_loss_pct, traded_at
            FROM trades
            ORDER BY traded_at DESC
            LIMIT 5
        """).fetchall()

    if recent_trades:
        try:
            trades_df = pd.DataFrame(recent_trades)
            if not trades_df.empty and 'traded_at' in trades_df.columns:
                trades_df['traded_at'] = pd.to_datetime(trades_df['traded_at'])
                trades_df['P&L %'] = trades_df['profit_loss_pct'].fillna('Open').apply(
                    lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else x
                )

                st.dataframe(
                    trades_df[['ticker', 'direction', 'entry_price', 'P&L %', 'traded_at']],
                    use_container_width=True
                )
            else:
                st.write("No trade data available.")
        except Exception as e:
            st.error(f"Error loading trades: {str(e)}")
            st.write("Raw trade data:", recent_trades)
    else:
        st.write("No trades yet today. Start with morning prep!")

def display_morning_prep():
    """Morning preparation page"""
    st.header("🌅 Morning Preparation")

    st.write("Calculate key levels and complete pre-market checklist before trading.")

    # Check if already completed today
    today_checklist = get_checklist_today()

    if today_checklist and today_checklist['completed']:
        st.success("✅ Morning prep already completed for today!")

        # Display current levels
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Key Levels")
            if today_checklist['pdh']:
                st.write(f"**PDH (Prior Day High):** ${today_checklist['pdh']:.2f}")
            if today_checklist['pdl']:
                st.write(f"**PDL (Prior Day Low):** ${today_checklist['pdl']:.2f}")
            if today_checklist['pdc']:
                st.write(f"**PDC (Prior Day Close):** ${today_checklist['pdc']:.2f}")
            if today_checklist['vwap']:
                st.write(f"**VWAP:** ${today_checklist['vwap']:.2f}")

        with col2:
            st.subheader("📈 Market Bias")
            if today_checklist['spy_bias']:
                st.write(f"**SPY Bias:** {today_checklist['spy_bias']}")
            if today_checklist['vix_level']:
                st.write(f"**VIX Level:** {today_checklist['vix_level']:.2f}")

    else:
        st.warning("⚠️ Morning prep not completed yet.")

        # Manual input form
        with st.form("morning_prep_form"):
            st.subheader("📊 Enter Key Levels")

            col1, col2 = st.columns(2)

            with col1:
                pdh = st.number_input("Prior Day High (PDH)", value=503.50, step=0.01)
                pdl = st.number_input("Prior Day Low (PDL)", value=499.80, step=0.01)
                pdc = st.number_input("Prior Day Close (PDC)", value=501.20, step=0.01)
                vwap = st.number_input("VWAP", value=501.80, step=0.01)

            with col2:
                spy_bias = st.selectbox("SPY Bias", ["BULLISH", "BEARISH", "NEUTRAL"])
                vix_level = st.number_input("VIX Level", value=15.5, step=0.1)
                news_events = st.text_area("News Events", placeholder="FOMC, CPI, earnings, etc.")

            submit_prep = st.form_submit_button("✅ Complete Morning Prep")

            if submit_prep:
                # Save checklist
                checklist = PreMarketChecklist(
                    trade_date=datetime.now().strftime('%Y-%m-%d'),
                    pdh=pdh,
                    pdl=pdl,
                    pdc=pdc,
                    vwap=vwap,
                    spy_bias=spy_bias,
                    vix_level=vix_level,
                    news_events=news_events,
                    completed=True
                )

                save_checklist(checklist)
                st.success("✅ Morning prep completed! You can now start trading.")
                st.rerun()

def display_trade_entry():
    """Trade entry page with 8-confirmation validation"""
    st.header("📈 Trade Entry")

    # Check if trading is allowed
    checklist_complete = is_checklist_complete_today()
    trades_today = get_trade_count_today()
    consecutive_losses = get_consecutive_losses()
    daily_pnl = get_daily_pnl_usd(st.session_state.account_size)

    # Discipline checks
    blocked_reasons = []
    if not checklist_complete:
        blocked_reasons.append("Pre-market checklist incomplete")
    if trades_today >= 3:
        blocked_reasons.append("Already took 3 trades today")
    if consecutive_losses >= 2:
        blocked_reasons.append("2 consecutive losses - STOP for the day")
    if daily_pnl <= -500:
        blocked_reasons.append(f"Daily loss limit reached (${daily_pnl:.2f})")

    if blocked_reasons:
        st.error("🚫 **TRADING BLOCKED**")
        for reason in blocked_reasons:
            st.write(f"• {reason}")
        return

    st.success("✅ All discipline rules passed - trading allowed")

    # Trade entry form
    with st.form("trade_entry_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Trade Details")
            symbol = st.selectbox("Symbol", ["SPY", "QQQ", "AAPL", "TSLA", "NVDA"])
            direction = st.selectbox("Direction", ["CALL", "PUT"])
            entry_price = st.number_input("Entry Price", value=2.15, step=0.01, min_value=0.01)
            quantity = st.number_input("Quantity (contracts)", value=2, step=1, min_value=1)
            emotional_state = st.selectbox("Emotional State",
                                         ["DISCIPLINED", "CONFIDENT", "NERVOUS", "FOMO", "RUSHED"])

        with col2:
            st.subheader("🎯 Position Risk")
            total_risk = entry_price * quantity * 100
            risk_pct = (total_risk / st.session_state.account_size) * 100

            st.metric("Total Risk", f"${total_risk:.0f}")
            st.metric("Risk %", f"{risk_pct:.1f}%")

            if risk_pct > 15:
                st.error("⚠️ Risk exceeds 15% of account!")
            else:
                st.success("✅ Risk within limits")

            # Profit/Loss targets
            stop_loss = entry_price * 0.85
            profit_target = entry_price * 1.25
            st.write(f"**Stop Loss (-15%):** ${stop_loss:.2f}")
            st.write(f"**Profit Target (+25%):** ${profit_target:.2f}")

        st.subheader("🔍 8-Confirmation Analysis")

        # Get market data (sample data for demo)
        market_data = get_sample_market_data(symbol)
        spy_data = get_sample_market_data("SPY")
        qqq_data = get_sample_market_data("QQQ")
        level_data = get_sample_levels_data()

        # Run confluence analysis
        validator = ConfluenceValidator()
        result = validator.validate_all_confirmations(
            symbol=symbol,
            direction=Direction(direction),
            market_data=market_data,
            spy_data=spy_data,
            qqq_data=qqq_data,
            level_data=level_data
        )

        # Display confirmations
        conf_cols = st.columns(4)

        for i, conf in enumerate(result.confirmations):
            with conf_cols[i % 4]:
                if conf.result == ConfirmationResult.PASS:
                    st.success(f"✅ {conf.name}")
                else:
                    st.error(f"❌ {conf.name}")
                st.caption(conf.reason)

        # Overall verdict
        st.subheader("📊 Confluence Result")

        if result.verdict == "HIGH_PROBABILITY":
            st.success(f"🎯 **HIGH PROBABILITY SETUP** ({result.passed_count}/8)")
            st.write("✅ All confirmations aligned - TAKE THE TRADE")
            trade_allowed = True
        elif result.verdict == "WEAK_SETUP":
            st.warning(f"⚠️ **WEAK SETUP** ({result.passed_count}/8)")
            st.write("Consider waiting for cleaner entry")
            trade_allowed = False
        else:
            st.error(f"🛑 **SKIP THE TRADE** ({result.passed_count}/8)")
            st.write("Missing confirmations - wait for next setup")
            trade_allowed = False

        # Submit button
        submit_trade = st.form_submit_button(
            "📝 Log Trade Entry" if trade_allowed else "🚫 Trade Blocked (Weak Setup)",
            disabled=not trade_allowed
        )

        if submit_trade and trade_allowed:
            # Create trade entry
            trade = Trade(
                ticker=symbol,
                direction=direction,
                entry_price=entry_price,
                quantity=quantity,
                emotional_state=emotional_state,
                candle_ok=result.confirmations[0].result == ConfirmationResult.PASS,
                volume_ok=result.confirmations[1].result == ConfirmationResult.PASS,
                vwap_ok=result.confirmations[2].result == ConfirmationResult.PASS,
                ema9_ok=result.confirmations[3].result == ConfirmationResult.PASS,
                ema21_ok=result.confirmations[4].result == ConfirmationResult.PASS,
                spy_ok=result.confirmations[5].result == ConfirmationResult.PASS,
                qqq_ok=result.confirmations[6].result == ConfirmationResult.PASS,
                support_resistance_ok=result.confirmations[7].result == ConfirmationResult.PASS,
            )

            # Save to database
            trade_id = save_trade_entry(trade)

            st.success(f"✅ **Trade #{trade_id} logged successfully!**")
            st.balloons()

            # Display trade summary
            st.info(f"""
            **Trade Summary:**
            - Symbol: {symbol} {direction}
            - Entry: ${entry_price:.2f} x {quantity} contracts
            - Total Risk: ${total_risk:.0f}
            - Confirmations: {result.passed_count}/8
            - Status: OPEN
            """)

def display_trade_journal():
    """Trade journal and history page"""
    st.header("📚 Trade Journal")

    # Get all trades
    with get_connection() as conn:
        trades = conn.execute("""
            SELECT * FROM trades
            ORDER BY traded_at DESC
        """).fetchall()

    if not trades:
        st.write("No trades logged yet. Start with your first trade entry!")
        return

    # Convert to DataFrame
    df = pd.DataFrame(trades)
    df['traded_at'] = pd.to_datetime(df['traded_at'])

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_trades = len(df)
        st.metric("Total Trades", total_trades)

    with col2:
        closed_trades = df[df['profit_loss_pct'].notna()]
        if len(closed_trades) > 0:
            win_rate = (closed_trades['profit_loss_pct'] > 0).mean() * 100
            st.metric("Win Rate", f"{win_rate:.1f}%")
        else:
            st.metric("Win Rate", "N/A")

    with col3:
        if len(closed_trades) > 0:
            avg_return = closed_trades['profit_loss_pct'].mean()
            st.metric("Avg Return", f"{avg_return:.1f}%")
        else:
            st.metric("Avg Return", "N/A")

    with col4:
        total_pnl = get_daily_pnl_usd(st.session_state.account_size)
        st.metric("Total P&L", f"${total_pnl:.2f}")

    # Trade table
    st.subheader("📊 Trade History")

    # Prepare display DataFrame
    display_df = df.copy()
    display_df['P&L %'] = display_df['profit_loss_pct'].fillna('Open').apply(
        lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else x
    )
    display_df['Risk $'] = display_df['entry_price'] * display_df['quantity'] * 100
    display_df['8-Conf'] = (
        display_df[['candle_ok', 'volume_ok', 'vwap_ok', 'ema9_ok',
                   'ema21_ok', 'spy_ok', 'qqq_ok', 'support_resistance_ok']]
        .sum(axis=1)
    ).astype(str) + "/8"

    st.dataframe(
        display_df[['ticker', 'direction', 'entry_price', 'quantity', 'Risk $',
                   '8-Conf', 'emotional_state', 'P&L %', 'traded_at']],
        use_container_width=True
    )

    # P&L Chart (if there are closed trades)
    if len(closed_trades) > 0:
        st.subheader("📈 Performance Chart")

        # Cumulative P&L
        closed_trades_sorted = closed_trades.sort_values('traded_at')
        closed_trades_sorted['cumulative_pnl'] = closed_trades_sorted['profit_loss_pct'].cumsum()

        fig = px.line(closed_trades_sorted, x='traded_at', y='cumulative_pnl',
                     title='Cumulative P&L %', markers=True)
        fig.update_layout(yaxis_title="Cumulative P&L %")
        st.plotly_chart(fig, use_container_width=True)

def display_settings():
    """Settings and configuration page"""
    st.header("⚙️ Settings")

    # Account settings
    st.subheader("💰 Account Settings")

    new_account_size = st.number_input(
        "Account Size",
        value=st.session_state.account_size,
        step=1000.0,
        min_value=1000.0
    )

    if st.button("Update Account Size"):
        st.session_state.account_size = new_account_size
        st.success(f"Account size updated to ${new_account_size:,.0f}")

    # Risk management settings
    st.subheader("⚠️ Risk Management")

    col1, col2 = st.columns(2)

    with col1:
        daily_loss_limit = st.number_input("Daily Loss Limit ($)", value=500, step=50)
        max_trades_per_day = st.number_input("Max Trades Per Day", value=3, step=1, min_value=1)

    with col2:
        max_consecutive_losses = st.number_input("Max Consecutive Losses", value=2, step=1, min_value=1)
        max_position_risk_pct = st.number_input("Max Position Risk %", value=15, step=1, min_value=1)

    # Database management
    st.subheader("🗄️ Database Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Reset Database", type="secondary"):
            if st.button("⚠️ Confirm Reset", type="secondary"):
                os.remove("trades.db")
                init_db()
                st.success("Database reset successfully!")
                st.rerun()

    with col2:
        if st.button("📊 Database Stats"):
            with get_connection() as conn:
                trade_count = conn.execute("SELECT COUNT(*) as count FROM trades").fetchone()['count']
                violation_count = conn.execute("SELECT COUNT(*) as count FROM violations").fetchone()['count']

            st.write(f"**Total Trades:** {trade_count}")
            st.write(f"**Total Violations:** {violation_count}")

def main():
    """Main application"""
    initialize_app()

    # Sidebar navigation
    st.sidebar.title("🎯 0DTE Trading System")
    st.sidebar.markdown("*Bill Fanter's 8-Confirmation Framework*")

    page = st.sidebar.selectbox(
        "Navigate to:",
        ["📊 Dashboard", "🌅 Morning Prep", "📈 Trade Entry", "📚 Trade Journal", "⚙️ Settings"]
    )

    # Quick stats in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Stats")
    st.sidebar.metric("Account", f"${st.session_state.account_size:,.0f}")
    st.sidebar.metric("Trades Today", f"{get_trade_count_today()}/3")
    st.sidebar.metric("Daily P&L", f"${get_daily_pnl_usd(st.session_state.account_size):.2f}")

    # Discipline status
    checklist_complete = is_checklist_complete_today()
    if checklist_complete:
        st.sidebar.success("✅ Ready to trade")
    else:
        st.sidebar.warning("⚠️ Complete morning prep")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Resources")
    st.sidebar.markdown("[📖 Trading Strategy](docs/trading-strategy.md)")
    st.sidebar.markdown("[⚠️ Risk Management](docs/risk-management.md)")
    st.sidebar.markdown("[🏗️ Architecture](docs/architecture.md)")

    # Route to pages
    if page == "📊 Dashboard":
        display_dashboard()
    elif page == "🌅 Morning Prep":
        display_morning_prep()
    elif page == "📈 Trade Entry":
        display_trade_entry()
    elif page == "📚 Trade Journal":
        display_trade_journal()
    elif page == "⚙️ Settings":
        display_settings()

if __name__ == "__main__":
    main()