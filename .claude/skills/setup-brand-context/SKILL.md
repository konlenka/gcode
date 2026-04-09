---
name: setup-brand-context
description: Set up or update the GCode Algo brand context file used by every auto-generated post
---

# setup-brand-context — Set up or update your GCode Algo brand context

This command walks you through setting up `.agents/social-media-context-sms.md` — the single source of truth for your brand voice, audience, content pillars, and example posts. Every automated post the bot generates reads from this file.

**Run this once before your first live post. Re-run whenever you want to update your voice or add example posts.**

## What happens

The `social-media-context-sms` skill will:
1. Check if the context file already exists (if so, you can update specific sections)
2. Ask about your identity, audience, voice, content pillars, platforms, and anti-patterns
3. Draft the full context file for your review
4. Save it to `.agents/social-media-context-sms.md`

Once saved, the Python pipeline (`generate.py` via `context_loader.py`) automatically loads it into every Claude API call — no restart needed.

## To run

Just tell Claude: **"Set up my brand context"** or **"Update my social media context"** and the skill will activate.

Or say: **"Run social-media-context-sms"**

## To update a specific section

Say: "Update the example posts in my brand context" or "Add a new phrase to my voice section" and Claude will open the file and edit just that section.

## File location
`.agents/social-media-context-sms.md`

## What to update over time
- **Example Posts** — add your best-performing real posts as they accumulate (this is the #1 quality improvement)
- **Voice Phrases** — add new expressions you naturally use
- **Anti-Patterns** — add any tones or topics you've seen and want to avoid
- **Content Pillars** — refine your angles as you learn what resonates

## Connection to the pipeline
`context_loader.py` → `prompts.py` → prepended to system prompt → every `generate.py` call
