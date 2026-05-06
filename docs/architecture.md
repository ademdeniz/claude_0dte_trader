# Architecture Decision Record

## System Design Philosophy

This project follows the **Claude Code layered architecture**:

1. **CLAUDE.md** — Constitution layer (rules, context, strategy)
2. **Skills** — Knowledge layer (reusable AI workflows)
3. **Hooks** — Guardrail layer (deterministic enforcement)
4. **Subagents** — Delegation layer (parallel analysis)
5. **Plugins** — Distribution layer (future: shareable package)

---

## Key Architectural Decisions

### ADR-001: SQLite Over PostgreSQL

**Decision:** Use SQLite for persistence instead of PostgreSQL

**Rationale:**
- Paper trading = single user, local machine
- No need for multi-user concurrency
- Zero server setup (just a file)
- Portable (can copy entire database to new machine)
- Sufficient for 10,000+ trades

**Trade-off:** If scaling to multi-user (e.g., team of traders), migrate to PostgreSQL

---

### ADR-002: Hooks Enforce Discipline (Not Prompts)

**Decision:** Use shell script hooks to block rule violations, not AI prompts

**Rationale:**
- AI can be persuaded ("just this once...")
- Hooks are deterministic (can't be bypassed without editing code)
- Faster (no API call latency)
- More reliable (no hallucination risk)

**Example:**
```bash
# PreToolUse.sh
if [ "$TRADE_COUNT" -ge 3 ]; then
  echo "❌ BLOCKED: 3 trades taken today"
  exit 1  # Hard block
fi
```

**Trade-off:** Less flexible than AI-based guardrails, but that's the point

---

### ADR-003: Skills Auto-Invoke (Not Manual Commands)

**Decision:** Skills are auto-invoked by Claude based on description matching

**Rationale:**
- User says: "run morning prep"
- Claude matches to `skills/morning-prep/SKILL.md`
- Claude auto-forks subagent with skill context
- No need to remember command syntax

**Example:**
```markdown
# skills/morning-prep/SKILL.md
Description: Calculate prior day levels before market open
When to invoke: User says "run morning prep" OR "calculate levels" OR it's 9:25 AM
```

**Trade-off:** Requires good skill descriptions (but Claude Code handles matching)

---

### ADR-004: Subagents for Parallel Confluence Checks

**Decision:** Use subagents to check SPY, QQQ, VIX simultaneously

**Rationale:**
- Sequential checks: SPY (2s) + QQQ (2s) + VIX (2s) = 6 seconds total
- Parallel checks: All 3 simultaneously = 2 seconds total
- Faster response = better for 0DTE (minutes matter)

**Implementation:**
```python
# Main agent delegates
subagent_1.check_spy()
subagent_2.check_qqq()
subagent_3.check_vix()

# Wait for all results
results = await gather_all()
```

**Trade-off:** More complex orchestration, but worth it for speed

---

### ADR-005: No Auto-Execution (Alert Only)

**Decision:** System NEVER auto-executes trades (alerts only)

**Rationale:**
- Paper trading = manual execution (build discipline)
- Live trading = requires human confirmation (regulatory + risk)
- This is a "copilot" system, not an autopilot

**Future:** Phase 5+ (after 6+ months live trading) could add auto-execution with multi-factor confirmation

---

### ADR-006: Pandas-TA Over TA-Lib

**Decision:** Use `pandas-ta` for technical indicators instead of `ta-lib`

**Rationale:**
- pandas-ta: Pure Python, easy install (`pip install pandas-ta`)
- ta-lib: Requires C dependencies, harder install
- pandas-ta: Good enough for VWAP, EMA, volume calculations
- ta-lib: Faster, but unnecessary for our scale

**Trade-off:** If scaling to hundreds of tickers real-time, switch to ta-lib

---

### ADR-007: Real-Time Data Deferred to Phase 3

**Decision:** Phase 1-2 use delayed data (free), Phase 3+ use real-time ($29/month)

**Rationale:**
- Paper trading doesn't need real-time (15-min delay is fine)
- Saves $29/month during learning phase
- Once profitable, real-time data worth the cost

**Data Sources:**
- Phase 1-2: Yahoo Finance (free, 15-min delay)
- Phase 3+: Polygon.io ($29/month, real-time)

---

### ADR-008: CLI First, Web UI Later

**Decision:** Build CLI journal first, Streamlit dashboard later

**Rationale:**
- CLI: Fast to build (1-2 hours), works immediately
- Streamlit: Prettier, but adds complexity (4-6 hours)
- Discipline > Aesthetics in Phase 1

**Implementation Plan:**
1. Week 1: Build CLI journal (`trade_journal.py`)
2. Week 2-4: Use it for 50 paper trades
3. Week 5: If profitable, build Streamlit dashboard

---

### ADR-009: Trade Journal Before Automation

**Decision:** Build trade journal BEFORE building automation tools

**Rationale:**
- Paper trading is 90% discipline, 10% finding setups
- Need to prove you can follow rules manually before automating
- Journal tracks violations → shows which traps you fall into
- Data from journal informs automation priorities

**Workflow:**
```
Phase 1: Manual trading + Journal (prove discipline)
  ↓
Phase 2: Add Morning Prep (save time on calculations)
  ↓
Phase 3: Add Alerts (find setups faster)
  ↓
Phase 4: Full automation (signals + validation)
```

---

### ADR-010: Emotional State Tracking

**Decision:** Log emotional state on every trade entry

**Rationale:**
- Emotional trading = biggest account killer
- Tracking state creates awareness
- Patterns emerge: "I always lose when I'm frustrated"
- Enables pre-trade intervention: "Feeling frustrated? Maybe don't trade today."

**Implementation:**
```python
# On trade entry
emotional_state = input("How are you feeling? (Calm/Frustrated/Confident/Rushed): ")

# On weekly report
print(f"Win rate when Calm: 68%")
print(f"Win rate when Frustrated: 32%")  # Red flag!
```

**Trade-off:** Adds friction to logging, but worth it for self-awareness

---

## Future Architecture Considerations

### When to Migrate to Cloud

**Current:** Runs locally on laptop  
**Trigger:** Want to run 24/7 monitoring without keeping laptop on  
**Solution:** Deploy to AWS EC2 / DigitalOcean droplet ($10/month)

### When to Add Multi-Ticker Support

**Current:** One ticker at a time (SPY or AAPL)  
**Trigger:** Want to monitor 5-10 stocks simultaneously  
**Solution:** Refactor to multi-threaded streaming (1 thread per ticker)

### When to Add Team Features

**Current:** Single user  
**Trigger:** Want to share with friends / build a team  
**Solution:** Migrate to PostgreSQL, add user auth, deploy as web app

---

## Technology Choices Summary

| Component | Technology | Why |
|-----------|-----------|-----|
| Language | Python 3.9+ | Best libraries for market data + pandas |
| Database | SQLite | Single user, zero setup, portable |
| Market Data | Alpaca / Polygon.io | Industry standard, good APIs |
| Indicators | pandas-ta | Easy install, good enough |
| Notifications | Twilio / Pushover | Reliable, cheap |
| Testing | pytest | Standard Python testing |
| Web UI (optional) | Streamlit | Fast to build, interactive |

---

## Dependencies

See `requirements.txt` for full list. Key dependencies:

- `pandas` — Data manipulation
- `pandas-ta` — Technical indicators
- `alpaca-py` or `polygon-py` — Market data
- `twilio` or `pushover` — Notifications
- `pytest` — Testing
- `streamlit` (optional) — Web dashboard
