"""
scraper.py — Scrape real performance data from trades.thegcodealgo.com.

Used for Type 4 (Social Proof) posts. Returns a formatted string of
real algo performance data to pass into the Claude prompt.

Returns empty string on failure (caller handles fallback).
"""

import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TRADES_URL = "https://www.trades.thegcodealgo.com"
TIMEOUT = 15


def fetch_performance_data() -> str:
    """
    Scrape trades.thegcodealgo.com and return a plain-text summary
    of available algo performance stats.

    Returns:
        str: Formatted performance data, or "" on failure.
    """
    try:
        response = requests.get(TRADES_URL, timeout=TIMEOUT, headers=_headers())
        response.raise_for_status()
        return _parse(response.text)
    except requests.RequestException as e:
        logger.warning("Scraper request failed: %s", e)
        return ""
    except Exception as e:
        logger.warning("Scraper parse failed: %s", e)
        return ""


def _parse(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    lines: list[str] = []

    # Remove scripts/styles to reduce noise
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Collect text from elements likely to contain stats
    # (percentages, win rates, trade counts, profit figures)
    stat_keywords = [
        "win", "rate", "profit", "trade", "return", "signal",
        "accuracy", "drawdown", "bot", "algo", "%", "pnl",
    ]

    seen: set[str] = set()
    for element in soup.find_all(["p", "h1", "h2", "h3", "h4", "li", "td", "span", "div"]):
        text = element.get_text(separator=" ", strip=True)
        if len(text) < 5 or len(text) > 300:
            continue
        text_lower = text.lower()
        if any(kw in text_lower for kw in stat_keywords):
            if text not in seen:
                seen.add(text)
                lines.append(text)
        if len(lines) >= 20:
            break

    if not lines:
        return ""

    return "\n".join(lines)


def _headers() -> dict:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
