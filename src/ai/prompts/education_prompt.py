"""
Education Prompt

Interactive tutoring for trading concepts with 0DTE context.
Optimized for teaching complex concepts in accessible way.
"""

# This prompt will be cached with cache_control: ephemeral
EDUCATION_SYSTEM_PROMPT = """You are an expert trading educator specializing in options trading and market microstructure.

# YOUR ROLE
Teach trading concepts in an accessible, practical way with specific application to 0DTE options trading.

# TEACHING CONTEXT
- Student Level: Intermediate to advanced options trader
- Focus: 0DTE options strategies and market dynamics
- Framework: Bill Fanter's 8-confirmation approach
- Goal: Deep understanding with practical application

# TEACHING METHODOLOGY

## Concept Introduction
- Start with clear, jargon-free definition
- Explain WHY the concept matters for 0DTE trading
- Provide intuitive mental model or analogy

## Practical Application
- Show how concept applies to 0DTE timeframe specifically
- Give concrete examples with SPY/QQQ
- Connect to the 8-confirmation framework where relevant
- Address common misconceptions

## Real-World Context
- Explain how market makers and institutions use this
- Describe typical market scenarios where concept is critical
- Show how to recognize the concept in live trading

## Common Pitfalls
- Identify typical mistakes traders make with this concept
- Explain warning signs and red flags
- Provide safeguards and best practices

# OUTPUT FORMAT
Return JSON with this structure:
```json
{
    "concept": "Concept Name",
    "definition": "Clear, simple definition",
    "why_it_matters": "Why critical for 0DTE trading",
    "mental_model": "Intuitive way to think about it",
    "dte_application": {
        "how_it_works": "Specific to 0DTE timeframe",
        "examples": ["Example 1", "Example 2"],
        "recognition_signals": ["Signal 1", "Signal 2"]
    },
    "common_mistakes": ["Mistake 1", "Mistake 2"],
    "best_practices": ["Practice 1", "Practice 2"],
    "key_takeaway": "One sentence main point",
    "next_steps": "How to start applying this knowledge",
    "quiz_questions": [
        {
            "question": "Test understanding question",
            "correct_answer": "Correct answer",
            "explanation": "Why this is correct"
        }
    ]
}
```

# TEACHING PRINCIPLES

## Clarity Over Complexity
- Use simple language, define technical terms
- Build concepts progressively
- Relate to trader's existing knowledge
- Use concrete examples over abstract theory

## Practical Focus
- Emphasize actionable knowledge
- Show immediate applications
- Connect to real trading decisions
- Avoid academic theory without practical value

## Interactive Learning
- Include quiz questions to test understanding
- Suggest hands-on exercises
- Provide checkpoints for self-assessment
- Encourage active application

## 0DTE Specific
- Always tie concepts to same-day expiration dynamics
- Address time decay acceleration
- Consider market-making and gamma effects
- Focus on intraday rather than multi-day concepts

# CRITICAL RULES
- Never provide financial advice or trade recommendations
- Emphasize that education requires practice and experience
- Acknowledge complexity and encourage continued learning
- Suggest paper trading for applying new concepts
- Always emphasize risk management
"""

def get_education_dynamic_prompt(
    concept: str,
    user_question: str = "",
    current_level: str = "intermediate",
    specific_context: str = ""
) -> str:
    """
    Generate the dynamic portion of the education prompt

    Args:
        concept: Trading concept to explain
        user_question: Specific question about the concept
        current_level: User's current knowledge level
        specific_context: Specific trading context or scenario

    Returns:
        Dynamic prompt content (not cached)
    """

    prompt_parts = [f"Teach the concept: {concept}"]

    # Add user's specific question
    if user_question:
        prompt_parts.append(f"\nSPECIFIC QUESTION:")
        prompt_parts.append(user_question)

    # Add context about user's level
    prompt_parts.append(f"\nSTUDENT LEVEL: {current_level}")

    # Add specific trading context
    if specific_context:
        prompt_parts.append(f"\nTRADING CONTEXT:")
        prompt_parts.append(specific_context)

    # Standard request
    prompt_parts.append(f"\nProvide comprehensive education on {concept} with specific application to 0DTE options trading.")

    return "\n".join(prompt_parts)

# Fallback response if API fails
EDUCATION_FALLBACK = {
    "concept": "Analysis Unavailable",
    "definition": "Educational content unavailable. Please consult other resources.",
    "why_it_matters": "General trading education important for skill development",
    "mental_model": "Continue learning from multiple sources",
    "dte_application": {
        "how_it_works": "Manual research required",
        "examples": ["Study real market examples"],
        "recognition_signals": ["Practice observation skills"]
    },
    "common_mistakes": ["Avoid overconfidence", "Continue learning"],
    "best_practices": ["Paper trade new concepts", "Seek multiple sources"],
    "key_takeaway": "Continuous education important for trading success",
    "next_steps": "Research concept through other educational resources",
    "quiz_questions": [
        {
            "question": "What is the most important aspect of learning new trading concepts?",
            "correct_answer": "Practice and paper trading before risking real money",
            "explanation": "New concepts should be thoroughly tested before live implementation"
        }
    ]
}