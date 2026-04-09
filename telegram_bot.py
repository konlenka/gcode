"""
telegram_bot.py — Telegram approval flow for X post drafts.

Responsibilities:
  - Send draft post to user with Approve / Reject / Regenerate inline buttons
  - Start a 2-hour auto-post timer (cancellable on response)
  - Call back into workflow on each action
  - Send error alerts immediately

Uses python-telegram-bot v20+ (async/await).
"""

import asyncio
import logging
import traceback
from typing import Callable, Awaitable

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

import config
from prompts import CONTENT_TYPES

logger = logging.getLogger(__name__)

# Callback data constants
CB_APPROVE = "approve"
CB_REJECT = "reject"
CB_REGEN = "regen"

# Global application instance (initialised once in main.py)
_app: Application | None = None

# Pending approval state: keyed by message_id
_pending: dict[int, dict] = {}


def get_application() -> Application:
    global _app
    if _app is None:
        _app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        _app.add_handler(CallbackQueryHandler(_handle_callback))
    return _app


async def send_for_approval(
    post_text: str,
    content_type: int,
    on_approve: Callable[[str], Awaitable[None]],
    on_regenerate: Callable[[], Awaitable[None]],
) -> None:
    """
    Send the draft post to Telegram for approval.

    Args:
        post_text:      The generated X post draft.
        content_type:   Integer 1–6 content type label.
        on_approve:     Async callback(post_text) → posts to X.
        on_regenerate:  Async callback() → regenerates a new draft.
    """
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    type_name = CONTENT_TYPES.get(content_type, f"Type {content_type}")
    char_count = len(post_text)

    message_text = (
        f"📝 *GCode Algo — Daily X Post Draft*\n"
        f"Type: {type_name} | {char_count} chars\n\n"
        f"```\n{post_text}\n```\n\n"
        f"_Auto-posts in 2 hours if no response._"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve & Post", callback_data=CB_APPROVE),
            InlineKeyboardButton("❌ Reject & Regen", callback_data=CB_REJECT),
        ],
        [
            InlineKeyboardButton("🔄 Regenerate (keep type)", callback_data=CB_REGEN),
        ],
    ])

    sent = await bot.send_message(
        chat_id=config.TELEGRAM_CHAT_ID,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

    # Store pending state keyed by message id
    _pending[sent.message_id] = {
        "post_text": post_text,
        "on_approve": on_approve,
        "on_regenerate": on_regenerate,
        "timer_task": None,
    }

    # Start 2-hour auto-post timer
    timer = asyncio.create_task(
        _auto_post_timer(sent.message_id, post_text, on_approve)
    )
    _pending[sent.message_id]["timer_task"] = timer

    logger.info("Sent approval request to Telegram (msg_id=%d)", sent.message_id)


async def _auto_post_timer(
    message_id: int,
    post_text: str,
    on_approve: Callable[[str], Awaitable[None]],
) -> None:
    """Wait APPROVAL_TIMEOUT_SECS then auto-post if still pending."""
    await asyncio.sleep(config.APPROVAL_TIMEOUT_SECS)

    if message_id not in _pending:
        return  # Already handled

    logger.info("Approval timeout reached — auto-posting (msg_id=%d)", message_id)
    _pending.pop(message_id, None)

    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    try:
        await on_approve(post_text)
        await bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text="⏰ Auto-posted to X (no response within timeout window).",
        )
    except Exception as e:
        await send_error_alert(f"Auto-post failed: {e}")


async def _handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    message_id = query.message.message_id
    state = _pending.pop(message_id, None)

    if state is None:
        await query.edit_message_text("⚠️ This post was already handled.")
        return

    # Cancel the auto-post timer
    timer = state.get("timer_task")
    if timer and not timer.done():
        timer.cancel()

    data = query.data

    if data == CB_APPROVE:
        await query.edit_message_text("✅ Approved! Posting to X now...")
        try:
            await state["on_approve"](state["post_text"])
        except Exception as e:
            await send_error_alert(f"Post to X failed after approval: {e}")

    elif data in (CB_REJECT, CB_REGEN):
        label = "Rejected" if data == CB_REJECT else "Regenerating"
        await query.edit_message_text(f"🔄 {label} — generating a new draft...")
        try:
            await state["on_regenerate"]()
        except Exception as e:
            await send_error_alert(f"Regeneration failed: {e}")


async def send_error_alert(error_msg: str) -> None:
    """Send an immediate error notification to Telegram."""
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    raw_tb = traceback.format_exc()
    if raw_tb and raw_tb.strip() not in ("NoneType: None", "None"):
        lines = raw_tb.splitlines()
        # Keep first line ("Traceback...") + last 12 lines (exception + immediate frames)
        if len(lines) > 13:
            tb_snippet = "\n".join(lines[:1] + ["  ..."] + lines[-12:])
        else:
            tb_snippet = raw_tb
        if len(tb_snippet) > 900:
            tb_snippet = tb_snippet[-900:]
    else:
        tb_snippet = "(no traceback)"
    text = (
        f"🚨 *GCode Bot Error*\n\n"
        f"`{error_msg}`\n\n"
        f"```\n{tb_snippet}\n```"
    )
    try:
        await bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=text,
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error("Failed to send error alert to Telegram: %s", e)
