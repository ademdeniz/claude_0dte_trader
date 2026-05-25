"""
Model Selection Utility for Token Optimization

Intelligently selects the optimal Claude model based on task complexity:
- Haiku: Simple data processing, formatting, routine calculations
- Sonnet: Complex analysis, judgment calls, edge case handling
- Opus: Reserved for most complex reasoning (future use)

Phase 3 Model Mapping:
- morning-prep: Haiku (simple data formatting, 70% cost reduction)
- trade-journal: Sonnet (complex 8-confirmation analysis)
"""

from enum import Enum
from typing import Dict, Optional
import os

class ModelTier(Enum):
    """Available model tiers ordered by capability and cost"""
    HAIKU = "claude-haiku-4-5-20251001"
    SONNET = "claude-sonnet-4-6"
    OPUS = "claude-opus-4-7"

class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"      # Data formatting, routine calculations
    MODERATE = "moderate"  # Analysis with some judgment required
    COMPLEX = "complex"    # Deep reasoning, edge cases, critical decisions

class ModelSelector:
    """Selects optimal model based on task requirements"""

    # Default model assignments based on task complexity
    DEFAULT_MODEL_MAPPING = {
        TaskComplexity.SIMPLE: ModelTier.HAIKU,
        TaskComplexity.MODERATE: ModelTier.SONNET,
        TaskComplexity.COMPLEX: ModelTier.OPUS
    }

    # Specific skill-to-model assignments (overrides complexity mapping)
    SKILL_MODEL_MAPPING = {
        "morning-prep": ModelTier.HAIKU,        # Simple: Calculate levels, format output
        "trade-journal": ModelTier.SONNET,      # Complex: 8-confirmation judgment calls
        "confluence-check": ModelTier.SONNET,   # Complex: Pattern recognition, analysis
        "level-alert": ModelTier.HAIKU,         # Simple: Proximity calculations, alerts
        "generate-report": ModelTier.SONNET,    # Moderate: Data interpretation, insights
    }

    def __init__(self, user_overrides: Optional[Dict[str, str]] = None):
        """
        Initialize model selector

        Args:
            user_overrides: Dict mapping skill names to model names for user customization
        """
        self.user_overrides = user_overrides or {}

    def get_model_for_skill(self, skill_name: str) -> str:
        """
        Get optimal model for a specific skill

        Args:
            skill_name: Name of the skill (morning-prep, trade-journal, etc.)

        Returns:
            Model name string for Anthropic API
        """
        # Check user overrides first
        if skill_name in self.user_overrides:
            return self.user_overrides[skill_name]

        # Check skill-specific mappings
        if skill_name in self.SKILL_MODEL_MAPPING:
            return self.SKILL_MODEL_MAPPING[skill_name].value

        # Fallback to Sonnet for unknown skills (safe default)
        return ModelTier.SONNET.value

    def get_model_for_complexity(self, complexity: TaskComplexity) -> str:
        """
        Get optimal model for a given complexity level

        Args:
            complexity: Task complexity level

        Returns:
            Model name string for Anthropic API
        """
        return self.DEFAULT_MODEL_MAPPING[complexity].value

    def get_cost_multiplier(self, model_name: str) -> float:
        """
        Get relative cost multiplier for a model (Sonnet = 1.0 baseline)

        Args:
            model_name: Model name

        Returns:
            Cost multiplier relative to Sonnet
        """
        # Approximate cost ratios based on Anthropic pricing
        cost_ratios = {
            ModelTier.HAIKU.value: 0.15,    # ~85% cheaper than Sonnet
            ModelTier.SONNET.value: 1.0,    # Baseline
            ModelTier.OPUS.value: 3.0       # ~3x more expensive than Sonnet
        }

        return cost_ratios.get(model_name, 1.0)

    def estimate_cost_savings(self, skill_usage: Dict[str, int]) -> Dict[str, float]:
        """
        Estimate cost savings from model tiering

        Args:
            skill_usage: Dict mapping skill names to usage count per month

        Returns:
            Dict with cost analysis
        """
        total_baseline_cost = 0
        total_optimized_cost = 0

        baseline_model = ModelTier.SONNET.value
        baseline_multiplier = self.get_cost_multiplier(baseline_model)

        for skill_name, usage_count in skill_usage.items():
            # Baseline cost (everything on Sonnet)
            baseline_cost = usage_count * baseline_multiplier
            total_baseline_cost += baseline_cost

            # Optimized cost (skill-specific models)
            optimized_model = self.get_model_for_skill(skill_name)
            optimized_multiplier = self.get_cost_multiplier(optimized_model)
            optimized_cost = usage_count * optimized_multiplier
            total_optimized_cost += optimized_cost

        savings_amount = total_baseline_cost - total_optimized_cost
        savings_percentage = (savings_amount / total_baseline_cost) * 100 if total_baseline_cost > 0 else 0

        return {
            "baseline_cost": total_baseline_cost,
            "optimized_cost": total_optimized_cost,
            "savings_amount": savings_amount,
            "savings_percentage": savings_percentage,
            "model_assignments": {skill: self.get_model_for_skill(skill) for skill in skill_usage.keys()}
        }

# Global instance for easy access
model_selector = ModelSelector()

def get_optimal_model(skill_name: str) -> str:
    """Convenience function to get optimal model for a skill"""
    return model_selector.get_model_for_skill(skill_name)

def load_user_model_config() -> Optional[Dict[str, str]]:
    """
    Load user model overrides from environment or config file

    Returns:
        Dict of user model overrides or None
    """
    # Check for environment variable with JSON config
    config_env = os.getenv('MODEL_OVERRIDES')
    if config_env:
        try:
            import json
            return json.loads(config_env)
        except json.JSONDecodeError:
            print("Warning: Invalid MODEL_OVERRIDES environment variable")

    return None

# Example usage and testing
if __name__ == "__main__":
    selector = ModelSelector()

    print("🤖 Model Selection for 0DTE Trading Skills")
    print("=" * 50)

    skills = ["morning-prep", "trade-journal", "confluence-check", "level-alert", "generate-report"]

    for skill in skills:
        model = selector.get_model_for_skill(skill)
        cost_multiplier = selector.get_cost_multiplier(model)
        print(f"{skill:15} → {model:25} (Cost: {cost_multiplier:4.2f}x)")

    print("\n💰 Cost Savings Estimate")
    print("=" * 30)

    # Typical monthly usage
    monthly_usage = {
        "morning-prep": 20,      # Once per trading day
        "trade-journal": 60,     # 3 trades per day × 20 days
        "confluence-check": 40,  # Additional validations
        "level-alert": 100,      # Monitoring alerts
        "generate-report": 4     # Weekly reports
    }

    savings = selector.estimate_cost_savings(monthly_usage)
    print(f"Baseline cost (all Sonnet): {savings['baseline_cost']:.2f} units")
    print(f"Optimized cost (tiered):     {savings['optimized_cost']:.2f} units")
    print(f"Savings:                     {savings['savings_amount']:.2f} units ({savings['savings_percentage']:.1f}%)")

    print(f"\nModel Assignments:")
    for skill, model in savings['model_assignments'].items():
        print(f"  {skill}: {model}")