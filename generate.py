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
CHAR_LIMIT = 280  # X hard limit (system prompt says 300 for safety margin — enforce 280 here)

_EXAMPLES_FILE = os.path.join(os.path.dirname(__file__), "data", "example_posts.json")

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
    # For Social Proof, scraper.py handles its own cache fallback (stats.json).
    # If context_data is still empty here, both live scrape and cache failed.
    if content_type == 4 and not context_data:
        logger.warning(
            "Type 4 (Social Proof): scraper returned no data and cache is empty. "
            "Post will use narrative angle. Check trades.thegcodealgo.com is reachable."
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

    post_text = _clean(message.content[0].text.strip())
    logger.info("Generated post (%d chars): %s", len(post_text), post_text[:80])

    # If over limit, ask Claude to shorten it (one retry)
    if len(post_text) > CHAR_LIMIT:
        logger.warning("Post is %d chars (limit %d) — asking Claude to shorten.", len(post_text), CHAR_LIMIT)
        shorten_messages = messages + [
            {"role": "assistant", "content": post_text},
            {"role": "user", "content": f"That post is {len(post_text)} characters. Shorten it to strictly under {CHAR_LIMIT} characters while keeping the hook, CTA link, and hashtags. Output only the shortened post."},
        ]
        retry = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=0.5,
            system=SYSTEM_PROMPT,
            messages=shorten_messages,
        )
        post_text = _clean(retry.content[0].text.strip())
        logger.info("Shortened post (%d chars): %s", len(post_text), post_text[:80])

    return post_text


def _clean(text: str) -> str:
    """Remove patterns that make posts sound AI-generated."""
    # Hard ban on em dashes — replace with comma or nothing depending on context
    text = text.replace(" — ", ", ")
    text = text.replace("— ", "")
    text = text.replace(" —", "")
    text = text.replace("—", ", ")
    return text


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


