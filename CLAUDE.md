# GCode Algo X Auto-Poster

## Business Context
This bot automatically generates and posts daily content to X (Twitter) for The GCode Algo brand — an algorithmic crypto trading service delivered via Telegram with Cornix auto-execution. Target audience: busy professionals (25–50) seeking hands-free, emotion-free crypto exposure.

**Core goal:** Drive Telegram sign-ups via `https://t.me/Gplussignup_bot?start=7a0be77b`

The bot uses Claude to generate posts, routes drafts through Telegram for human approval (with a 2-hour auto-post timeout), then publishes to X via Tweepy.

## Tech Stack
- **Language:** Python 3.11+
- **AI:** Anthropic Claude API (`claude-sonnet-4-6`, temp 0.9)
- **X Posting:** Tweepy v2 (OAuth 1.0a, Free tier)
- **Approval Flow:** python-telegram-bot v20+ (async, inline keyboard buttons)
- **Scheduling:** APScheduler (AsyncIOScheduler, random daily trigger)
- **Data:** SQLite (state.db — minimal content type tracking)
- **Web Scraping:** BeautifulSoup + requests (trades.thegcodealgo.com)
- **Web Search:** Tavily API (market commentary context only)
- **Config:** python-dotenv (.env file)

## Project Structure
```
gcode/
├── CLAUDE.md                    # This file
├── main.py                      # Entry point — run bot or --now for immediate post
├── config.py                    # Env var loading + validation (fails fast if missing)
├── workflow.py                  # Full pipeline orchestration
├── scheduler.py                 # APScheduler: random daily job 23:00–01:00 UTC
├── generate.py                  # Claude API content generation + few-shot examples
├── prompts.py                   # Two-layer prompt: brand context + GCode rules
├── context_loader.py            # Loads .agents/social-media-context-sms.md into prompts
├── scraper.py                   # Scrape trades.thegcodealgo.com for real stats
├── search.py                    # Tavily search for market commentary context
├── twitter_client.py            # Tweepy v2 tweet posting
├── telegram_bot.py              # Approval flow: send draft, handle buttons, auto-post timer
├── state.py                     # SQLite wrapper: track last 3 content types
├── prompts/
│   └── system_prompt.md         # X post format rules + GCode-specific constraints ONLY
│                                #   (brand voice lives in .agents/social-media-context-sms.md)
├── .agents/
│   └── social-media-context-sms.md   # ★ Brand voice, audience, pillars, examples (SOURCE OF TRUTH)
├── .claude/
│   └── skills/
│       ├── setup-brand-context/SKILL.md  # /setup-brand-context — run social-media-context-sms
│       ├── post-now/SKILL.md             # /post-now — trigger one post immediately
│       ├── post-with-hooks/SKILL.md      # /post-with-hooks — hook-writer → post generation
│       ├── repurpose-last/SKILL.md       # /repurpose-last — repurpose to LinkedIn/Threads/Bluesky
│       ├── test-generate/SKILL.md        # /test-generate — draft a post (no send)
│       ├── test-scraper/SKILL.md         # /test-scraper — test the trades page scraper
│       └── post-history/SKILL.md         # /post-history — show recent post log
├── data/
│   ├── example_posts.json       # JSON example posts (merged with context file examples)
│   └── stats.json               # Manual fallback stats for Social Proof posts
├── .env.example                 # API key template
├── requirements.txt
└── state.db                     # Auto-created on first run (gitignored)
```

## Social Media Skills

5 skills installed via `npx skills add blacktwist/social-media-skills` in `.agents/skills/`:

| Skill | Purpose | Triggers pipeline? |
|---|---|---|
| `social-media-context-sms` | Creates/updates `.agents/social-media-context-sms.md` — brand voice source of truth | No — setup only |
| `hook-writer-sms` | Generates 5–7 hook variants across 9 patterns | No — use via `/post-with-hooks` |
| `post-writer-sms` | Writes ad-hoc single posts outside the automated pipeline | No — manual only |
| `thread-writer-sms` | Writes multi-part threads | No — manual only |
| `content-repurposer-sms` | Repurposes X posts to LinkedIn/Threads/Bluesky | No — use via `/repurpose-last` |

**Integration architecture:**
```
.agents/social-media-context-sms.md
    ↓ loaded by context_loader.py
    ↓ prepended to system prompt in prompts.py
    ↓ injected into every Claude API call in generate.py
    ↓ also provides few-shot examples alongside data/example_posts.json
```

**IMPORTANT — Run this first:** Before the first live post, run `/setup-brand-context` to create the brand context file. The pipeline works without it but post quality is significantly better with it.

## Coding Conventions
- Python type hints on all function signatures
- All API keys loaded from environment via `config.py` — NEVER hardcoded
- Use `logging` module throughout — no bare `print()` in production code
- Use `async/await` for all network calls (Telegram, Claude, X, Tavily)
- Catch specific exceptions; on any failure → `telegram_bot.send_error_alert()`
- Keep prompts in `prompts/` directory as `.md` files, not inline strings
- State DB path: `state.db` in project root (auto-created by `state.init_db()`)

## Content Type System
| # | Type | Weight | Data needed |
|---|------|--------|-------------|
| 1 | HYPE/OPPORTUNITY | 25% | None |
| 2 | EDUCATIONAL/TIP | 25% | None |
| 3 | COMMUNITY/ENGAGEMENT | 20% | None |
| 4 | SOCIAL PROOF/RESULTS | 15% | scraper.py → trades.thegcodealgo.com |
| 5 | MARKET COMMENTARY | 10% | search.py → Tavily |
| 6 | MINDSET/PSYCHOLOGY | 5% | None |

**Rotation rule:** Never repeat the same type consecutively. Type 3 is the default fallback.

## Approval Flow
```
Scheduler fires → workflow.run_daily_post()
  → select content type
  → gather context (scrape/search if needed)
  → generate.generate_post() → Claude API
  → telegram_bot.send_for_approval()
      ├─ [✅ Approve] → twitter_client.post_tweet() → state.record_post()
      ├─ [❌ Reject]  → regenerate same type, restart 2h timer
      ├─ [🔄 Regen]  → regenerate same type, restart 2h timer
      └─ [timeout]   → auto-post → state.record_post()
  → Any exception → telegram_bot.send_error_alert()
```

## Scheduling
- Default window: **23:00–01:00 UTC** (= 6–8pm US Eastern = 9–11am Sydney/Melbourne)
- Override via `.env`: `SCHEDULE_START_UTC` and `SCHEDULE_WINDOW_MINS`
- Random minute within window so posts don't appear scheduled to followers

## Running the Bot
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with all API keys

# ★ FIRST TIME ONLY — set up brand context (run in Claude Code chat)
# /setup-brand-context

# Test one post immediately (recommended first run)
python main.py --now

# Run in production (keeps running, daily schedule)
python main.py
```

**Custom slash commands (type in Claude Code chat):**
```
/setup-brand-context  # ★ Run once first — creates brand voice context file
/post-now             # Trigger immediate post (goes to Telegram for approval)
/post-with-hooks      # Hook variants first → pick best → trigger post
/repurpose-last       # Repurpose last X post to LinkedIn/Threads/Bluesky
/test-generate        # Preview a generated draft (no Telegram, no X)
/test-scraper         # Test the trades.thegcodealgo.com scraper
/post-history         # View recent post log from SQLite
```

## Key Rules — NEVER Violate
- **NEVER fabricate stats** for Social Proof posts — only use scraped data from trades.thegcodealgo.com
- **NEVER post without Telegram approval** unless the 2-hour timeout fires
- **NEVER hardcode API keys** — always use `.env`
- **NEVER repeat the same content type consecutively**
- Post character limit: **300 chars max** (X standard is 280 — system prompt enforces 300 for safety margin)

## Environment Variables
See `.env.example` for all required keys. The bot will fail immediately on startup if any required key is missing (`config.py` validates all on import).
