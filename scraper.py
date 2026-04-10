"""
scraper.py — Scrape real performance data from trades.thegcodealgo.com.

The site is a JavaScript SPA, so Playwright is used to fully render the page
before parsing. On success, data is cached to data/stats.json so it's available
if the site is temporarily unreachable on the next run.

Used for Type 4 (Social Proof) posts. Returns a formatted string of real algo
performance stats to pass into the Claude prompt.

Returns empty string on failure (generate.py falls back to cached stats.json).
"""

import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

TRADES_URL = "https://trades.thegcodealgo.com"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "data", "stats.json")
PAGE_TIMEOUT = 20000  # ms — how long to wait for page to fully load


def fetch_performance_data() -> str:
    """
    Scrape trades.thegcodealgo.com using Playwright (JS-rendered).
    Caches successful results to data/stats.json.

    Returns:
        str: Plain-text performance stats for Claude, or "" on failure.
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        logger.warning("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return _load_cache()

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            })

            logger.info("Playwright: navigating to %s", TRADES_URL)
            page.goto(TRADES_URL, wait_until="networkidle", timeout=PAGE_TIMEOUT)

            # Give JS time to populate any dynamic stats
            page.wait_for_timeout(3000)

            text = page.inner_text("body")
            browser.close()

        if not text or len(text.strip()) < 20:
            logger.warning("Playwright returned empty page body — site may be down.")
            return _load_cache()

        result = _parse(text)

        if result:
            _save_cache(result)
            logger.info("Scraper success — %d chars of stats data", len(result))
        else:
            logger.warning("Playwright rendered page but found no stat keywords.")
            return _load_cache()

        return result

    except Exception as e:
        logger.warning("Playwright scrape failed: %s", e)
        return _load_cache()


def _parse(text: str) -> str:
    """Extract stat-relevant lines from the rendered page text."""
    stat_keywords = [
        "win", "rate", "profit", "trade", "return", "signal",
        "accuracy", "drawdown", "algo", "%", "pnl", "loss",
        "gain", "total", "monthly", "weekly", "performance",
    ]

    lines = text.splitlines()
    seen: set[str] = set()
    results: list[str] = []

    for line in lines:
        line = line.strip()
        if len(line) < 4 or len(line) > 300:
            continue
        line_lower = line.lower()
        if any(kw in line_lower for kw in stat_keywords):
            if line not in seen:
                seen.add(line)
                results.append(line)
        if len(results) >= 25:
            break

    return "\n".join(results)


def _save_cache(data: str) -> None:
    """Save scraped text to stats.json as a timestamped cache."""
    try:
        cache = {
            "_note": "Auto-populated by scraper.py — do not edit manually",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "source": TRADES_URL,
            "raw_stats": data,
        }
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
        logger.debug("Stats cache updated: %s", CACHE_FILE)
    except Exception as e:
        logger.warning("Failed to save stats cache: %s", e)


def _load_cache() -> str:
    """Load last successful scrape from stats.json cache."""
    try:
        if not os.path.exists(CACHE_FILE):
            return ""
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
        raw = cache.get("raw_stats", "")
        if raw:
            last_updated = cache.get("last_updated", "unknown")
            logger.info("Using cached stats from %s", last_updated)
        return raw
    except Exception as e:
        logger.warning("Failed to load stats cache: %s", e)
        return ""
