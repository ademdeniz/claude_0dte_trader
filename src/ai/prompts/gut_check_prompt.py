"""
Gut Check Prompt

Quick psychological assessment before trade entry.
Small prompt optimized for fast execution and low token cost.
"""

# This prompt will be cached with cache_control: ephemeral
GUT_CHECK_SYSTEM_PROMPT = """You are a trading psychology expert providing quick gut checks before 0DTE options trades.

# YOUR ROLE
Provide binary PROCEED/STAND_DOWN recommendations based on trader psychological state and setup quality.

# DECISION FRAMEWORK

## PROCEED Conditions (All must be true)
- Setup has 7/8 or 8/8 confirmations
- Emotional state is CALM or DISCIPLINED
- Focus level is 7+ out of 10
- No revenge trading pattern (prior loss doesn't trigger FOMO)
- Conviction level is 7+ out of 10
- Adequate sleep (6+ hours)

## STAND_DOWN Conditions (Any triggers stand down)
- Setup has <7/8 confirmations
- Emotional state is ANXIOUS, EXCITED, FRUSTRATED, or FOMO
- Focus level is <7 out of 10
- Revenge trading pattern detected
- Conviction level is <7 out of 10
- Sleep deprivation (<6 hours)
- Already took 2+ trades today without clear edge

# OUTPUT FORMAT
Return JSON with this structure:
```json
{
    "verdict": "PROCEED" or "STAND_DOWN",
    "confidence": 1-10,
    "reasoning": "Brief 2-sentence explanation",
    "risk_factors": ["factor1", "factor2"],
    "trader_state_assessment": "Brief psychological read"
}
```

# ANALYSIS PRINCIPLES
- Binary decision: PROCEED or STAND_DOWN only
- Conservative bias: when in doubt, stand down
- Focus on psychological state over setup quality
- Consider cumulative fatigue and emotional state
- Quick assessment, not detailed analysis

# CRITICAL RULES
- Never encourage risky trades
- Always err on the side of caution
- Consider trader's recent performance pattern
- Acknowledge when information is insufficient
"""

def get_gut_check_dynamic_prompt(
    setup_data: dict,
    trader_state: dict,
    recent_trades: list = None
) -> str:
    """
    Generate the dynamic portion of the gut check prompt

    Args:
        setup_data: Current trade setup information
        trader_state: Trader's current psychological state
        recent_trades: Recent trading history for context

    Returns:
        Dynamic prompt content (not cached)
    """

    prompt_parts = ["Perform gut check for this trade:"]

    # Setup information
    if setup_data:
        prompt_parts.append(f"\nSETUP:")
        prompt_parts.append(f"Symbol: {setup_data.get('symbol', 'N/A')}")
        prompt_parts.append(f"Direction: {setup_data.get('direction', 'N/A')}")
        prompt_parts.append(f"Confirmation Score: {setup_data.get('confirmation_score', 0)}/8")

        if 'failed_confirmations' in setup_data:
            prompt_parts.append(f"Failed Confirmations: {', '.join(setup_data['failed_confirmations'])}")

    # Trader state
    if trader_state:
        prompt_parts.append(f"\nTRADER STATE:")
        prompt_parts.append(f"Emotional State: {trader_state.get('emotional_state', 'UNKNOWN')}")
        prompt_parts.append(f"Focus Level: {trader_state.get('focus_level', 5)}/10")
        prompt_parts.append(f"Sleep Hours: {trader_state.get('sleep_hours', 'N/A')}")
        prompt_parts.append(f"Trade Conviction: {trader_state.get('conviction', 5)}/10")
        prompt_parts.append(f"Trades Today: {trader_state.get('trades_today', 0)}")

    # Recent context
    if recent_trades:
        prompt_parts.append(f"\nRECENT CONTEXT:")
        last_trade = recent_trades[0] if recent_trades else None
        if last_trade:
            outcome = "WIN" if last_trade.get('profit_loss_pct', 0) > 0 else "LOSS"
            prompt_parts.append(f"Last Trade: {outcome} ({last_trade.get('profit_loss_pct', 0):+.1f}%)")

        if len(recent_trades) >= 2:
            last_two = recent_trades[:2]
            outcomes = [("WIN" if t.get('profit_loss_pct', 0) > 0 else "LOSS") for t in last_two]
            if outcomes == ["LOSS", "LOSS"]:
                prompt_parts.append("Pattern: Two losses in a row - high revenge risk")

    prompt_parts.append("\nProvide PROCEED/STAND_DOWN decision with reasoning.")

    return "\n".join(prompt_parts)

# Fallback response if API fails
GUT_CHECK_FALLBACK = {
    "verdict": "STAND_DOWN",
    "confidence": 5,
    "reasoning": "Gut check analysis unavailable. Standing down as safety measure.",
    "risk_factors": ["AI analysis unavailable"],
    "trader_state_assessment": "Unable to assess psychological state"
}