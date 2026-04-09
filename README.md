# GCode Algo X Auto-Poster

Automated daily X (Twitter) posting bot for [The GCode Algo](https://thegcodealgo.com) — an algorithmic crypto trading service. Generates brand-consistent posts via Claude AI, routes drafts through Telegram for approval, and publishes to X automatically.

---

## How it works

```
Daily schedule (random time, 11pm–1am UTC)
  → Claude AI generates a post (6 content types, weighted rotation)
  → Draft sent to your Telegram with Approve / Reject / Regenerate buttons
  → You approve → posts to X instantly
  → No response in 2 hours → auto-posts
```

---

## Features

- **AI-generated posts** — Claude `claude-sonnet-4-6` with your brand voice baked in
- **6 content types** — Hype, Educational, Community, Social Proof, Market Commentary, Mindset (weighted rotation, never repeats consecutively)
- **Telegram approval flow** — review every post before it goes live, with one-tap approve/reject/regenerate
- **2-hour auto-post** — never misses a day if you don't respond
- **Live stats scraping** — pulls real performance data from `trades.thegcodealgo.com` for Social Proof posts
- **Market context** — Tavily web search injects fresh crypto news for Market Commentary posts
- **Anti-fabrication** — hard-coded rules prevent Claude from inventing stats or guaranteeing returns
- **Brand context system** — single source-of-truth file drives every post's voice, audience framing, and tone

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/konlenka/gcode.git
cd gcode
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env` with your API keys:

| Key | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `X_API_KEY` + `X_API_SECRET` | [developer.twitter.com](https://developer.twitter.com) → Your App → Keys and Tokens |
| `X_ACCESS_TOKEN` + `X_ACCESS_TOKEN_SECRET` | Same page → Access Token and Secret |
| `TELEGRAM_BOT_TOKEN` | Message [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TELEGRAM_CHAT_ID` | Message [@userinfobot](https://t.me/userinfobot) — it replies with your ID |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) — free tier available |

> **X API note:** Free tier is sufficient, but you must enable **Read and Write** permissions in your app settings on developer.twitter.com.

### 3. Test one post

```bash
python main.py --now
```

This generates a post and sends it to your Telegram for approval. No scheduling — fires immediately.

### 4. Run in production

```bash
python main.py
```

Keeps running. Posts once per day at a random time within the configured UTC window.

---

## Claude Code commands

If you're using [Claude Code](https://claude.ai/code), these slash commands are available:

| Command | What it does |
|---|---|
| `/post-now` | Trigger an immediate post (goes to Telegram for approval) |
| `/test-generate` | Preview a generated draft — no Telegram, no X |
| `/test-scraper` | Test the trades page scraper |
| `/post-history` | View recent post log from SQLite |
| `/setup-brand-context` | Update your brand voice, audience, and example posts |
| `/post-with-hooks` | Generate hook variants first, pick the best, then post |
| `/repurpose-last` | Repurpose your last X post to LinkedIn, Threads, or Bluesky |

---

## Content types

| # | Type | Weight | Data source |
|---|---|---|---|
| 1 | Hype / Opportunity | 25% | None |
| 2 | Educational / Tip | 25% | None |
| 3 | Community / Engagement | 20% | None |
| 4 | Social Proof / Results | 15% | Scrapes trades.thegcodealgo.com |
| 5 | Market Commentary | 10% | Tavily web search |
| 6 | Mindset / Psychology | 5% | None |

---

## Project structure

```
gcode/
├── main.py              # Entry point
├── workflow.py          # Pipeline orchestration
├── generate.py          # Claude API post generation
├── prompts.py           # Two-layer prompt system
├── context_loader.py    # Loads brand context into every Claude call
├── scheduler.py         # Daily random trigger (APScheduler)
├── telegram_bot.py      # Approval flow + error alerts
├── twitter_client.py    # Tweepy v2 tweet posting
├── scraper.py           # Performance data scraper
├── search.py            # Tavily market context search
├── state.py             # SQLite post log
├── config.py            # Env var loading + validation
├── prompts/
│   └── system_prompt.md              # X post format rules
├── .agents/
│   └── social-media-context-sms.md  # Brand voice source of truth
├── data/
│   ├── example_posts.json            # Few-shot example posts
│   └── stats.json                    # Fallback performance stats
└── .env.example                      # API key template
```

---

## Customisation

**Change your brand voice** — edit `.agents/social-media-context-sms.md` or run `/setup-brand-context` in Claude Code.

**Add example posts** — paste your best-performing real posts into the `## Example Posts` section of `.agents/social-media-context-sms.md`. The more real examples, the more accurately Claude matches your voice.

**Update performance stats** — fill in `data/stats.json` with real numbers for Social Proof posts (used as fallback when the live scraper can't reach your site).

**Change posting time** — set `SCHEDULE_START_UTC` and `SCHEDULE_WINDOW_MINS` in `.env`. Default: 23:00–01:00 UTC (6–8pm US Eastern / 9–11am Sydney).

---

## Tech stack

- **Python 3.11+**
- **Anthropic Claude API** — `claude-sonnet-4-6`, temperature 0.9
- **Tweepy v2** — X posting via OAuth 1.0a
- **python-telegram-bot v20+** — async approval flow
- **APScheduler** — daily random trigger
- **BeautifulSoup + requests** — performance data scraping
- **Tavily** — market context search
- **SQLite** — minimal state tracking
