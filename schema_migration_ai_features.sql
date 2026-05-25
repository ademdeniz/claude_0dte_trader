-- Schema Migration: AI Features for 0DTE Trading Dashboard
-- Adds tables for caching AI analysis results to minimize token costs

-- ══════════════════════════════════════════════════════════════════════
-- AI BRIEFINGS TABLE
-- Caches daily pre-market briefings (expires end of trading day)
-- ══════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS ai_briefings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT    NOT NULL UNIQUE,       -- YYYY-MM-DD format
    content     TEXT    NOT NULL,              -- JSON briefing data
    tokens_used INTEGER NOT NULL DEFAULT 0,    -- Token cost tracking
    cost_usd    REAL    NOT NULL DEFAULT 0.0,  -- USD cost tracking
    created_at  TEXT    NOT NULL               -- ISO timestamp
);

-- Index for fast date lookups
CREATE INDEX IF NOT EXISTS idx_briefings_date ON ai_briefings(date);

-- ══════════════════════════════════════════════════════════════════════
-- AI ANALYSES TABLE
-- Caches pattern analysis, strategy variations, etc. (weekly/monthly)
-- ══════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS ai_analyses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_type TEXT    NOT NULL,              -- 'journal_pattern', 'strategy_variation', etc.
    time_period   TEXT,                          -- '7d', '30d', '90d', 'all', NULL for one-time
    content       TEXT    NOT NULL,              -- JSON analysis result
    tokens_used   INTEGER NOT NULL DEFAULT 0,    -- Token cost tracking
    cost_usd      REAL    NOT NULL DEFAULT 0.0,  -- USD cost tracking
    created_at    TEXT    NOT NULL               -- ISO timestamp
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_analyses_type_period ON ai_analyses(analysis_type, time_period);
CREATE INDEX IF NOT EXISTS idx_analyses_created ON ai_analyses(created_at);

-- ══════════════════════════════════════════════════════════════════════
-- AI GUT CHECKS TABLE
-- Per-trade psychological assessment cache
-- ══════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS ai_gut_checks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id        INTEGER REFERENCES trades(id),    -- Link to specific trade
    emotional_state TEXT    NOT NULL,                 -- CALM, ANXIOUS, FOMO, etc.
    focus_level     INTEGER NOT NULL,                 -- 1-10 scale
    conviction      INTEGER NOT NULL,                 -- 1-10 scale
    verdict         TEXT    NOT NULL CHECK(verdict IN ('PROCEED', 'STAND_DOWN')),
    reasoning       TEXT    NOT NULL,                 -- AI explanation
    tokens_used     INTEGER NOT NULL DEFAULT 0,      -- Token cost tracking
    created_at      TEXT    NOT NULL                  -- ISO timestamp
);

-- Index for trade lookup
CREATE INDEX IF NOT EXISTS idx_gut_checks_trade ON ai_gut_checks(trade_id);

-- ══════════════════════════════════════════════════════════════════════
-- AI REVIEWS TABLE
-- Post-trade execution analysis cache
-- ══════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS ai_reviews (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id             INTEGER REFERENCES trades(id),          -- Link to specific trade
    execution_grade      TEXT    NOT NULL CHECK(execution_grade IN ('A', 'B', 'C', 'D', 'F')),
    lesson               TEXT    NOT NULL,                       -- Key lesson learned
    tomorrow_adjustment  TEXT    NOT NULL,                       -- What to do differently
    tokens_used          INTEGER NOT NULL DEFAULT 0,            -- Token cost tracking
    created_at           TEXT    NOT NULL                        -- ISO timestamp
);

-- Index for trade lookup
CREATE INDEX IF NOT EXISTS idx_reviews_trade ON ai_reviews(trade_id);

-- ══════════════════════════════════════════════════════════════════════
-- USER EDUCATION TABLE
-- Learning concepts and Q&A cache
-- ══════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS user_education (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    concept      TEXT    NOT NULL,                  -- Concept name
    question     TEXT,                              -- User's question (if custom)
    explanation  TEXT    NOT NULL,                  -- AI explanation/tutorial
    key_takeaway TEXT    NOT NULL,                  -- Main point to remember
    applied      BOOLEAN NOT NULL DEFAULT FALSE,    -- Has user applied this knowledge?
    tokens_used  INTEGER NOT NULL DEFAULT 0,        -- Token cost tracking
    created_at   TEXT    NOT NULL                   -- ISO timestamp
);

-- Index for concept lookup
CREATE INDEX IF NOT EXISTS idx_education_concept ON user_education(concept);
CREATE INDEX IF NOT EXISTS idx_education_applied ON user_education(applied);

-- ══════════════════════════════════════════════════════════════════════
-- AI USAGE TRACKING VIEW
-- Summary view for monitoring AI costs and usage
-- ══════════════════════════════════════════════════════════════════════
CREATE VIEW IF NOT EXISTS ai_usage_summary AS
SELECT
    'briefings' as category,
    COUNT(*) as count,
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost_usd,
    AVG(tokens_used) as avg_tokens,
    MAX(created_at) as last_used
FROM ai_briefings

UNION ALL

SELECT
    'analyses' as category,
    COUNT(*) as count,
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost_usd,
    AVG(tokens_used) as avg_tokens,
    MAX(created_at) as last_used
FROM ai_analyses

UNION ALL

SELECT
    'gut_checks' as category,
    COUNT(*) as count,
    SUM(tokens_used) as total_tokens,
    0.0 as total_cost_usd,  -- Cost calculated from tokens
    AVG(tokens_used) as avg_tokens,
    MAX(created_at) as last_used
FROM ai_gut_checks

UNION ALL

SELECT
    'reviews' as category,
    COUNT(*) as count,
    SUM(tokens_used) as total_tokens,
    0.0 as total_cost_usd,  -- Cost calculated from tokens
    AVG(tokens_used) as avg_tokens,
    MAX(created_at) as last_used
FROM ai_reviews

UNION ALL

SELECT
    'education' as category,
    COUNT(*) as count,
    SUM(tokens_used) as total_tokens,
    0.0 as total_cost_usd,  -- Cost calculated from tokens
    AVG(tokens_used) as avg_tokens,
    MAX(created_at) as last_used
FROM user_education;