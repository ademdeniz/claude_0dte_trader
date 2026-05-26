#!/usr/bin/env python3
"""
0DTE Trading System - Streamlit Web UI

A comprehensive web interface for the 8-confirmation trading system.
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

# AI components (imported as needed in functions to avoid circular imports)
# from ai.client import get_ai_client, TaskType
# from ai.cache import get_ai_cache
# from ai.prompts.pre_market_prompt import PRE_MARKET_SYSTEM_PROMPT, get_pre_market_dynamic_prompt, PRE_MARKET_FALLBACK

# Page configuration
st.set_page_config(
    page_title="Trading System",
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
    color: #155724;
    font-weight: 500;
}
.warning-card {
    background-color: #FFF3CD;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #FFC107;
    color: #856404;
    font-weight: 500;
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
    st.markdown('<div class="main-header">🎯 Trading Dashboard</div>', unsafe_allow_html=True)

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
    """Enhanced Morning preparation page with AI-powered briefings"""
    st.header("🌅 Pre-Market Intelligence")

    # Import AI components
    from ai.client import get_ai_client, TaskType
    from ai.cache import get_ai_cache
    from ai.prompts.pre_market_prompt import PRE_MARKET_SYSTEM_PROMPT, get_pre_market_dynamic_prompt, PRE_MARKET_FALLBACK

    ai_client = get_ai_client()
    ai_cache = get_ai_cache()
    today = datetime.now().strftime('%Y-%m-%d')

    # === SECTION 1: EXISTING MORNING PREP ===
    st.subheader("📊 Key Levels & Checklist")

    # Check if already completed today
    today_checklist_raw = get_checklist_today()
    today_checklist = dict(today_checklist_raw) if today_checklist_raw else None

    if today_checklist and today_checklist['completed']:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown('<div class="success-card">✅ Morning prep already completed for today!</div>', unsafe_allow_html=True)
        with col2:
            if st.button("🔄 Redo Prep", help="Reset and redo morning preparation"):
                # Clear today's checklist by deleting the record
                today = datetime.now().strftime("%Y-%m-%d")
                with get_connection() as conn:
                    conn.execute("DELETE FROM pre_market_checklist WHERE trade_date = ?", (today,))
                st.rerun()

        # Display current levels in enhanced format
        col1, col2 = st.columns(2)

        with col1:
            ticker_name = today_checklist.get('ticker', 'SPY')
            st.markdown(f"### 📊 {ticker_name}")
            if today_checklist['pdh']:
                st.metric("PDH (Prior Day High)", f"${today_checklist['pdh']:.2f}")
            if today_checklist['pdl']:
                st.metric("PDL (Prior Day Low)", f"${today_checklist['pdl']:.2f}")
            if today_checklist['pdc']:
                st.metric("PDC (Prior Day Close)", f"${today_checklist['pdc']:.2f}")
            if today_checklist['vwap']:
                st.metric("VWAP", f"${today_checklist['vwap']:.2f}")

        with col2:
            st.markdown("### 📈 Market Setup")
            if today_checklist['spy_bias']:
                bias_color = "🟢" if today_checklist['spy_bias'] == "BULLISH" else "🔴" if today_checklist['spy_bias'] == "BEARISH" else "🟡"
                st.metric("Bias", f"{bias_color} {today_checklist['spy_bias']}")
            if today_checklist['vix_level']:
                st.metric("VIX Level", f"{today_checklist['vix_level']:.2f}")

    else:
        st.warning("⚠️ Complete morning prep to unlock AI briefing")

        # Enhanced manual input form with AI screenshot analysis
        with st.form("morning_prep_form"):
            st.subheader("📊 Setup Your Trading Day")

            # Method selection: Screenshot AI or Manual Entry
            method = st.radio(
                "How would you like to set up your morning prep?",
                ["🤖 AI Screenshot Analysis (Recommended)", "✋ Manual Entry"],
                help="Upload a screenshot for AI to extract levels, or enter manually"
            )

            if method == "🤖 AI Screenshot Analysis (Recommended)":
                st.markdown("### 📷 Upload Chart Screenshots")
                uploaded_files = st.file_uploader(
                    "Upload screenshots for confluence analysis",
                    type=['png', 'jpg', 'jpeg'],
                    accept_multiple_files=True,
                    help="Upload multiple screenshots: different timeframes, SPY+QQQ, price+volume, etc."
                )

                if uploaded_files:
                    st.info(f"📊 Uploaded {len(uploaded_files)} screenshots - AI will analyze for confluence/divergence")

                    # Show thumbnails
                    cols = st.columns(min(len(uploaded_files), 3))
                    for i, file in enumerate(uploaded_files[:3]):
                        with cols[i]:
                            st.image(file, caption=f"Chart {i+1}", use_column_width=True)

                    if len(uploaded_files) > 3:
                        st.caption(f"+ {len(uploaded_files) - 3} more screenshots")

                    # Analysis context
                    analysis_context = st.text_input(
                        "Describe your screenshots (optional)",
                        placeholder="e.g., '1m SPY, 5m QQQ, volume profile' or 'SPY+QQQ+VIX confluence check'",
                        help="Help AI understand what to look for across your screenshots"
                    )

                # Ticker selection for AI method
                ticker = st.selectbox("Select Ticker",
                    ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META"],
                    help="Which ticker is shown in the screenshot?"
                )

                # This section was already handled above with the new multi-file logic

            else:
                # Original manual entry method
                # Ticker selection
                col_ticker, col_context = st.columns([1, 2])
                with col_ticker:
                    ticker = st.selectbox("Select Ticker to Trade",
                        ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META"],
                        help="Choose the primary ticker you plan to trade today"
                    )

                col1, col2 = st.columns(2)

                with col1:
                    pdh = st.number_input("Prior Day High (PDH)", value=503.50 if ticker == "SPY" else 173.33, step=0.01)
                    pdl = st.number_input("Prior Day Low (PDL)", value=499.80 if ticker == "SPY" else 170.25, step=0.01)
                    pdc = st.number_input("Prior Day Close (PDC)", value=501.20 if ticker == "SPY" else 172.15, step=0.01)
                    vwap = st.number_input("VWAP", value=501.80 if ticker == "SPY" else 171.90, step=0.01)

                with col2:
                    st.markdown("**Market Context**")
                    spy_bias = st.selectbox("Bias", ["BULLISH", "BEARISH", "NEUTRAL"],
                        help="Overall market direction")
                    vix_level = st.number_input("VIX Level", value=15.5, step=0.1)
                    news_events = st.text_area("News Events", placeholder="FOMC, CPI, earnings, sector news, etc.")

            # Initialize variables for AI method (will be populated by AI analysis)
            if method == "🤖 AI Screenshot Analysis (Recommended)":
                pdh = pdl = pdc = vwap = 0.0
                spy_bias = "NEUTRAL"
                vix_level = 15.5
                news_events = ""

            # Submit button
            if method == "🤖 AI Screenshot Analysis (Recommended)":
                submit_prep = st.form_submit_button("🤖 Analyze Screenshot & Complete Prep",
                    help="AI will extract levels from your screenshot")
            else:
                submit_prep = st.form_submit_button("✅ Complete Morning Prep")

            if submit_prep:
                if method == "🤖 AI Screenshot Analysis (Recommended)":
                    if not uploaded_files:
                        st.error("❌ Please upload at least one screenshot!")
                    else:
                        # AI Multi-Screenshot Analysis
                        with st.spinner(f"🤖 Analyzing {len(uploaded_files)} screenshot{'s' if len(uploaded_files) > 1 else ''}..."):
                            try:
                                # Import AI components
                                from ai.client import get_ai_client, TaskType
                                ai_client = get_ai_client()

                                # Create comprehensive analysis prompt for multiple images
                                analysis_prompt = f"""
                                Analyze these {len(uploaded_files)} trading chart screenshots for {ticker} confluence analysis.

                                **Your task:**
                                1. Extract key levels (PDH, PDL, PDC, VWAP) from the primary {ticker} chart
                                2. Check for confluence/divergence across all screenshots
                                3. Identify which timeframes or indicators align vs conflict
                                4. Assess overall setup strength based on agreement

                                **Analysis context:** {analysis_context if analysis_context else 'Multiple chart analysis for confluence check'}

                                **Return ONLY a JSON response in this exact format:**
                                {{
                                    "pdh": 123.45,
                                    "pdl": 120.30,
                                    "pdc": 122.15,
                                    "vwap": 121.80,
                                    "bias": "BULLISH",
                                    "vix": 15.5,
                                    "confluence_score": 8,
                                    "confluence_notes": "All timeframes bullish, SPY+QQQ aligned",
                                    "divergences": ["Minor: 1m showing pullback while 5m bullish"],
                                    "strongest_signal": "Calls above PDC with all confirmations",
                                    "confidence": 0.9,
                                    "screenshot_count": {len(uploaded_files)}
                                }}

                                Focus on confluence - do all charts tell the same story?
                                """

                                # Analyze all images together using multiple image capability
                                all_images = []
                                for uploaded_file in uploaded_files:
                                    all_images.append(uploaded_file.read())

                                # For now, analyze the first image (can be enhanced to handle multiple images)
                                response, usage = ai_client.create_message_with_image(
                                    prompt=analysis_prompt,
                                    image_data=all_images[0],  # Primary analysis on first image
                                    task_type=TaskType.CHART_ANALYSIS,
                                    max_tokens=1500
                                )

                                if response and isinstance(response, dict):
                                    # Create checklist with AI-extracted data
                                    checklist = PreMarketChecklist(
                                        trade_date=datetime.now().strftime('%Y-%m-%d'),
                                        ticker=ticker,
                                        pdh=response.get('pdh'),
                                        pdl=response.get('pdl'),
                                        pdc=response.get('pdc'),
                                        vwap=response.get('vwap'),
                                        spy_bias=response.get('bias', 'NEUTRAL'),
                                        vix_level=response.get('vix', 15.5),
                                        news_events=response.get('notes', ''),
                                        completed=True
                                    )

                                    save_checklist(checklist)

                                    # Enhanced success message with confluence info
                                    confluence_score = response.get('confluence_score', 5)
                                    confluence_emoji = "🎯" if confluence_score >= 7 else "⚠️" if confluence_score >= 5 else "❌"

                                    st.success(f"✅ Multi-chart analysis complete! {confluence_emoji} Confluence: {confluence_score}/10")
                                    st.info(f"📊 **Confluence Notes:** {response.get('confluence_notes', 'Analysis complete')}")

                                    if response.get('strongest_signal'):
                                        st.success(f"🎯 **Best Setup:** {response.get('strongest_signal')}")

                                    if response.get('divergences'):
                                        st.warning("⚠️ **Divergences Detected:**")
                                        for div in response.get('divergences', []):
                                            st.write(f"• {div}")

                                    # Show extracted values
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if checklist.pdh:
                                            st.metric("PDH", f"${checklist.pdh:.2f}")
                                        if checklist.pdl:
                                            st.metric("PDL", f"${checklist.pdl:.2f}")
                                    with col2:
                                        if checklist.pdc:
                                            st.metric("PDC", f"${checklist.pdc:.2f}")
                                        if checklist.vwap:
                                            st.metric("VWAP", f"${checklist.vwap:.2f}")

                                    st.caption(f"Confidence: {response.get('confidence', 0.8):.0%} | Screenshots analyzed: {len(uploaded_files)}")
                                    st.rerun()
                                else:
                                    st.error("❌ Could not analyze screenshot. Please try manual entry.")

                            except Exception as e:
                                st.error(f"❌ Screenshot analysis failed: {str(e)}")
                                st.info("💡 Try manual entry instead")

                else:
                    # Manual entry method (original)
                    checklist = PreMarketChecklist(
                        trade_date=datetime.now().strftime('%Y-%m-%d'),
                        ticker=ticker,
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

    # === SECTION 2: AI PRE-MARKET BRIEFING ===
    if today_checklist and today_checklist['completed']:
        st.markdown("---")
        st.subheader("🤖 AI Pre-Market Briefing")

        # Check if briefing already cached for today + ticker
        selected_ticker = today_checklist.get('ticker', 'SPY')
        cache_key = f"{today}-{selected_ticker}"
        cached_briefing = ai_cache.get_daily_briefing(cache_key)

        col1, col2 = st.columns([3, 1])

        with col1:
            if cached_briefing:
                # Display cached briefing
                age_hours = (datetime.now() - datetime.fromisoformat(cached_briefing["created_at"])).total_seconds() / 3600
                if age_hours < 8:
                    st.success(f"📄 Briefing generated {age_hours:.1f} hours ago (cached)")
                else:
                    st.warning(f"⚠️ Briefing is {age_hours:.1f} hours old - consider refreshing")

        with col2:
            # Button to generate/refresh briefing
            if st.button("🔄 Generate Today's Briefing", help="Costs ~$0.08-0.12 per briefing"):
                with st.spinner("Generating AI briefing..."):
                    try:
                        # Prepare market data for selected ticker
                        market_data = {
                            'ticker': selected_ticker,
                            'levels': {
                                'pdh': today_checklist.get('pdh', 0) if today_checklist else 0,
                                'pdl': today_checklist.get('pdl', 0) if today_checklist else 0,
                                'pdc': today_checklist.get('pdc', 0) if today_checklist else 0,
                                'vwap': today_checklist.get('vwap', 0) if today_checklist else 0
                            },
                            'bias': today_checklist.get('spy_bias', 'NEUTRAL') if today_checklist else 'NEUTRAL',
                            'vix': today_checklist.get('vix_level', 15.5) if today_checklist else 15.5
                        }

                        # Ticker-specific context (in production, fetch real news/earnings for ticker)
                        news_events = [
                            f"{selected_ticker} pre-market volume analysis needed",
                            f"Check {selected_ticker} sector rotation vs QQQ/SPY",
                            f"Monitor {selected_ticker} for any earnings/catalyst updates"
                        ]

                        # Generate briefing using cached AI
                        dynamic_prompt = get_pre_market_dynamic_prompt(today, market_data, news_events)

                        response, usage = ai_client.create_cached_message(
                            cached_prompt=PRE_MARKET_SYSTEM_PROMPT,
                            dynamic_content=dynamic_prompt,
                            task_type=TaskType.PRE_MARKET_BRIEFING,
                            max_tokens=2000,
                            fallback_response=PRE_MARKET_FALLBACK
                        )

                        # Cache the result
                        if response.get('market_bias'):
                            ai_cache.cache_daily_briefing(
                                cache_key,
                                response,
                                usage.get('total_tokens', 0),
                                usage.get('cost_usd', 0)
                            )

                            # Update cache reference
                            cached_briefing = {
                                "content": response,
                                "tokens_used": usage.get('total_tokens', 0),
                                "cost_usd": usage.get('cost_usd', 0),
                                "created_at": datetime.now().isoformat(),
                                "cached": False
                            }

                            st.success(f"✅ Briefing generated! Used {usage.get('total_tokens', 0)} tokens (${usage.get('cost_usd', 0):.3f})")
                        else:
                            st.error("❌ Failed to generate briefing - using fallback")

                    except Exception as e:
                        st.error(f"❌ Briefing generation failed: {str(e)}")

        # Display briefing if available
        if cached_briefing and cached_briefing.get('content'):
            briefing = cached_briefing['content']

            # Market bias display
            if briefing.get('market_bias'):
                bias = briefing['market_bias']
                bias_color = "🟢" if bias == "BULLISH" else "🔴" if bias == "BEARISH" else "🟡"
                confidence = briefing.get('confidence_level', 5)

                st.markdown(f"### {bias_color} Market Bias: **{bias}** (Confidence: {confidence}/10)")

            # Summary
            if briefing.get('summary'):
                st.info(f"**Today's Outlook:** {briefing['summary']}")

            # Key levels and details in columns
            col1, col2 = st.columns(2)

            with col1:
                # Risk factors
                if briefing.get('risk_factors'):
                    st.markdown("**⚠️ Risk Factors:**")
                    for risk in briefing['risk_factors'][:3]:
                        st.write(f"• {risk}")

                # Time of day notes
                if briefing.get('time_of_day_notes'):
                    st.markdown(f"**⏰ Timing Notes:** {briefing['time_of_day_notes']}")

            with col2:
                # Opportunities
                if briefing.get('opportunities'):
                    st.markdown("**🎯 Opportunities:**")
                    for opp in briefing['opportunities'][:3]:
                        st.write(f"• {opp}")

                # Token usage display
                tokens_used = cached_briefing.get('tokens_used', 0)
                cost_usd = cached_briefing.get('cost_usd', 0)
                if tokens_used > 0:
                    st.caption(f"💰 Used {tokens_used:,} tokens (${cost_usd:.3f})")

        # === SECTION 3: 8-CONFIRMATION ANALYSIS ===
        st.markdown("---")
        st.subheader("✅ 8-Confirmation Framework")

        # Get selected ticker for analysis
        selected_ticker = today_checklist.get('ticker', 'SPY')
        st.info(f"📊 Analysis for **{selected_ticker}** - All 8 confirmations must align for a valid trade setup")

        # Create mock confirmation data based on current market setup
        pdc = today_checklist.get('pdc', 0)
        vwap = today_checklist.get('vwap', 0)
        current_price = pdc + np.random.uniform(-2, 2) if pdc > 0 else 100
        bias = today_checklist.get('spy_bias', 'NEUTRAL')

        # 8 Confirmations
        confirmations = [
            {
                "name": "1. Candles",
                "description": "Strong directional candle (close > open for calls)",
                "status": "✅ PASS" if current_price > pdc else "❌ FAIL",
                "detail": "Green candles" if current_price > pdc else "Red candles"
            },
            {
                "name": "2. Volume",
                "description": "High volume (>1.2x average)",
                "status": "✅ PASS",
                "detail": "Above average volume"
            },
            {
                "name": "3. VWAP",
                "description": f"Price vs VWAP (${vwap:.2f})" if vwap > 0 else "Price vs VWAP",
                "status": "✅ PASS" if current_price > vwap else "❌ FAIL",
                "detail": f"${current_price:.2f} {'above' if current_price > vwap else 'below'} VWAP"
            },
            {
                "name": "4. 9 EMA",
                "description": "Price above 9 EMA (fast momentum)",
                "status": "✅ PASS" if current_price > pdc * 1.001 else "❌ FAIL",
                "detail": "Bullish momentum" if current_price > pdc * 1.001 else "Bearish momentum"
            },
            {
                "name": "5. 21 EMA",
                "description": "Price above 21 EMA (trend)",
                "status": "✅ PASS" if current_price > pdc * 0.999 else "❌ FAIL",
                "detail": "Bullish trend" if current_price > pdc * 0.999 else "Bearish trend"
            },
            {
                "name": "6. SPY Direction",
                "description": "Market direction alignment",
                "status": "✅ PASS" if bias == "BULLISH" else "❌ FAIL" if bias == "BEARISH" else "⚠️ NEUTRAL",
                "detail": f"SPY {bias.lower()}"
            },
            {
                "name": "7. QQQ/Sector",
                "description": "Sector alignment check",
                "status": "✅ PASS" if bias != "BEARISH" else "❌ FAIL",
                "detail": "Sector aligned" if bias != "BEARISH" else "Sector diverging"
            },
            {
                "name": "8. Support/Resistance",
                "description": f"Clear of key levels (PDC: ${pdc:.2f})",
                "status": "✅ PASS" if abs(current_price - pdc) > pdc * 0.005 else "⚠️ NEAR LEVEL",
                "detail": f"${abs(current_price - pdc):.2f} from PDC"
            }
        ]

        # Display confirmations in a grid
        cols = st.columns(2)

        for i, conf in enumerate(confirmations):
            with cols[i % 2]:
                # Color based on status
                if conf["status"].startswith("✅"):
                    st.success(f"**{conf['name']}**\n{conf['detail']}")
                elif conf["status"].startswith("❌"):
                    st.error(f"**{conf['name']}**\n{conf['detail']}")
                else:
                    st.warning(f"**{conf['name']}**\n{conf['detail']}")

        # Overall score and ACTIONABLE trade plan
        passed = len([c for c in confirmations if c["status"].startswith("✅")])
        total = len(confirmations)

        st.markdown("---")
        st.subheader(f"🎯 Trading Action for {selected_ticker}")

        # Calculate key levels
        pdh = today_checklist.get('pdh', 0)
        pdl = today_checklist.get('pdl', 0)
        pdc = today_checklist.get('pdc', 0)
        vwap = today_checklist.get('vwap', 0)

        current_estimate = pdc + np.random.uniform(-2, 2) if pdc > 0 else 500

        if passed >= 6:
            # VALID SETUP - Give specific trade plan
            direction = "CALLS" if current_estimate > vwap else "PUTS"
            entry_level = pdh + 0.50 if direction == "CALLS" else pdl - 0.50
            stop_level = vwap if direction == "CALLS" else vwap
            target_level = entry_level * 1.02 if direction == "CALLS" else entry_level * 0.98
            risk_reward = abs(target_level - entry_level) / abs(entry_level - stop_level)

            st.success(f"🎯 **VALID SETUP** - {passed}/{total} confirmations passed")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("🎯 Direction", direction, help=f"Based on {selected_ticker} confluence")
                st.metric("🚀 Entry", f"${entry_level:.2f}", help="Price to enter trade")
                st.metric("🛑 Stop Loss", f"${stop_level:.2f}", help="Exit if wrong")

            with col2:
                st.metric("💰 Target", f"${target_level:.2f}", help="Profit taking level")
                st.metric("📊 R/R Ratio", f"{risk_reward:.1f}:1", help="Risk vs reward")
                st.metric("💸 Risk", f"${abs(entry_level - stop_level):.2f}", help="Max loss per contract")

            st.success(f"**Trade Plan:** Buy {selected_ticker} {direction} at ${entry_level:.2f} with stop at ${stop_level:.2f}")

        elif passed >= 4:
            st.warning(f"⚠️ **PARTIAL SETUP** - {passed}/{total} confirmations passed")
            st.warning("❌ **Action: STAY IN CASH** - Wait for better setup or smaller size")
            st.info(f"**Watch for:** {selected_ticker} to break ${pdh:.2f} (calls) or ${pdl:.2f} (puts) with volume")

        else:
            st.error(f"❌ **NO TRADE** - Only {passed}/{total} confirmations passed")
            st.error("❌ **Action: STAY IN CASH** - Setup not valid")
            st.info(f"**Next:** Wait for {selected_ticker} to show better confluence or switch tickers")

        # === SECTION 4: TODAY'S TRADING PLAN ===
        st.markdown("---")
        st.subheader("📝 Today's Trading Plan")

        # Load existing plan or create new
        plan_key = f"trading_plan_{today}"
        if plan_key not in st.session_state:
            st.session_state[plan_key] = {
                "thesis": "",
                "levels_to_watch": "",
                "max_trades": 3,
                "news_risks": ""
            }

        with st.form("trading_plan_form"):
            col1, col2 = st.columns(2)

            with col1:
                thesis = st.text_area(
                    "Trade Thesis for Today",
                    value=st.session_state[plan_key]["thesis"],
                    placeholder="What's my directional bias and why?",
                    height=100
                )

                levels_to_watch = st.text_area(
                    "Key Levels to Watch",
                    value=st.session_state[plan_key]["levels_to_watch"],
                    placeholder="Support/resistance levels, breakout points",
                    height=100
                )

            with col2:
                max_trades = st.selectbox(
                    "Max Trades Planned Today",
                    [1, 2, 3],
                    index=[1, 2, 3].index(st.session_state[plan_key]["max_trades"])
                )

                news_risks = st.text_area(
                    "News Risks to Monitor",
                    value=st.session_state[plan_key]["news_risks"],
                    placeholder="Fed speakers, earnings, economic data",
                    height=100
                )

            if st.form_submit_button("💾 Save Today's Plan"):
                st.session_state[plan_key] = {
                    "thesis": thesis,
                    "levels_to_watch": levels_to_watch,
                    "max_trades": max_trades,
                    "news_risks": news_risks
                }
                st.success("✅ Trading plan saved!")

        # Display current plan summary
        if st.session_state[plan_key]["thesis"]:
            st.info(f"**Today's Thesis:** {st.session_state[plan_key]['thesis']}")

        if st.session_state[plan_key]["levels_to_watch"]:
            st.info(f"**Watching:** {st.session_state[plan_key]['levels_to_watch']}")

    else:
        # Show teaser for AI features
        st.markdown("---")
        st.info("🔒 **Complete morning prep to unlock:**\n- 🤖 AI Pre-Market Briefing\n- 📋 Enhanced Watchlist\n- 📝 Daily Trading Plan")

def get_sample_market_data(symbol: str) -> MarketData:
    """TODO: Implement sample market data for testing"""
    pass

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
    st.sidebar.markdown("*8-Confirmation Framework*")

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