"""
Journal Analysis Prompt

Cached system prompt for analyzing trading patterns and performance.
Uses cache_control to minimize token costs for weekly/monthly analysis.
"""

# This prompt will be cached with cache_control: ephemeral
JOURNAL_ANALYSIS_SYSTEM_PROMPT = """You are an expert trading performance analyst specializing in options trading psychology and pattern recognition.

# YOUR ROLE
Analyze trading journal data to identify patterns, strengths, weaknesses, and provide actionable insights for improvement.

# TRADING CONTEXT
- Strategy: 0DTE options using Bill Fanter's 8-confirmation framework
- Trader Level: Intermediate to advanced
- Focus: Pattern recognition, emotional discipline, setup quality
- Goal: Continuous improvement through data-driven insights

# ANALYSIS FRAMEWORK

## Performance Metrics (You'll receive pre-computed)
- Win rate, average win/loss, expectancy
- Confirmation scores (which of 8 confirmations most often fail)
- Time-based patterns (best/worst times of day)
- Emotional state correlation with outcomes
- Setup strength vs actual results

## Pattern Recognition
- A+ setups: What makes the best trades
- Problem patterns: Repeated mistakes
- Behavioral patterns: Emotional triggers
- Time patterns: Performance by hour/day
- Confirmation patterns: Which rules are hardest to follow

## Psychological Analysis
- Relationship between emotional state and outcomes
- Discipline violations and their impact
- Overtrading vs undertrading patterns
- Risk management adherence

# OUTPUT REQUIREMENTS

Return analysis as JSON with this structure:
```json
{
    "analysis_period": "7d/30d/90d/all",
    "summary": {
        "overall_grade": "A/B/C/D/F",
        "key_strength": "Primary thing trader does well",
        "key_weakness": "Primary area for improvement",
        "trend_direction": "IMPROVING/DECLINING/STABLE"
    },
    "patterns": {
        "a_plus_setups": ["Pattern 1", "Pattern 2"],
        "problem_patterns": ["Problem 1", "Problem 2"],
        "time_patterns": "When trader performs best/worst",
        "emotional_patterns": "Emotional state correlations"
    },
    "recommendations": {
        "immediate_actions": ["Action 1", "Action 2"],
        "rules_to_focus": ["Rule 1", "Rule 2"],
        "habits_to_build": ["Habit 1", "Habit 2"],
        "habits_to_break": ["Bad habit 1", "Bad habit 2"]
    },
    "discipline_score": {
        "overall": 85,
        "breakdown": {
            "setup_quality": 90,
            "risk_management": 80,
            "emotional_control": 85,
            "rule_following": 85
        }
    },
    "next_steps": ["Specific action 1", "Specific action 2"]
}
```

# ANALYSIS PRINCIPLES

## Data-Driven Insights
- Base findings on actual trade data, not general advice
- Quantify patterns where possible
- Identify statistical significance in patterns
- Look for leading indicators of success/failure

## Psychological Awareness
- Recognize emotional trading patterns
- Identify triggers for discipline violations
- Suggest behavioral modifications based on data
- Address both confidence and fear patterns

## Actionable Recommendations
- Provide specific, measurable actions
- Prioritize highest-impact improvements
- Consider trader's current skill level
- Focus on 1-3 key areas for improvement

## Honest Assessment
- Don't sugarcoat problems
- Acknowledge what's working well
- Provide balanced perspective
- Use encouraging but realistic tone

# CRITICAL RULES
- Never provide financial advice or predictions
- Base analysis only on provided trade data
- Acknowledge limitations of sample size
- Suggest paper trading for testing new approaches
- Always emphasize risk management
"""

def get_journal_analysis_dynamic_prompt(
    time_period: str,
    trade_stats: dict,
    sample_trades: list,
    user_notes: str = ""
) -> str:
    """
    Generate the dynamic portion of the journal analysis prompt

    Args:
        time_period: Analysis period (7d, 30d, 90d, all)
        trade_stats: Pre-computed statistics
        sample_trades: List of representative trades
        user_notes: User's personal observations

    Returns:
        Dynamic prompt content (not cached)
    """

    prompt_parts = [f"Analyze trading performance for {time_period} period."]

    # Add pre-computed statistics
    if trade_stats:
        prompt_parts.append("\nPERFORMANCE STATISTICS:")
        prompt_parts.append(f"Total Trades: {trade_stats.get('total_trades', 0)}")
        prompt_parts.append(f"Win Rate: {trade_stats.get('win_rate', 0):.1f}%")
        prompt_parts.append(f"Average Win: {trade_stats.get('avg_win', 0):.1f}%")
        prompt_parts.append(f"Average Loss: {trade_stats.get('avg_loss', 0):.1f}%")
        prompt_parts.append(f"Expectancy: {trade_stats.get('expectancy', 0):.1f}%")
        prompt_parts.append(f"Max Consecutive Wins: {trade_stats.get('max_win_streak', 0)}")
        prompt_parts.append(f"Max Consecutive Losses: {trade_stats.get('max_loss_streak', 0)}")

        if 'confirmation_scores' in trade_stats:
            prompt_parts.append("\nCONFIRMATION ANALYSIS:")
            for conf, rate in trade_stats['confirmation_scores'].items():
                prompt_parts.append(f"{conf}: {rate:.1f}% pass rate")

        if 'emotional_breakdown' in trade_stats:
            prompt_parts.append("\nEMOTIONAL STATE BREAKDOWN:")
            for emotion, data in trade_stats['emotional_breakdown'].items():
                prompt_parts.append(f"{emotion}: {data['count']} trades, {data['win_rate']:.1f}% win rate")

    # Add sample trades for pattern recognition
    if sample_trades:
        prompt_parts.append(f"\nREPRESENTATIVE TRADES (showing {len(sample_trades)} of {trade_stats.get('total_trades', 0)}):")
        for i, trade in enumerate(sample_trades[:10], 1):  # Limit to 10 trades
            outcome = "WIN" if trade.get('profit_loss_pct', 0) > 0 else "LOSS"
            conf_score = sum([
                trade.get('candle_ok', 0), trade.get('volume_ok', 0), trade.get('vwap_ok', 0),
                trade.get('ema9_ok', 0), trade.get('ema21_ok', 0), trade.get('spy_ok', 0),
                trade.get('qqq_ok', 0), trade.get('support_resistance_ok', 0)
            ])
            prompt_parts.append(f"Trade {i}: {trade.get('ticker')} {trade.get('direction')} - {outcome} ({trade.get('profit_loss_pct', 0):+.1f}%) - {conf_score}/8 confirmations - {trade.get('emotional_state', 'UNKNOWN')}")

    # Add user observations
    if user_notes:
        prompt_parts.append(f"\nUSER OBSERVATIONS:")
        prompt_parts.append(user_notes)

    prompt_parts.append(f"\nProvide comprehensive analysis JSON for the {time_period} period.")

    return "\n".join(prompt_parts)

# Fallback response if API fails
JOURNAL_ANALYSIS_FALLBACK = {
    "analysis_period": "",
    "summary": {
        "overall_grade": "C",
        "key_strength": "Analysis unavailable",
        "key_weakness": "AI analysis unavailable",
        "trend_direction": "UNKNOWN"
    },
    "patterns": {
        "a_plus_setups": ["Analysis unavailable"],
        "problem_patterns": ["Analysis unavailable"],
        "time_patterns": "Analysis unavailable",
        "emotional_patterns": "Analysis unavailable"
    },
    "recommendations": {
        "immediate_actions": ["Manual review of recent trades"],
        "rules_to_focus": ["Continue following 8-confirmation framework"],
        "habits_to_build": ["Manual pattern tracking"],
        "habits_to_break": ["Monitor discipline manually"]
    },
    "discipline_score": {
        "overall": 75,
        "breakdown": {
            "setup_quality": 75,
            "risk_management": 75,
            "emotional_control": 75,
            "rule_following": 75
        }
    },
    "next_steps": ["Review trades manually", "Continue journaling"]
}