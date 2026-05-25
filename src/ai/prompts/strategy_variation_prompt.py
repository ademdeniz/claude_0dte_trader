"""
Strategy Variation Analysis Prompt

Mathematical analysis of strategy modifications and their expected impact.
Uses pre-computed statistics with AI interpretation for cost efficiency.
"""

# This prompt will be cached with cache_control: ephemeral
STRATEGY_VARIATION_SYSTEM_PROMPT = """You are a quantitative trading analyst specializing in strategy optimization and risk assessment.

# YOUR ROLE
Analyze proposed trading strategy variations using mathematical models and historical performance data.

# ANALYSIS FRAMEWORK

## Mathematical Modeling
- Expected value calculations based on historical win rates
- Risk-reward ratio analysis
- Break-even win rate calculations
- Stress testing under different market conditions
- Monte Carlo scenario analysis (when sample size sufficient)

## Risk Assessment
- Impact on maximum drawdown
- Effect on volatility of returns
- Tail risk considerations
- Capital efficiency changes

## Statistical Significance
- Sample size requirements for reliable testing
- Confidence intervals for performance metrics
- Statistical significance of observed differences
- Power analysis for test duration

# OUTPUT FORMAT
Return JSON with this structure:
```json
{
    "variation_name": "Descriptive name",
    "mathematical_analysis": {
        "current_expected_value": 0.XX,
        "proposed_expected_value": 0.XX,
        "improvement_pct": 0.XX,
        "break_even_win_rate": 0.XX,
        "required_win_rate": 0.XX
    },
    "risk_impact": {
        "max_drawdown_change": "INCREASE/DECREASE/NEUTRAL",
        "volatility_change": "INCREASE/DECREASE/NEUTRAL",
        "tail_risk": "HIGHER/LOWER/SAME"
    },
    "testing_plan": {
        "recommended_sample_size": 50,
        "testing_duration": "4-6 weeks",
        "success_criteria": "Win rate > XX% or EV > $XX",
        "failure_criteria": "Stop if losses exceed $XX"
    },
    "recommendation": "IMPLEMENT/TEST/REJECT",
    "reasoning": "Mathematical justification",
    "implementation_notes": ["Note 1", "Note 2"]
}
```

# ANALYSIS PRINCIPLES

## Mathematical Rigor
- Base all calculations on provided historical data
- Show expected value calculations explicitly
- Consider both mean and variance of outcomes
- Account for position sizing impact

## Conservative Estimates
- Use conservative assumptions for projections
- Consider worst-case scenarios
- Account for implementation slippage
- Factor in psychological difficulty of rule changes

## Practical Implementation
- Consider real-world execution challenges
- Account for market condition dependencies
- Assess psychological feasibility for the trader
- Plan proper testing methodology

# CRITICAL RULES
- Never recommend untested strategy changes for live trading
- Always suggest paper trading or small size testing first
- Acknowledge limitations of historical data
- Emphasize that past performance doesn't guarantee future results
- Focus on risk management in all recommendations
"""

def get_strategy_variation_dynamic_prompt(
    current_strategy: dict,
    proposed_variation: dict,
    historical_stats: dict,
    hypothesis: str = ""
) -> str:
    """
    Generate the dynamic portion of the strategy variation prompt

    Args:
        current_strategy: Current trading rules and parameters
        proposed_variation: Proposed changes to strategy
        historical_stats: Pre-computed historical performance data
        hypothesis: User's hypothesis for why variation might work

    Returns:
        Dynamic prompt content (not cached)
    """

    prompt_parts = ["Analyze this strategy variation:"]

    # Current strategy
    if current_strategy:
        prompt_parts.append(f"\nCURRENT STRATEGY:")
        for rule, value in current_strategy.items():
            prompt_parts.append(f"{rule}: {value}")

    # Proposed variation
    if proposed_variation:
        prompt_parts.append(f"\nPROPOSED VARIATION:")
        for rule, value in proposed_variation.items():
            prompt_parts.append(f"Change {rule} to: {value}")

    # Historical performance data (pre-computed in Python)
    if historical_stats:
        prompt_parts.append(f"\nHISTORICAL PERFORMANCE:")
        prompt_parts.append(f"Total Trades: {historical_stats.get('total_trades', 0)}")
        prompt_parts.append(f"Win Rate: {historical_stats.get('win_rate', 0):.1f}%")
        prompt_parts.append(f"Average Win: {historical_stats.get('avg_win', 0):.1f}%")
        prompt_parts.append(f"Average Loss: {historical_stats.get('avg_loss', 0):.1f}%")
        prompt_parts.append(f"Current Expected Value: ${historical_stats.get('expected_value', 0):.2f}")
        prompt_parts.append(f"Win/Loss Ratio: {historical_stats.get('win_loss_ratio', 0):.2f}")
        prompt_parts.append(f"Maximum Drawdown: {historical_stats.get('max_drawdown', 0):.1f}%")

        if 'monthly_returns' in historical_stats:
            prompt_parts.append(f"Monthly Returns Volatility: {historical_stats['monthly_volatility']:.1f}%")

    # User hypothesis
    if hypothesis:
        prompt_parts.append(f"\nUSER HYPOTHESIS:")
        prompt_parts.append(hypothesis)

    prompt_parts.append("\nProvide mathematical analysis and testing recommendation.")

    return "\n".join(prompt_parts)

# Fallback response if API fails
STRATEGY_VARIATION_FALLBACK = {
    "variation_name": "Analysis Unavailable",
    "mathematical_analysis": {
        "current_expected_value": 0,
        "proposed_expected_value": 0,
        "improvement_pct": 0,
        "break_even_win_rate": 0.50,
        "required_win_rate": 0.55
    },
    "risk_impact": {
        "max_drawdown_change": "UNKNOWN",
        "volatility_change": "UNKNOWN",
        "tail_risk": "UNKNOWN"
    },
    "testing_plan": {
        "recommended_sample_size": 50,
        "testing_duration": "4-6 weeks",
        "success_criteria": "Manual evaluation required",
        "failure_criteria": "Manual evaluation required"
    },
    "recommendation": "TEST",
    "reasoning": "Analysis unavailable - manual evaluation recommended",
    "implementation_notes": ["Manual strategy analysis required"]
}