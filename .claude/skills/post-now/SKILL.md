---
name: post-now
description: Trigger the full GCode X post pipeline immediately (goes to Telegram for approval)
---

# post-now — Trigger an immediate post

Trigger the full GCode X post pipeline right now, without waiting for the daily scheduler.

## What this does
1. Selects a content type (weighted random, avoids last used)
2. Gathers any needed context (scrapes trades site or searches web)
3. Generates a post draft via Claude
4. Sends draft to your Telegram with Approve / Reject / Regenerate buttons
5. Waits for your response (auto-posts after 2 hours if no reply)

## Steps

Run this command to trigger one post immediately:

```bash
python main.py --now
```

The terminal will stay open and listen for your Telegram button press. You'll see logs showing:
- Which content type was selected
- Whether scraping/search was triggered
- The generated draft (first 80 chars in logs)
- Confirmation when posted or auto-post timer fires

## To stop
Press `Ctrl+C` at any time. If you've already sent the draft to Telegram and press Ctrl+C, the auto-post timer is cancelled and no post will go out.

## Notes
- This is safe to run at any time — it does NOT skip the Telegram approval step
- If you want a truly silent dry run (no Telegram, no X post), use `/test-generate` instead
