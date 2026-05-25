# Morning Prep Skill (Cached Implementation)

## Description
Calculate prior day levels using cached Anthropic API calls to reduce token consumption by 70-80%.

## When to Invoke
- User says: "run morning prep", "calculate levels", "morning prep", "get PDH PDL"
- Automatically at 9:25 AM ET (if SessionStart hook enabled)
- Before first trade of the day (enforced by PreToolUse hook)

## Optimized Implementation

This skill now uses a cached Python implementation that:
- ✅ **Caches system prompts** with `cache_control` markers
- ✅ **Reduces token usage by 70-80%** after first call
- ✅ **Returns structured JSON** instead of prose
- ✅ **Pre-validates data** in Python before AI calls

## What This Skill Does

Execute the cached morning prep script:

```bash
python3 tools/scripts/cached_morning_prep.py
```

The script will:
1. Use cached AI prompts for methodology (cached content)
2. Pass only dynamic data (current date) to AI (non-cached)
3. Calculate key levels: PDH, PDL, PDC, VWAP
4. Identify high-volume zones and support/resistance
5. Save results to database
6. Update pre-market checklist status

## Output Format

```json
{
    "status": "success",
    "data": {
        "pdh": 503.50,
        "pdl": 499.80, 
        "pdc": 501.20,
        "vwap": 501.35,
        "high_volume_zones": [...],
        "support_levels": [...],
        "resistance_levels": [...]
    },
    "summary": "Brief text summary",
    "timestamp": "2026-05-24T10:00:00Z"
}
```

## Token Usage Comparison

**Before (Original Skill):**
- System context: ~8,000 tokens
- Response: ~1,500 tokens  
- **Total: ~9,500 tokens**

**After (Cached Implementation):**
- First call: ~9,500 tokens (same as before)
- Subsequent calls: ~2,000 tokens (cached system prompt)
- **Savings: 78% reduction after cache warm-up**

## API Key Setup

Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

## Testing

Test without API key:
```bash
python3 tools/scripts/cached_morning_prep.py --test
```

## Error Handling

The script handles:
- Missing API key (falls back to test mode)
- API errors (returns error status)
- Invalid JSON responses (logs and retries)
- Database connection issues (saves to backup file)

## Follow-Up Actions

After running this skill:
1. Pre-market checklist automatically updated
2. Levels saved to database
3. Ready to start trading at 9:45 AM
4. PreToolUse hook will verify completion before trade logging