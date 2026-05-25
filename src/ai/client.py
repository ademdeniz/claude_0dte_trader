"""
Unified AI Client for 0DTE Trading System

Provides:
- Anthropic client initialization with error handling
- Model selection based on task complexity
- Prompt caching wrapper with cache_control markers
- Token tracking and cost estimation
- Retry logic and graceful fallbacks

All AI calls in the dashboard should go through this module.
"""

import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import anthropic

# Import our model selector
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.model_selector import get_optimal_model, ModelSelector

class TaskType(Enum):
    """Task types for model selection and cost estimation"""
    PRE_MARKET_BRIEFING = "pre-market-briefing"
    JOURNAL_ANALYSIS = "journal-analysis"
    GUT_CHECK = "gut-check"
    POST_TRADE_REVIEW = "post-trade-review"
    STRATEGY_VARIATION = "strategy-variation"
    EDUCATION = "education"
    DAILY_BIAS = "daily-bias"

class AIClient:
    """Unified AI client with caching and cost tracking"""

    # Token cost estimates (input tokens per $1 USD for different models)
    TOKEN_COSTS = {
        "claude-haiku-4-5-20251001": {"input": 250000, "output": 125000},  # $4/$8 per million
        "claude-sonnet-4-6": {"input": 30000, "output": 75000},            # $3/$15 per million
        "claude-opus-4-7": {"input": 15000, "output": 75000},              # $15/$75 per million
    }

    def __init__(self):
        """Initialize AI client"""
        self.client = None
        self.model_selector = ModelSelector()
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Anthropic client with error handling"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("⚠️ Warning: ANTHROPIC_API_KEY not set. AI features will use fallback mode.")
            return

        try:
            self.client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            print(f"❌ Failed to initialize Anthropic client: {e}")

    def get_optimal_model(self, task_type: TaskType) -> str:
        """Get optimal model for a specific task type"""
        task_mapping = {
            TaskType.PRE_MARKET_BRIEFING: "morning-prep",  # Use Haiku for data formatting
            TaskType.DAILY_BIAS: "morning-prep",           # Use Haiku for simple analysis
            TaskType.GUT_CHECK: "morning-prep",            # Use Haiku for quick checks
            TaskType.POST_TRADE_REVIEW: "trade-journal",   # Use Sonnet for judgment
            TaskType.JOURNAL_ANALYSIS: "trade-journal",    # Use Sonnet for complex analysis
            TaskType.STRATEGY_VARIATION: "trade-journal",  # Use Sonnet for math interpretation
            TaskType.EDUCATION: "generate-report",         # Use Sonnet for teaching
        }

        skill_name = task_mapping.get(task_type, "trade-journal")
        return get_optimal_model(skill_name)

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Estimate cost in USD for a given token usage"""
        if model not in self.TOKEN_COSTS:
            model = "claude-sonnet-4-6"  # Default fallback

        costs = self.TOKEN_COSTS[model]
        input_cost = input_tokens / costs["input"]
        output_cost = output_tokens / costs["output"]

        return input_cost + output_cost

    def create_cached_message(
        self,
        cached_prompt: str,
        dynamic_content: str,
        task_type: TaskType,
        max_tokens: int = 2000,
        temperature: float = 0.1,
        fallback_response: Optional[Dict] = None
    ) -> Tuple[Dict, Dict]:
        """
        Create message with prompt caching

        Args:
            cached_prompt: System prompt that will be cached
            dynamic_content: Dynamic content (not cached)
            task_type: Type of task for model selection
            max_tokens: Maximum response tokens
            temperature: Model temperature
            fallback_response: Response to return if API fails

        Returns:
            Tuple of (response_dict, usage_stats)
        """

        # Check if client is available
        if not self.client:
            if fallback_response:
                return fallback_response, {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0,
                    "model": "fallback",
                    "cached": False,
                    "error": "No API key - using fallback"
                }
            else:
                return {
                    "status": "error",
                    "message": "AI client not available. Please set ANTHROPIC_API_KEY."
                }, {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "model": "none", "cached": False}

        # Get optimal model for this task
        model = self.get_optimal_model(task_type)

        # Create messages with cache control
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cached_prompt,
                        "cache_control": {"type": "ephemeral"}  # Cache this stable content
                    },
                    {
                        "type": "text",
                        "text": dynamic_content
                        # No cache_control - this changes per request
                    }
                ]
            }
        ]

        # Make API call with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                start_time = time.time()

                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=messages,
                    temperature=temperature
                )

                response_time = time.time() - start_time

                # Extract usage statistics
                input_tokens = getattr(response.usage, 'input_tokens', 0)
                output_tokens = getattr(response.usage, 'output_tokens', 0)
                cost_usd = self.estimate_cost(input_tokens, output_tokens, model)

                usage_stats = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "cost_usd": cost_usd,
                    "model": model,
                    "response_time": response_time,
                    "cached": attempt == 0,  # First call populates cache
                    "attempt": attempt + 1,
                    "timestamp": datetime.now().isoformat()
                }

                # Parse response
                response_text = response.content[0].text.strip()

                # Try to parse as JSON if it looks like JSON
                try:
                    if response_text.startswith('{') and response_text.endswith('}'):
                        response_dict = json.loads(response_text)
                    elif response_text.startswith('```json'):
                        # Extract JSON from code block
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            response_dict = json.loads(response_text[json_start:json_end])
                        else:
                            response_dict = {"content": response_text, "format": "text"}
                    else:
                        response_dict = {"content": response_text, "format": "text"}
                except json.JSONDecodeError:
                    response_dict = {"content": response_text, "format": "text"}

                # Add metadata
                response_dict["_ai_metadata"] = {
                    "task_type": task_type.value,
                    "model": model,
                    "tokens_used": input_tokens + output_tokens,
                    "cost_usd": cost_usd,
                    "cached": attempt > 0  # Subsequent calls use cache
                }

                return response_dict, usage_stats

            except anthropic.APIError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⚠️ API error (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"   Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Final attempt failed
                    if fallback_response:
                        return fallback_response, {
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "cost_usd": 0.0,
                            "model": model,
                            "cached": False,
                            "error": f"API error after {max_retries} attempts: {str(e)}"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"API error after {max_retries} attempts: {str(e)}"
                        }, {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "model": model, "cached": False}

            except Exception as e:
                if fallback_response:
                    return fallback_response, {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cost_usd": 0.0,
                        "model": model,
                        "cached": False,
                        "error": f"Unexpected error: {str(e)}"
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Unexpected error: {str(e)}"
                    }, {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "model": model, "cached": False}

    def quick_analysis(
        self,
        prompt: str,
        task_type: TaskType,
        max_tokens: int = 1000,
        fallback: str = "Analysis unavailable"
    ) -> Tuple[str, Dict]:
        """
        Quick analysis for simple prompts (no caching)

        Args:
            prompt: Complete prompt text
            task_type: Type of task for model selection
            max_tokens: Maximum response tokens
            fallback: Fallback text if API fails

        Returns:
            Tuple of (response_text, usage_stats)
        """

        if not self.client:
            return fallback, {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "model": "fallback"}

        model = self.get_optimal_model(task_type)

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )

            input_tokens = getattr(response.usage, 'input_tokens', 0)
            output_tokens = getattr(response.usage, 'output_tokens', 0)
            cost_usd = self.estimate_cost(input_tokens, output_tokens, model)

            usage_stats = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": cost_usd,
                "model": model,
                "cached": False,
                "timestamp": datetime.now().isoformat()
            }

            return response.content[0].text.strip(), usage_stats

        except Exception as e:
            print(f"⚠️ Quick analysis failed: {e}")
            return fallback, {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "model": model, "error": str(e)}

# Global instance for easy access
ai_client = AIClient()

def get_ai_client() -> AIClient:
    """Get global AI client instance"""
    return ai_client