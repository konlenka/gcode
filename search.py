"""
search.py — Tavily web search for current crypto market context.

Used only for Type 5 (Market Commentary) posts to inject fresh,
real-world market data into the Claude prompt.

Returns plain-text news snippets, or "" on failure.
"""

import logging
from datetime import date
from tavily import TavilyClient
import config

logger = logging.getLogger(__name__)


def fetch_market_context() -> str:
    """
    Search for current crypto market conditions and news.

    Returns:
        str: Top 3 news snippets as plain text, or "" on failure.
    """
    try:
        client = TavilyClient(api_key=config.TAVILY_API_KEY)
        today = date.today().strftime("%B %d, %Y")
        query = (
            f"crypto market Bitcoin BTC altcoin price movement analysis {today}"
        )
        result = client.search(
            query=query,
            search_depth="basic",
            max_results=3,
            include_answer=True,
        )
        return _format(result)
    except Exception as e:
        logger.warning("Tavily search failed: %s", e)
        return ""


def _format(result: dict) -> str:
    parts: list[str] = []

    if result.get("answer"):
        parts.append(f"Summary: {result['answer']}")

    for item in result.get("results", [])[:3]:
        title = item.get("title", "")
        content = item.get("content", "")
        if title or content:
            snippet = f"• {title}: {content[:200]}" if title else f"• {content[:200]}"
            parts.append(snippet)

    return "\n".join(parts)
