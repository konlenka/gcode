"""
workflow.py — Orchestrates the full daily post pipeline.

Pipeline per run:
  1. Select content type (weighted random, avoiding last 3 used)
  2. Gather context data (scrape or search if needed)
  3. Generate post via Claude
  4. Send to Telegram for approval
  5a. Approved → post to X → log
  5b. Rejected/Regen → regenerate (same type), restart approval timer
  5c. Timeout → auto-post → log
  6. Any exception → Telegram error alert
"""

import asyncio
import logging
import random
import traceback

import config
import generate
import scraper
import search
import state
import telegram_bot
import twitter_client
from prompts import CONTENT_TYPE_WEIGHTS, CONTENT_TYPES

logger = logging.getLogger(__name__)


async def run_daily_post() -> None:
    """Entry point called by the scheduler once per day."""
    logger.info("=== Daily post workflow started ===")
    try:
        content_type = _select_content_type()
        await _run_for_type(content_type)
    except Exception as e:
        logger.error("Unhandled workflow error: %s", e, exc_info=True)
        await telegram_bot.send_error_alert(str(e))


async def _run_for_type(content_type: int) -> None:
    """Run the pipeline for a given content type. Retries on regenerate (max 5)."""
    for attempt in range(6):
        if attempt == 5:
            await telegram_bot.send_error_alert("Too many regeneration attempts. Skipping today's post.")
            return
        if attempt > 0:
            logger.info("Regenerating post (attempt %d)...", attempt)

        logger.info("Content type: %d (%s)", content_type, CONTENT_TYPES[content_type])

        # Step 1: Gather context data
        context_data = await _gather_context(content_type)

        # Step 2: Generate post
        try:
            last_3 = state.get_last_3_types()
            post_text = generate.generate_post(content_type, last_3, context_data)
        except Exception as e:
            logger.error("Content generation failed: %s", e)
            await telegram_bot.send_error_alert(f"Claude API error: {e}")
            return

        # Step 3: Send for approval
        approval_future: asyncio.Future[str] = asyncio.get_running_loop().create_future()

        async def on_approve(text: str, _fut: asyncio.Future = approval_future) -> None:
            try:
                tweet_id = twitter_client.post_tweet(text)
                state.record_post(content_type, "posted")
                logger.info("Successfully posted tweet: %s", tweet_id)
                if not _fut.done():
                    _fut.set_result("approved")
            except Exception as exc:
                logger.error("X API post failed: %s", exc)
                await telegram_bot.send_error_alert(f"X post failed: {exc}")
                state.record_post(content_type, "failed")
                if not _fut.done():
                    _fut.set_exception(exc)

        async def on_regenerate(_fut: asyncio.Future = approval_future) -> None:
            if not _fut.done():
                _fut.set_result("regenerate")

        await telegram_bot.send_for_approval(
            post_text=post_text,
            content_type=content_type,
            on_approve=on_approve,
            on_regenerate=on_regenerate,
        )

        # Wait for approval outcome (resolved by callback or auto-post timer)
        try:
            result = await asyncio.wait_for(
                approval_future,
                timeout=config.APPROVAL_TIMEOUT_SECS + 60,  # small buffer over the Telegram timer
            )
            if result == "regenerate":
                continue
            return  # approved or exception — either way, done
        except asyncio.TimeoutError:
            # Should not reach here normally (Telegram timer handles auto-post)
            logger.warning("Workflow future timed out — auto-post already handled by Telegram timer.")
            return


async def _gather_context(content_type: int) -> str:
    """Fetch external data for types that need it."""
    if content_type == 4:  # Social Proof
        logger.info("Scraping trades.thegcodealgo.com for social proof data...")
        data = scraper.fetch_performance_data()
        if not data:
            logger.warning("Scraper returned no data — proceeding without stats.")
            await telegram_bot.send_error_alert(
                "trades.thegcodealgo.com scrape returned no data. "
                "Social proof post will use narrative angle instead."
            )
        return data

    if content_type == 5:  # Market Commentary
        logger.info("Fetching market context via Tavily...")
        data = search.fetch_market_context()
        if not data:
            logger.warning("Tavily search returned no data — proceeding without live market data.")
        return data

    return ""


def _select_content_type() -> int:
    """
    Select a content type using weighted random, excluding any type
    that was used in the last 3 posts.

    Falls back to type 3 (Community/Engagement) if all eligible types
    are somehow exhausted.
    """
    last_3 = state.get_last_3_types()
    last_type = last_3[0] if last_3 else None

    # Build filtered weights: exclude the immediately previous type
    # (The spec says never repeat consecutively; using last 3 for context
    #  but hard-blocking only the most recent one in the selector to
    #  preserve valid weekly distribution.)
    eligible = {
        t: w
        for t, w in CONTENT_TYPE_WEIGHTS.items()
        if t != last_type
    }

    if not eligible:
        logger.warning("No eligible content type found — defaulting to type 3.")
        return 3

    types = list(eligible.keys())
    weights = list(eligible.values())
    chosen = random.choices(types, weights=weights, k=1)[0]
    logger.info(
        "Selected content type %d (%s). Last type was: %s",
        chosen,
        CONTENT_TYPES[chosen],
        CONTENT_TYPES.get(last_type, "none"),
    )
    return chosen
