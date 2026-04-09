---
name: repurpose-last
description: Take the most recent X post and repurpose it for LinkedIn, Threads, and/or Bluesky
---

# repurpose-last — Repurpose your latest X post across other platforms

Takes the most recently published X post from `state.db` and uses `content-repurposer-sms` to produce platform-native versions for LinkedIn, Threads, and/or Bluesky — without copy-pasting.

## When to use this
- After a post gets good engagement and you want to push it to more platforms
- To build a multi-platform presence from a single daily automated post
- To get more reach from content you've already approved

## Steps

### Step 1 — Fetch the last post
Claude reads the most recent post from `state.db`:

```python
import sqlite3, os
conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath('state.py')), 'state.db'))
rows = conn.execute("SELECT content_type, posted_at, status FROM post_log ORDER BY id DESC LIMIT 1").fetchall()
conn.close()
```

*Note: state.db tracks content type and timestamp but not the post text (minimal logging). You may need to paste the post text from X if you want exact repurposing. Alternatively, Claude can regenerate a post of the same type from that date.*

### Step 2 — Choose platforms to repurpose to
Tell Claude which platforms:
- "Repurpose to LinkedIn and Threads"
- "Just LinkedIn"
- "All three — LinkedIn, Threads, Bluesky"

### Step 3 — content-repurposer-sms creates platform-native versions
Claude runs `content-repurposer-sms` using:
- The original X post as source content
- The brand context from `.agents/social-media-context-sms.md`
- Platform-specific rules (LinkedIn: longer, professional; Threads: casual; Bluesky: 300 chars, witty)

### Step 4 — Review and post
Claude displays each derivative. You copy and post them manually, or use BlackTwist MCP if connected.

## Platform format notes
| Platform | Length | Tone | Hashtags |
|---|---|---|---|
| LinkedIn | 1,200–1,500 chars | Professional, data-backed | 3–5 at end |
| Threads | ≤500 chars | Casual, conversational | Optional |
| Bluesky | ≤300 chars | Anti-corporate, witty | Minimal |

## Tip
Add the best repurposed posts to your brand context as examples:
"Add this LinkedIn version as an example post in my brand context"
