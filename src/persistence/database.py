# Copyright 2026 Adem Garic. All rights reserved.

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Trade, Violation, PreMarketChecklist

DB_PATH = Path(__file__).parent.parent.parent / "trades.db"

DEFAULT_SETTINGS = {
    "max_trades_per_day": "3",
    "max_consecutive_losses": "2",
    "daily_loss_limit_usd": "500",
    "daily_profit_target_pct": "25",
    "stop_loss_spy_pct": "15",
    "stop_loss_moderate_pct": "12",
    "stop_loss_volatile_pct": "10",
    "account_size_usd": "1000",
    "max_position_pct": "15",
}


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS trades (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker                  TEXT    NOT NULL,
                direction               TEXT    NOT NULL CHECK(direction IN ('CALL', 'PUT')),
                entry_price             REAL    NOT NULL,
                exit_price              REAL,
                quantity                INTEGER NOT NULL DEFAULT 1,
                profit_loss_pct         REAL,
                stop_loss_hit           INTEGER,
                emotional_state         TEXT    NOT NULL,
                candle_ok               INTEGER NOT NULL DEFAULT 0,
                volume_ok               INTEGER NOT NULL DEFAULT 0,
                vwap_ok                 INTEGER NOT NULL DEFAULT 0,
                ema9_ok                 INTEGER NOT NULL DEFAULT 0,
                ema21_ok                INTEGER NOT NULL DEFAULT 0,
                spy_ok                  INTEGER NOT NULL DEFAULT 0,
                qqq_ok                  INTEGER NOT NULL DEFAULT 0,
                support_resistance_ok   INTEGER NOT NULL DEFAULT 0,
                notes                   TEXT,
                traded_at               TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS violations (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id        INTEGER REFERENCES trades(id),
                violation_type  TEXT    NOT NULL,
                description     TEXT    NOT NULL,
                occurred_at     TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pre_market_checklist (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_date          TEXT    NOT NULL UNIQUE,
                pdh                 REAL,
                pdl                 REAL,
                pdc                 REAL,
                vwap                REAL,
                support_levels      TEXT,
                resistance_levels   TEXT,
                spy_bias            TEXT,
                vix_level           REAL,
                news_events         TEXT,
                completed           INTEGER NOT NULL DEFAULT 0,
                created_at          TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key     TEXT PRIMARY KEY,
                value   TEXT NOT NULL
            );
        """)
        _seed_default_settings(conn)


def _seed_default_settings(conn: sqlite3.Connection) -> None:
    for key, value in DEFAULT_SETTINGS.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )


# ── Trades ────────────────────────────────────────────────────────────────────

def save_trade_entry(trade: Trade) -> int:
    """Insert a new trade entry. Returns the new trade id."""
    now = trade.traded_at or datetime.now().isoformat()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO trades (
                ticker, direction, entry_price, quantity, emotional_state,
                candle_ok, volume_ok, vwap_ok, ema9_ok, ema21_ok,
                spy_ok, qqq_ok, support_resistance_ok, notes, traded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade.ticker, trade.direction, trade.entry_price, trade.quantity,
                trade.emotional_state,
                int(trade.candle_ok), int(trade.volume_ok), int(trade.vwap_ok),
                int(trade.ema9_ok), int(trade.ema21_ok),
                int(trade.spy_ok), int(trade.qqq_ok), int(trade.support_resistance_ok),
                trade.notes, now,
            ),
        )
        return cur.lastrowid


def save_trade_exit(trade_id: int, exit_price: float, stop_loss_hit: bool, notes: Optional[str] = None) -> None:
    """Update an open trade with exit data and calculated P&L."""
    with get_connection() as conn:
        row = conn.execute("SELECT entry_price FROM trades WHERE id = ?", (trade_id,)).fetchone()
        if row is None:
            raise ValueError(f"Trade {trade_id} not found")
        entry = row["entry_price"]
        pnl_pct = round((exit_price - entry) / entry * 100, 2)
        conn.execute(
            """
            UPDATE trades
            SET exit_price = ?, stop_loss_hit = ?, profit_loss_pct = ?,
                notes = COALESCE(?, notes)
            WHERE id = ?
            """,
            (exit_price, int(stop_loss_hit), pnl_pct, notes, trade_id),
        )


def get_trades_today() -> list[sqlite3.Row]:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM trades WHERE traded_at LIKE ? ORDER BY traded_at",
            (f"{today}%",),
        ).fetchall()


def get_trade_count_today() -> int:
    return len(get_trades_today())


def get_consecutive_losses() -> int:
    """Count losses at the tail of today's closed trades."""
    with get_connection() as conn:
        today = datetime.now().strftime("%Y-%m-%d")
        rows = conn.execute(
            """
            SELECT profit_loss_pct FROM trades
            WHERE traded_at LIKE ? AND exit_price IS NOT NULL
            ORDER BY traded_at DESC
            """,
            (f"{today}%",),
        ).fetchall()
    streak = 0
    for row in rows:
        if row["profit_loss_pct"] is not None and row["profit_loss_pct"] < 0:
            streak += 1
        else:
            break
    return streak


def get_daily_pnl_usd(account_size: float) -> float:
    """Return today's realized P&L in dollars (approximate via pct × account)."""
    with get_connection() as conn:
        today = datetime.now().strftime("%Y-%m-%d")
        rows = conn.execute(
            """
            SELECT profit_loss_pct FROM trades
            WHERE traded_at LIKE ? AND profit_loss_pct IS NOT NULL
            """,
            (f"{today}%",),
        ).fetchall()
    total_pct = sum(r["profit_loss_pct"] for r in rows)
    return round(total_pct / 100 * account_size, 2)


# ── Violations ────────────────────────────────────────────────────────────────

def save_violation(violation: Violation) -> int:
    now = violation.occurred_at or datetime.now().isoformat()
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO violations (trade_id, violation_type, description, occurred_at) VALUES (?, ?, ?, ?)",
            (violation.trade_id, violation.violation_type, violation.description, now),
        )
        return cur.lastrowid


def get_violations_this_week() -> list[sqlite3.Row]:
    from datetime import timedelta
    week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM violations WHERE occurred_at >= ? ORDER BY occurred_at",
            (week_start,),
        ).fetchall()


# ── Pre-Market Checklist ───────────────────────────────────────────────────────

def save_checklist(checklist: PreMarketChecklist) -> int:
    now = checklist.created_at or datetime.now().isoformat()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO pre_market_checklist
                (trade_date, pdh, pdl, pdc, vwap, support_levels, resistance_levels,
                 spy_bias, vix_level, news_events, completed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(trade_date) DO UPDATE SET
                pdh=excluded.pdh, pdl=excluded.pdl, pdc=excluded.pdc, vwap=excluded.vwap,
                support_levels=excluded.support_levels, resistance_levels=excluded.resistance_levels,
                spy_bias=excluded.spy_bias, vix_level=excluded.vix_level,
                news_events=excluded.news_events, completed=excluded.completed
            """,
            (
                checklist.trade_date, checklist.pdh, checklist.pdl, checklist.pdc,
                checklist.vwap,
                json.dumps(checklist.support_levels) if isinstance(checklist.support_levels, list) else checklist.support_levels,
                json.dumps(checklist.resistance_levels) if isinstance(checklist.resistance_levels, list) else checklist.resistance_levels,
                checklist.spy_bias, checklist.vix_level, checklist.news_events,
                int(checklist.completed), now,
            ),
        )
        return cur.lastrowid


def get_checklist_today() -> Optional[sqlite3.Row]:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM pre_market_checklist WHERE trade_date = ?",
            (today,),
        ).fetchone()


def is_checklist_complete_today() -> bool:
    row = get_checklist_today()
    return bool(row and row["completed"])


# ── Settings ──────────────────────────────────────────────────────────────────

def get_setting(key: str) -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None


def set_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
