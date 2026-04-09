"""
prompts.py — System prompt and per-content-type prompt builders for Claude.

Two-layer prompt architecture:
  Layer 1 — Brand context:  .agents/social-media-context-sms.md
            Voice, audience, content pillars, example posts, anti-patterns.
            Created/updated via the social-media-context-sms skill.
  Layer 2 — GCode rules:    prompts/system_prompt.md
            X post format rules, content type rotation, CTA link, char limits,
            hashtag requirements, stat fabrication ban. GCode-specific only.

Edit .agents/social-media-context-sms.md to change brand voice or audience.
Edit prompts/system_prompt.md to change post format rules or content types.

Content types:
  1  HYPE / OPPORTUNITY       (25%)
  2  EDUCATIONAL / TIP        (25%)
  3  COMMUNITY / ENGAGEMENT   (20%)
  4  SOCIAL PROOF / RESULTS   (15%)
  5  MARKET COMMENTARY        (10%)
  6  MINDSET / PSYCHOLOGY      (5%)
"""

import logging
import os
from datetime import date

import context_loader

logger = logging.getLogger(__name__)

_PROMPT_FILE = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.md")

CONTENT_TYPES = {
    1: "HYPE/OPPORTUNITY",
    2: "EDUCATIONAL/TIP",
    3: "COMMUNITY/ENGAGEMENT",
    4: "SOCIAL PROOF/RESULTS",
    5: "MARKET COMMENTARY",
    6: "MINDSET/PSYCHOLOGY",
}

CONTENT_TYPE_WEIGHTS = {1: 25, 2: 25, 3: 20, 4: 15, 5: 10, 6: 5}


def _load_system_prompt() -> str:
    with open(_PROMPT_FILE, "r", encoding="utf-8") as f:
        rules = f.read()

    # Prepend brand context if available (layer 1 before layer 2)
    brand_context = context_loader.build_context_prefix()
    if brand_context:
        return brand_context + rules
    else:
        logger.warning(
            "Brand context file missing — running with rules only. "
            "Run /setup-brand-context in Claude Code for best results."
        )
        return rules


SYSTEM_PROMPT: str = _load_system_prompt()


def build_user_prompt(
    content_type: int,
    last_3_types: list[int],
    context_data: str = "",
) -> str:
    type_name = CONTENT_TYPES[content_type]
    avoided = ", ".join(CONTENT_TYPES[t] for t in last_3_types) if last_3_types else "none"
    today = date.today().strftime("%B %d, %Y")

    type_instructions = _type_instructions(content_type, context_data)

    return f"""Today's date: {today}

SELECTED CONTENT TYPE: {type_name} (Type {content_type})

RECENTLY USED TYPES (DO NOT COPY STYLE FROM THESE): {avoided}

{type_instructions}

Now generate exactly ONE X post following ALL system rules. Output ONLY the post text."""


def _type_instructions(content_type: int, context_data: str) -> str:
    if content_type == 1:
        return (
            "FOCUS: Market momentum, hidden edges, algo advantages. "
            "Sub-angles to pick from: breakthrough moments, competitive advantages, timing opportunities. "
            "Create urgency without hype. Highlight the edge algorithmic trading provides right now."
        )
    if content_type == 2:
        return (
            "FOCUS: Risk management tip, trading psychology, discipline, or actionable wisdom. "
            "Sub-angles: beginner mistakes, pro secrets, step-by-step insight. "
            "Educate the audience on one concrete, practical concept they can use today."
        )
    if content_type == 3:
        return (
            "FOCUS: Community engagement — spark conversation or debate. "
            "MUST include a direct question, poll option, or challenge to the audience. "
            "Sub-angles: controversial takes, personal experiences, predictions, 'this or that' choices. "
            "Make people want to reply."
        )
    if content_type == 4:
        context_section = (
            f"\nREAL PERFORMANCE DATA FROM trades.thegcodealgo.com (use this — do NOT fabricate):\n{context_data}\n"
            if context_data
            else "\nNo live data available this run — focus on transformation story/testimonial angle without specific stats.\n"
        )
        return (
            "FOCUS: Real bot performance, user transformation stories, case studies. "
            + context_section
            + "Sub-angles: before/after transformations, specific wins, anonymized user stories. "
            "NEVER fabricate stats. Only use provided data or general transformation narrative."
        )
    if content_type == 5:
        context_section = (
            f"\nCURRENT MARKET NEWS/CONTEXT (use for freshness):\n{context_data}\n"
            if context_data
            else "\nNo live market data available — use general market cycle knowledge.\n"
        )
        return (
            "FOCUS: Current crypto trends, market conditions, price action reactions. "
            + context_section
            + "Sub-angles: contrarian views, hidden patterns, future implications. "
            "Reference real market conditions if data provided above."
        )
    if content_type == 6:
        return (
            "FOCUS: Emotional control, patience, systematic thinking, mental models. "
            "Sub-angles: behavioral insights, discipline frameworks, overcoming FOMO/fear. "
            "Help traders understand the psychological edge of using an algo."
        )
    return ""
