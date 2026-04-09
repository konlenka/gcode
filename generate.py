"""
generate.py — Call Claude API to generate one X post draft.

Uses claude-sonnet-4-6 with temperature 0.9 for creative variety.
Injects up to 3 few-shot example posts from data/example_posts.json
to anchor Claude to the exact voice and style you want.

Returns the post text as a plain string (≤300 chars, line breaks as \n).
"""

import json
import logging
import os

import anthropic

import config
import context_loader
from prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 400
TEMPERATURE = 0.9

_EXAMPLES_FILE = os.path.join(os.path.dirname(__file__), "data", "example_posts.json")
_STATS_FILE = os.path.join(os.path.dirname(__file__), "data", "stats.json")

MAX_EXAMPLES = 3  # Number of few-shot examples to inject per call


def generate_post(
    content_type: int,
    last_3_types: list[int],
    context_data: str = "",
) -> str:
    """
    Generate a single X post draft via Claude.

    Args:
        content_type:  Integer 1–6 representing the content type.
        last_3_types:  List of last 3 used content type integers (anti-repetition).
        context_data:  Scraped or searched context string (optional).
                       For type 4 (Social Proof), if empty, auto-loads data/stats.json.

    Returns:
        str: The post text ready to publish.
    """
    # For Social Proof, fall back to local stats.json if no scraped data
    if content_type == 4 and not context_data:
        context_data = _load_local_stats()
        if not context_data:
            logger.warning(
                "Type 4 (Social Proof): both scraper and stats.json returned no data. "
                "Post will use narrative angle — update data/stats.json with real figures."
            )

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    user_prompt = build_user_prompt(content_type, last_3_types, context_data)

    # Build message history with few-shot examples
    messages = _build_messages(user_prompt)

    logger.info("Generating post — content type %d (%d examples injected)", content_type, len(messages) // 2)

    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    post_text = message.content[0].text.strip()
    logger.info("Generated post (%d chars): %s", len(post_text), post_text[:80])
    return post_text


def _build_messages(user_prompt: str) -> list[dict]:
    """
    Build the messages list with few-shot examples prepended.

    Sources (merged, de-duplicated):
      1. data/example_posts.json  — manually curated JSON examples
      2. .agents/social-media-context-sms.md — examples from brand context file

    Each example becomes a user/assistant exchange so Claude sees ideal
    outputs before being asked to generate a new one.
    """
    messages: list[dict] = []

    # Merge examples from both sources, de-duplicate by text
    json_examples = [e["text"] for e in _load_examples() if e.get("text")]
    context_examples = context_loader.extract_examples()
    seen: set[str] = set()
    all_examples: list[str] = []
    for text in context_examples + json_examples:
        if text and text.strip() and text not in seen:
            seen.add(text)
            all_examples.append(text)

    for text in all_examples[:MAX_EXAMPLES]:
        messages.append({
            "role": "user",
            "content": "Generate one GCode Algo X post now.",
        })
        messages.append({
            "role": "assistant",
            "content": text,
        })

    # Final real request
    messages.append({"role": "user", "content": user_prompt})
    return messages


def _load_examples() -> list[dict]:
    """Load approved example posts from data/example_posts.json."""
    try:
        with open(_EXAMPLES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        examples = [e for e in data.get("examples", []) if e.get("text")]
        return examples
    except Exception as e:
        logger.debug("Could not load example posts: %s", e)
        return []


def _load_local_stats() -> str:
    """
    Load manually maintained stats from data/stats.json as fallback
    for Social Proof posts when the live scraper returns nothing.
    """
    try:
        with open(_STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        lines: list[str] = []
        overall = data.get("overall", {})
        if overall.get("win_rate_pct"):
            lines.append(f"Overall win rate: {overall['win_rate_pct']}%")
        if overall.get("total_signals"):
            lines.append(f"Total signals: {overall['total_signals']}")
        if overall.get("avg_profit_per_trade_pct"):
            lines.append(f"Avg profit per trade: {overall['avg_profit_per_trade_pct']}%")
        if overall.get("best_month_return_pct"):
            lines.append(f"Best month return: {overall['best_month_return_pct']}%")
        if overall.get("months_live"):
            lines.append(f"Live for: {overall['months_live']} months")

        for algo in data.get("algos", []):
            if algo.get("win_rate_pct") and algo.get("name"):
                lines.append(
                    f"{algo['name']}: {algo['win_rate_pct']}% win rate"
                    + (f", {algo['total_trades']} trades" if algo.get("total_trades") else "")
                )

        for h in data.get("recent_highlights", []):
            if h.get("verified") and h.get("description"):
                lines.append(f"Recent: {h['description']}")

        return "\n".join(lines) if lines else ""
    except Exception as e:
        logger.debug("Could not load local stats: %s", e)
        return ""
