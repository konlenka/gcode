---
name: test-generate
description: Preview a generated post draft without sending to Telegram or posting to X
---

# test-generate — Preview a post draft (no send, no post)

Generate a post draft and display it here in Claude Code — without sending to Telegram or posting to X. Use this to check the quality and style of generated content.

## What this does
- Reads the last 3 content types from state.db
- Selects the next content type (weighted random, avoids last used)
- Scrapes or searches for context if needed
- Calls Claude to generate the post
- Prints the draft here with metadata (type, char count, context used)

## Steps

Run this Python snippet:

```python
import sys, io, state, generate, scraper, search, random
from prompts import CONTENT_TYPES, CONTENT_TYPE_WEIGHTS
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

state.init_db()
last_3 = state.get_last_3_types()
last_type = last_3[0] if last_3 else None

eligible = {t: w for t, w in CONTENT_TYPE_WEIGHTS.items() if t != last_type}
content_type = random.choices(list(eligible.keys()), weights=list(eligible.values()), k=1)[0]

context_data = ""
if content_type == 4:
    context_data = scraper.fetch_performance_data()
elif content_type == 5:
    context_data = search.fetch_market_context()

post = generate.generate_post(content_type, last_3, context_data)

print(f"\n{'='*60}")
print(f"Content Type : {content_type} — {CONTENT_TYPES[content_type]}")
print(f"Char Count   : {len(post)} / 280")
print(f"Last 3 Types : {[CONTENT_TYPES.get(t) for t in last_3]}")
print(f"{'='*60}\n")
print(post)
print(f"\n{'='*60}")
```

## Notes
- This does NOT record the post to state.db (so it won't affect the rotation)
- Safe to run as many times as you like for testing
- To test a specific content type, set `content_type = 3` (or 1–6) before the generate call
