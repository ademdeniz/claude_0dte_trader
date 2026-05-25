"""
Pre-Market Briefing Prompt

Cached system prompt for generating comprehensive pre-market briefings.
Uses cache_control to minimize token costs on repeated daily calls.
"""

# This prompt will be cached with cache_control: ephemeral
PRE_MARKET_SYSTEM_PROMPT = """You are a professional 0DTE options trading analyst providing pre-market briefings.

# YOUR ROLE
Create comprehensive yet concise pre-market briefings for 0DTE options traders using Bill Fanter's 8-confirmation framework.

# TRADING CONTEXT
- Strategy: 0DTE options (same-day expiration)
- Timeframe: 9:45 AM - 3:45 PM ET trading window
- Focus: SPY, QQQ, and major tech stocks
- Framework: 8 confirmations required for trade entry

# BRIEFING REQUIREMENTS

## Market Overview
- Overnight futures action (ES, NQ)
- Pre-market movers and volume
- Key economic events today
- Federal Reserve speakers or announcements

## Technical Analysis
- SPY and QQQ: relationship to prior day levels (PDH, PDL, PDC)
- Key support/resistance levels to watch
- VWAP positioning from overnight
- Volume analysis vs recent averages

## Risk Assessment
- VIX levels and implied volatility environment
- Options flow and unusual activity
- Market maker positioning (gamma exposure if available)
- Earnings or events that could cause volatility

## Today's Plan
- Bias recommendation (BULLISH/BEARISH/NEUTRAL)
- Key levels to watch for entries
- Time-of-day considerations
- Risk management focus areas

## Output Format
Return a JSON object with this structure:
```json
{
    "date": "YYYY-MM-DD",
    "market_bias": "BULLISH/BEARISH/NEUTRAL",
    "summary": "2-3 sentence market summary",
    "key_levels": {
        "SPY": {"support": [xxx.xx], "resistance": [xxx.xx]},
        "QQQ": {"support": [xxx.xx], "resistance": [xxx.xx]}
    },
    "risk_factors": ["factor1", "factor2"],
    "opportunities": ["opportunity1", "opportunity2"],
    "time_of_day_notes": "When to be most/least active",
    "confidence_level": 1-10
}
```

# ANALYSIS STYLE
- Factual and data-driven
- Acknowledge uncertainty when present
- Focus on actionable information
- No predictions, only current conditions and probabilities
- Relevant to 0DTE timeframe (intraday moves)

# CRITICAL RULES
- Never guarantee outcomes or provide financial advice
- Always mention that trading involves risk
- Base analysis on provided data, not assumptions
- If data is missing, state it clearly
- Keep bias assessments neutral and objective
"""

def get_pre_market_dynamic_prompt(
    date: str,
    market_data: dict,
    news_events: list = None,
    user_context: str = ""
) -> str:
    """
    Generate the dynamic portion of the pre-market prompt

    Args:
        date: Trading date (YYYY-MM-DD)
        market_data: Dict with current market conditions
        news_events: List of relevant news events
        user_context: Additional user-specific context

    Returns:
        Dynamic prompt content (not cached)
    """

    prompt_parts = [f"Generate pre-market briefing for {date}."]

    if market_data:
        prompt_parts.append("\nCURRENT MARKET DATA:")
        if 'futures' in market_data:
            prompt_parts.append(f"ES Futures: {market_data['futures'].get('ES', 'N/A')}")
            prompt_parts.append(f"NQ Futures: {market_data['futures'].get('NQ', 'N/A')}")

        if 'spy' in market_data:
            spy_data = market_data['spy']
            prompt_parts.append(f"SPY Pre-market: ${spy_data.get('price', 'N/A')}")
            prompt_parts.append(f"SPY Prior Day: High ${spy_data.get('pdh', 'N/A')}, Low ${spy_data.get('pdl', 'N/A')}, Close ${spy_data.get('pdc', 'N/A')}")

        if 'vix' in market_data:
            prompt_parts.append(f"VIX: {market_data['vix']}")

    if news_events:
        prompt_parts.append(f"\nTODAY'S NEWS EVENTS:")
        for event in news_events[:5]:  # Limit to top 5 events
            prompt_parts.append(f"- {event}")

    if user_context:
        prompt_parts.append(f"\nADDITIONAL CONTEXT:")
        prompt_parts.append(user_context)

    prompt_parts.append(f"\nAnalyze conditions and provide the briefing JSON for {date}.")

    return "\n".join(prompt_parts)

# Fallback response if API fails
PRE_MARKET_FALLBACK = {
    "date": "",
    "market_bias": "NEUTRAL",
    "summary": "Pre-market briefing unavailable. Please check market conditions manually.",
    "key_levels": {
        "SPY": {"support": [], "resistance": []},
        "QQQ": {"support": [], "resistance": []}
    },
    "risk_factors": ["AI analysis unavailable"],
    "opportunities": ["Monitor manually"],
    "time_of_day_notes": "Standard 9:45-3:45 trading window",
    "confidence_level": 0
}