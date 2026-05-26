# Copyright 2026 Adem Garic. All rights reserved.

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Trade:
    ticker: str
    direction: str           # CALL or PUT
    entry_price: float
    quantity: int            # number of contracts
    emotional_state: str     # Calm / Confident / Frustrated / Rushed
    # 8 confirmations (True = confirmed, False = not confirmed)
    candle_ok: bool
    volume_ok: bool
    vwap_ok: bool
    ema9_ok: bool
    ema21_ok: bool
    spy_ok: bool
    qqq_ok: bool
    support_resistance_ok: bool
    # set on exit
    exit_price: Optional[float] = None
    stop_loss_hit: Optional[bool] = None   # True = exited at stop, False = exited at target/manual
    profit_loss_pct: Optional[float] = None
    notes: Optional[str] = None
    id: Optional[int] = None
    traded_at: Optional[str] = None        # ISO datetime


@dataclass
class Violation:
    trade_id: Optional[int]   # None if violation happened outside a trade (e.g. checklist skipped)
    violation_type: str       # FOMO | OVERTRADING | REVENGE | AVERAGING_DOWN | NO_CHECKLIST | IGNORED_STOP | EARLY_CUT | DISTRACTED
    description: str
    id: Optional[int] = None
    occurred_at: Optional[str] = None     # ISO datetime


@dataclass
class PreMarketChecklist:
    trade_date: str           # YYYY-MM-DD
    ticker: str = "SPY"       # Primary ticker being traded
    pdh: Optional[float] = None
    pdl: Optional[float] = None
    pdc: Optional[float] = None
    vwap: Optional[float] = None
    support_levels: Optional[str] = None  # JSON list of floats
    resistance_levels: Optional[str] = None
    spy_bias: Optional[str] = None        # BULLISH | BEARISH | NEUTRAL
    vix_level: Optional[float] = None
    news_events: Optional[str] = None     # free text — FOMC, CPI, earnings, etc.
    completed: bool = False
    id: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class Settings:
    key: str
    value: str
