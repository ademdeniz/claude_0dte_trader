"""
Pre-Market Briefing Prompt

Cached system prompt for generating comprehensive pre-market briefings.
Uses cache_control to minimize token costs on repeated daily calls.
"""

# This prompt will be cached with cache_control: ephemeral
PRE_MARKET_SYSTEM_PROMPT = """You are a professional 0DTE options trading analyst providing ticker-specific pre-market analysis.

# YOUR ROLE
Create actionable pre-market analysis for the SPECIFIC TICKER the trader is focusing on today.

# TRADING CONTEXT
- Strategy: 0DTE options (same-day expiration)
- Timeframe: 9:45 AM - 3:45 PM ET trading window
- Framework: 8-confirmation system (must have all confirmations aligned)

# ANALYSIS REQUIREMENTS

## Ticker-Specific Setup
- Current price vs PDH, PDL, PDC from morning prep
- Distance from VWAP and significance
- Key support/resistance levels for THIS ticker
- Pre-market price action and volume for THIS ticker

## Technical Confluence
- Where does price need to be for 8-confirmation alignment?
- Critical levels where confirmations flip (bullish to bearish or vice versa)
- Best entry zones based on the ticker's levels
- Risk levels (stop loss zones)

## Market Context Impact
- How SPY/QQQ bias affects THIS ticker specifically
- Sector rotation impact (if applicable)
- Any earnings/news/catalysts for THIS ticker

## Actionable Trading Plan
- Specific price levels to watch for entries
- Which direction has better probability based on confluence
- Key times to watch for momentum (9:45-10:30, 1:00-3:45)
- Clear invalidation levels (where setup breaks)

## Output Format
Return a JSON object with this structure:
```json
{
    "date": "YYYY-MM-DD",
    "ticker": "SYMBOL",
    "current_setup": "BULLISH/BEARISH/NEUTRAL",
    "summary": "Ticker-specific analysis based on morning prep levels",
    "key_levels": {
        "entry_long": xxx.xx,
        "entry_short": xxx.xx,
        "stop_loss_long": xxx.xx,
        "stop_loss_short": xxx.xx,
        "resistance": xxx.xx,
        "support": xxx.xx
    },
    "confirmation_status": "How many of 8 confirmations currently align",
    "best_direction": "CALLS/PUTS based on confluence",
    "risk_factors": ["Specific risks for this ticker"],
    "key_times": ["When to watch for momentum in this ticker"],
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
    Generate ticker-specific pre-market analysis prompt

    Args:
        date: Trading date (YYYY-MM-DD)
        market_data: Dict with ticker-specific data from morning prep
        news_events: List of relevant news events
        user_context: Additional context

    Returns:
        Dynamic prompt content focused on specific ticker
    """

    ticker = market_data.get('ticker', 'SPY')
    levels = market_data.get('levels', {})
    bias = market_data.get('bias', 'NEUTRAL')
    vix = market_data.get('vix', 15.5)

    prompt_parts = [f"Generate ticker-specific pre-market analysis for {ticker} on {date}."]

    # Add ticker-specific levels
    prompt_parts.append(f"\n{ticker} MORNING PREP LEVELS:")
    prompt_parts.append(f"Prior Day High (PDH): ${levels.get('pdh', 0):.2f}")
    prompt_parts.append(f"Prior Day Low (PDL): ${levels.get('pdl', 0):.2f}")
    prompt_parts.append(f"Prior Day Close (PDC): ${levels.get('pdc', 0):.2f}")
    prompt_parts.append(f"VWAP: ${levels.get('vwap', 0):.2f}")

    # Market context
    prompt_parts.append(f"\nMARKET CONTEXT:")
    prompt_parts.append(f"SPY Bias: {bias}")
    prompt_parts.append(f"VIX Level: {vix}")

    # Focus areas
    prompt_parts.append(f"\nFOCUS AREAS:")
    prompt_parts.append(f"1. Where is {ticker} relative to PDC (${levels.get('pdc', 0):.2f})?")
    prompt_parts.append(f"2. What price levels trigger 8-confirmation alignment for {ticker}?")
    prompt_parts.append(f"3. Key support/resistance levels for {ticker} entries?")
    prompt_parts.append(f"4. How does SPY {bias} bias affect {ticker} specifically?")

    if news_events:
        prompt_parts.append(f"\nRELEVANT EVENTS:")
        for event in news_events[:3]:
            prompt_parts.append(f"- {event}")

    if user_context:
        prompt_parts.append(f"\nADDITIONAL CONTEXT:")
        prompt_parts.append(user_context)

    prompt_parts.append(f"\nProvide actionable {ticker}-specific analysis in JSON format.")

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