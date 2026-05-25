"""
Post-Trade Review Prompt

Quick trade execution analysis and lesson extraction.
Small prompt optimized for fast execution after trade completion.
"""

# This prompt will be cached with cache_control: ephemeral
POST_TRADE_REVIEW_SYSTEM_PROMPT = """You are a trading coach providing brief post-trade reviews for continuous improvement.

# YOUR ROLE
Analyze trade execution and extract one key lesson for tomorrow's trading.

# REVIEW FRAMEWORK

## Execution Grade (A-F)
- A: Perfect execution, followed all rules, good result
- B: Good execution, minor rule violations, acceptable result
- C: Average execution, some mistakes but manageable
- D: Poor execution, multiple rule violations, lucky if profitable
- F: Terrible execution, major rule violations, bad habits reinforced

## Key Factors
- Setup quality vs outcome
- Rule adherence (entry, exit, position sizing)
- Emotional state impact on decision making
- Stop loss and profit target execution
- Time of day and market conditions

# OUTPUT FORMAT
Return JSON with this structure:
```json
{
    "execution_grade": "A/B/C/D/F",
    "grade_reasoning": "Brief explanation of grade",
    "key_lesson": "One specific lesson for tomorrow",
    "tomorrow_adjustment": "One thing to do differently",
    "pattern_note": "Any behavioral pattern observed"
}
```

# ANALYSIS PRINCIPLES
- Focus on execution process, not just outcome
- Identify one specific improvement for next trade
- Consider emotional state and decision quality
- Look for patterns that help or hurt performance
- Keep feedback constructive and actionable

# CRITICAL RULES
- Be honest about poor execution
- Acknowledge good process even if result was poor
- Focus on what trader can control
- One lesson only - don't overwhelm with feedback
"""

def get_post_trade_review_dynamic_prompt(
    trade_data: dict,
    trader_reflection: dict
) -> str:
    """
    Generate the dynamic portion of the post-trade review prompt

    Args:
        trade_data: Trade execution data
        trader_reflection: Trader's self-assessment

    Returns:
        Dynamic prompt content (not cached)
    """

    prompt_parts = ["Review this completed trade:"]

    # Trade execution data
    if trade_data:
        prompt_parts.append(f"\nTRADE DATA:")
        prompt_parts.append(f"Symbol: {trade_data.get('symbol', 'N/A')} {trade_data.get('direction', 'N/A')}")
        prompt_parts.append(f"Entry: ${trade_data.get('entry_price', 0):.2f}")
        prompt_parts.append(f"Exit: ${trade_data.get('exit_price', 0):.2f}")
        prompt_parts.append(f"Result: {trade_data.get('profit_loss_pct', 0):+.1f}%")
        prompt_parts.append(f"Confirmation Score: {trade_data.get('confirmation_score', 0)}/8")
        prompt_parts.append(f"Emotional State: {trade_data.get('emotional_state', 'UNKNOWN')}")

        # Exit reason
        if 'exit_reason' in trade_data:
            prompt_parts.append(f"Exit Reason: {trade_data['exit_reason']}")

    # Trader's self-reflection
    if trader_reflection:
        prompt_parts.append(f"\nTRADER REFLECTION:")
        if trader_reflection.get('worked_as_expected'):
            prompt_parts.append(f"Worked as Expected: {trader_reflection['worked_as_expected']}")
        if trader_reflection.get('followed_rules'):
            prompt_parts.append(f"Followed Exit Rules: {trader_reflection['followed_rules']}")
        if trader_reflection.get('surprise_factor'):
            prompt_parts.append(f"What Surprised Me: {trader_reflection['surprise_factor']}")
        if trader_reflection.get('confidence_after'):
            prompt_parts.append(f"Confidence After: {trader_reflection['confidence_after']}/10")
        if trader_reflection.get('reflection'):
            prompt_parts.append(f"My Reflection: {trader_reflection['reflection']}")

    prompt_parts.append("\nProvide execution grade and one key lesson for tomorrow.")

    return "\n".join(prompt_parts)

# Fallback response if API fails
POST_TRADE_REVIEW_FALLBACK = {
    "execution_grade": "C",
    "grade_reasoning": "Unable to analyze - review manually",
    "key_lesson": "Continue following 8-confirmation framework",
    "tomorrow_adjustment": "Manual trade review",
    "pattern_note": "Analysis unavailable"
}