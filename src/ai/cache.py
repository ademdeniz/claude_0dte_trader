"""
AI Result Caching System

Database-backed caching for AI analysis results with TTL support.
Reduces token costs by avoiding repeated AI calls for stable data.

Cache Types:
- Daily cache: Pre-market briefings, daily bias (expires end of trading day)
- Weekly cache: Journal analysis (expires when new trades added)
- Per-trade cache: Gut checks, reviews (permanent, linked to trade_id)
- Education cache: Concept explanations (permanent, reusable)
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "trades.db"

def get_connection() -> sqlite3.Connection:
    """Get database connection"""
    conn = sqlite3.Connection(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

class AICache:
    """Database-backed AI result cache with TTL support"""

    def __init__(self):
        self._ensure_cache_tables()

    def _ensure_cache_tables(self):
        """Ensure cache tables exist (will be created in database migration)"""
        # Tables will be created in the database migration step
        # This is just a placeholder to ensure the class works
        pass

    # ── Daily Cache (Pre-market briefings, daily bias) ──────────────────────

    def get_daily_briefing(self, date: str) -> Optional[Dict]:
        """Get cached daily briefing for a specific date"""
        try:
            with get_connection() as conn:
                result = conn.execute(
                    "SELECT content, tokens_used, cost_usd, created_at FROM ai_briefings WHERE date = ?",
                    (date,)
                ).fetchone()

                if result:
                    return {
                        "content": json.loads(result["content"]),
                        "tokens_used": result["tokens_used"],
                        "cost_usd": result["cost_usd"],
                        "created_at": result["created_at"],
                        "cached": True
                    }
                return None
        except Exception as e:
            print(f"⚠️ Error getting daily briefing: {e}")
            return None

    def cache_daily_briefing(
        self,
        date: str,
        content: Dict,
        tokens_used: int,
        cost_usd: float
    ) -> bool:
        """Cache daily briefing result"""
        try:
            with get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO ai_briefings
                    (date, content, tokens_used, cost_usd, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    date,
                    json.dumps(content),
                    tokens_used,
                    cost_usd,
                    datetime.now().isoformat()
                ))
                return True
        except Exception as e:
            print(f"⚠️ Error caching daily briefing: {e}")
            return False

    def is_daily_cache_valid(self, date: str, max_age_hours: int = 8) -> bool:
        """Check if daily cache is still valid (not too old)"""
        cached_result = self.get_daily_briefing(date)
        if not cached_result:
            return False

        # Check age
        cached_time = datetime.fromisoformat(cached_result["created_at"])
        age_hours = (datetime.now() - cached_time).total_seconds() / 3600

        return age_hours <= max_age_hours

    # ── Analysis Cache (Journal patterns, strategy variations) ──────────────

    def get_analysis(self, analysis_type: str, time_period: str = None) -> Optional[Dict]:
        """Get cached analysis result"""
        try:
            with get_connection() as conn:
                if time_period:
                    result = conn.execute("""
                        SELECT content, tokens_used, cost_usd, created_at
                        FROM ai_analyses
                        WHERE analysis_type = ? AND time_period = ?
                        ORDER BY created_at DESC LIMIT 1
                    """, (analysis_type, time_period)).fetchone()
                else:
                    result = conn.execute("""
                        SELECT content, tokens_used, cost_usd, created_at
                        FROM ai_analyses
                        WHERE analysis_type = ?
                        ORDER BY created_at DESC LIMIT 1
                    """, (analysis_type,)).fetchone()

                if result:
                    return {
                        "content": json.loads(result["content"]),
                        "tokens_used": result["tokens_used"],
                        "cost_usd": result["cost_usd"],
                        "created_at": result["created_at"],
                        "cached": True
                    }
                return None
        except Exception as e:
            print(f"⚠️ Error getting analysis: {e}")
            return None

    def cache_analysis(
        self,
        analysis_type: str,
        content: Dict,
        tokens_used: int,
        cost_usd: float,
        time_period: str = None
    ) -> bool:
        """Cache analysis result"""
        try:
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO ai_analyses
                    (analysis_type, time_period, content, tokens_used, cost_usd, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    analysis_type,
                    time_period,
                    json.dumps(content),
                    tokens_used,
                    cost_usd,
                    datetime.now().isoformat()
                ))
                return True
        except Exception as e:
            print(f"⚠️ Error caching analysis: {e}")
            return False

    def invalidate_analysis(self, analysis_type: str, time_period: str = None):
        """Invalidate cached analysis (e.g., when new trades are added)"""
        try:
            with get_connection() as conn:
                if time_period:
                    conn.execute(
                        "DELETE FROM ai_analyses WHERE analysis_type = ? AND time_period = ?",
                        (analysis_type, time_period)
                    )
                else:
                    conn.execute(
                        "DELETE FROM ai_analyses WHERE analysis_type = ?",
                        (analysis_type,)
                    )
        except Exception as e:
            print(f"⚠️ Error invalidating analysis cache: {e}")

    # ── Per-Trade Cache (Gut checks, reviews) ───────────────────────────────

    def get_gut_check(self, trade_id: int) -> Optional[Dict]:
        """Get cached gut check for a trade"""
        try:
            with get_connection() as conn:
                result = conn.execute("""
                    SELECT emotional_state, focus_level, conviction, verdict, reasoning, tokens_used, created_at
                    FROM ai_gut_checks WHERE trade_id = ?
                """, (trade_id,)).fetchone()

                if result:
                    return dict(result)
                return None
        except Exception as e:
            print(f"⚠️ Error getting gut check: {e}")
            return None

    def cache_gut_check(
        self,
        trade_id: int,
        emotional_state: str,
        focus_level: int,
        conviction: int,
        verdict: str,
        reasoning: str,
        tokens_used: int
    ) -> bool:
        """Cache gut check result"""
        try:
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO ai_gut_checks
                    (trade_id, emotional_state, focus_level, conviction, verdict, reasoning, tokens_used, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_id,
                    emotional_state,
                    focus_level,
                    conviction,
                    verdict,
                    reasoning,
                    tokens_used,
                    datetime.now().isoformat()
                ))
                return True
        except Exception as e:
            print(f"⚠️ Error caching gut check: {e}")
            return False

    def get_trade_review(self, trade_id: int) -> Optional[Dict]:
        """Get cached trade review"""
        try:
            with get_connection() as conn:
                result = conn.execute("""
                    SELECT execution_grade, lesson, tomorrow_adjustment, tokens_used, created_at
                    FROM ai_reviews WHERE trade_id = ?
                """, (trade_id,)).fetchone()

                if result:
                    return dict(result)
                return None
        except Exception as e:
            print(f"⚠️ Error getting trade review: {e}")
            return None

    def cache_trade_review(
        self,
        trade_id: int,
        execution_grade: str,
        lesson: str,
        tomorrow_adjustment: str,
        tokens_used: int
    ) -> bool:
        """Cache trade review result"""
        try:
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO ai_reviews
                    (trade_id, execution_grade, lesson, tomorrow_adjustment, tokens_used, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    trade_id,
                    execution_grade,
                    lesson,
                    tomorrow_adjustment,
                    tokens_used,
                    datetime.now().isoformat()
                ))
                return True
        except Exception as e:
            print(f"⚠️ Error caching trade review: {e}")
            return False

    # ── Education Cache (Concept explanations) ─────────────────────────────

    def get_education_concept(self, concept: str) -> Optional[Dict]:
        """Get cached education concept"""
        try:
            with get_connection() as conn:
                result = conn.execute("""
                    SELECT question, explanation, key_takeaway, applied, tokens_used, created_at
                    FROM user_education WHERE concept = ?
                    ORDER BY created_at DESC LIMIT 1
                """, (concept,)).fetchone()

                if result:
                    return dict(result)
                return None
        except Exception as e:
            print(f"⚠️ Error getting education concept: {e}")
            return None

    def cache_education_concept(
        self,
        concept: str,
        question: str,
        explanation: str,
        key_takeaway: str,
        tokens_used: int
    ) -> bool:
        """Cache education concept result"""
        try:
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO user_education
                    (concept, question, explanation, key_takeaway, applied, tokens_used, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    concept,
                    question,
                    explanation,
                    key_takeaway,
                    False,  # applied = False initially
                    tokens_used,
                    datetime.now().isoformat()
                ))
                return True
        except Exception as e:
            print(f"⚠️ Error caching education concept: {e}")
            return False

    def mark_concept_applied(self, concept: str) -> bool:
        """Mark an education concept as applied"""
        try:
            with get_connection() as conn:
                conn.execute(
                    "UPDATE user_education SET applied = ? WHERE concept = ?",
                    (True, concept)
                )
                return True
        except Exception as e:
            print(f"⚠️ Error marking concept as applied: {e}")
            return False

    # ── Cache Statistics ──────────────────────────────────────────────────

    def get_cache_stats(self) -> Dict:
        """Get cache usage statistics"""
        try:
            with get_connection() as conn:
                briefings = conn.execute("SELECT COUNT(*), SUM(tokens_used), SUM(cost_usd) FROM ai_briefings").fetchone()
                analyses = conn.execute("SELECT COUNT(*), SUM(tokens_used), SUM(cost_usd) FROM ai_analyses").fetchone()
                gut_checks = conn.execute("SELECT COUNT(*), SUM(tokens_used) FROM ai_gut_checks").fetchone()
                reviews = conn.execute("SELECT COUNT(*), SUM(tokens_used) FROM ai_reviews").fetchone()
                education = conn.execute("SELECT COUNT(*), SUM(tokens_used) FROM user_education").fetchone()

                return {
                    "briefings": {"count": briefings[0] or 0, "tokens": briefings[1] or 0, "cost": briefings[2] or 0},
                    "analyses": {"count": analyses[0] or 0, "tokens": analyses[1] or 0, "cost": analyses[2] or 0},
                    "gut_checks": {"count": gut_checks[0] or 0, "tokens": gut_checks[1] or 0},
                    "reviews": {"count": reviews[0] or 0, "tokens": reviews[1] or 0},
                    "education": {"count": education[0] or 0, "tokens": education[1] or 0},
                    "total_tokens": (briefings[1] or 0) + (analyses[1] or 0) + (gut_checks[1] or 0) + (reviews[1] or 0) + (education[1] or 0),
                    "total_cost": (briefings[2] or 0) + (analyses[2] or 0)
                }
        except Exception as e:
            print(f"⚠️ Error getting cache stats: {e}")
            return {"error": str(e)}

    def clear_old_cache(self, days_old: int = 30):
        """Clear cache entries older than specified days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()

            with get_connection() as conn:
                # Clear old briefings (but keep recent ones)
                conn.execute("DELETE FROM ai_briefings WHERE created_at < ?", (cutoff_date,))

                # Clear old analyses (they can be regenerated)
                conn.execute("DELETE FROM ai_analyses WHERE created_at < ?", (cutoff_date,))

                # Keep gut checks and reviews (linked to specific trades)
                # Keep education (valuable knowledge base)

                print(f"🧹 Cleared AI cache entries older than {days_old} days")
        except Exception as e:
            print(f"⚠️ Error clearing old cache: {e}")

# Global instance
ai_cache = AICache()

def get_ai_cache() -> AICache:
    """Get global AI cache instance"""
    return ai_cache