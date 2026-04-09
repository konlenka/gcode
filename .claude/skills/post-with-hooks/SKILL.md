---
name: post-with-hooks
description: Generate 5-7 hook variants first, pick the best one, then trigger the full post pipeline
---

# post-with-hooks — Generate hooks first, then build the post around the best one

Uses `hook-writer-sms` to generate 5–7 opening line variants, lets you pick the strongest, then triggers the full pipeline with that hook as a creative seed. Best used when you want extra control over the post's angle before it goes to Telegram for approval.

## When to use this
- You have a specific angle or topic in mind for today's post
- You want to A/B test different hook approaches before committing
- The auto-generated post from `/post-now` didn't feel right — use this to start from the hook and rebuild

## Steps

### Step 1 — Tell Claude the topic and content type
Say something like:
- "Run post-with-hooks for a Social Proof post about our win rate"
- "Run post-with-hooks, Educational type, topic: position sizing mistakes"
- "Run post-with-hooks, Community type, about emotional trading"

### Step 2 — Hook-writer generates variants
Claude will run `hook-writer-sms` using the brand context from `.agents/social-media-context-sms.md` and generate 5–7 hook variants across different patterns:
- Contrarian, Question, Confession, Industry Secret, Myth-Busting, Comparison Shock, Challenge

### Step 3 — You pick the best hook
Review the variants and tell Claude which number you prefer (or "combine 2 and 5").

### Step 4 — Generate the full post
Claude builds the complete post around your chosen hook, then triggers the full approval pipeline:

```bash
python main.py --now
```

The Telegram draft will be sent with your selected hook as the opening line.

## Tips
- The hooks from `hook-writer-sms` follow the same anti-repetition rules as the main pipeline
- You can ask for more variants: "Give me 3 more contrarian options"
- If you want to skip Telegram and just preview: ask Claude to "show me the full post without sending it"
