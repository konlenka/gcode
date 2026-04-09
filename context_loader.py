"""
context_loader.py — Load the brand context file created by social-media-context-sms.

The context file at .agents/social-media-context-sms.md is the single source of truth
for GCode Algo's voice, audience, content pillars, anti-patterns, and example posts.

All Claude API calls in the pipeline inject this context so generated posts are
always on-brand — without duplicating that information in the system prompt.
"""

import logging
import os
import re

logger = logging.getLogger(__name__)

CONTEXT_FILE = os.path.join(
    os.path.dirname(__file__), ".agents", "social-media-context-sms.md"
)


def load_brand_context() -> str:
    """
    Load the full brand context file as a string.

    Returns:
        str: Full context markdown, or "" if the file doesn't exist.
    """
    if not os.path.exists(CONTEXT_FILE):
        logger.warning(
            "Brand context file not found at %s. "
            "Run /setup-brand-context in Claude Code to create it.",
            CONTEXT_FILE,
        )
        return ""

    with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    logger.debug("Loaded brand context (%d chars)", len(content))
    return content


def extract_examples() -> list[str]:
    """
    Parse example posts from the brand context file.

    Returns:
        list[str]: List of verbatim post texts from the Example Posts section.
    """
    context = load_brand_context()
    if not context:
        return []

    examples: list[str] = []

    # Find the Example Posts section
    section_match = re.search(
        r"## Example Posts(.*?)(?=\n## |\Z)", context, re.DOTALL
    )
    if not section_match:
        return []

    section = section_match.group(1)

    # Extract each code block (verbatim post text); handle optional language tags e.g. ```text
    code_blocks = re.findall(r"```(?:\w+)?\n(.*?)\n```", section, re.DOTALL)
    for block in code_blocks:
        text = block.strip()
        if text and "Note:" not in text[:50]:
            examples.append(text)

    return examples


def build_context_prefix() -> str:
    """
    Return a formatted prefix to prepend to the system prompt.
    Contains brand identity, voice, audience, and anti-patterns — the
    sections most relevant to generation quality.

    Returns:
        str: Formatted context prefix, or "" if file missing.
    """
    context = load_brand_context()
    if not context:
        return ""

    return (
        "=== BRAND CONTEXT (source of truth — follow this exactly) ===\n\n"
        + context
        + "\n\n=== END BRAND CONTEXT ===\n\n"
    )
