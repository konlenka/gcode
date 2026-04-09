---
name: test-scraper
description: Test the trades.thegcodealgo.com scraper and display extracted performance stats
---

# test-scraper — Test the trades page scraper

Scrape `trades.thegcodealgo.com` and display the extracted performance data. Use this to verify the scraper is working and to see what stats are available for Social Proof posts.

## Steps

Run:

```bash
python -c "
import scraper
data = scraper.fetch_performance_data()
if data:
    print('Scraper SUCCESS\n')
    print(data)
else:
    print('Scraper returned no data. Check:')
    print('  1. trades.thegcodealgo.com is accessible')
    print('  2. The page structure has changed (may need scraper.py update)')
    print('  3. Your internet connection / firewall')
"
```

## What to look for
- Win rates, trade counts, profit percentages, algo names
- Any figures that can be used verbatim in Social Proof posts
- If data is empty or garbled, the scraper's keyword filters in `scraper.py:_parse()` may need updating

## Updating the scraper
If the page structure changes and the scraper stops working:
1. Open [scraper.py](../../scraper.py) and look at `_parse()`
2. Inspect the live page HTML (browser DevTools → Elements)
3. Update the `stat_keywords` list or add targeted CSS selectors for specific data tables
4. Re-run this skill to confirm

## Notes
- The scraper uses a real browser User-Agent to avoid bot blocks
- Timeout is 15 seconds (configurable in `scraper.py:TIMEOUT`)
- On failure, the bot sends a Telegram alert and falls back to narrative-style Social Proof posts
