"""
main.py — Entry point for the GCode Algo X Auto-Poster.

Starts:
  1. SQLite database (creates tables if new)
  2. APScheduler (daily random trigger within configured UTC window)
  3. Telegram bot (long-polling for approval callbacks)

Usage:
  python main.py              # Run the bot (keeps running)
  python main.py --now        # Trigger one post immediately (for testing)
"""

import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def _run_bot() -> None:
    # Late imports so logging is configured first and .env is loaded
    import config  # validates all env vars on import — fails fast if missing
    import state
    import scheduler
    import workflow
    from telegram_bot import get_application

    # Init DB
    state.init_db()
    logger.info("SQLite state DB ready.")

    # Start scheduler
    sched = scheduler.start(workflow.run_daily_post)
    logger.info(
        "Scheduler running. Window: %02d:00 UTC + %d mins.",
        config.SCHEDULE_START_UTC,
        config.SCHEDULE_WINDOW_MINS,
    )

    # Start Telegram bot (long-polling — blocks until interrupted)
    app = get_application()
    logger.info("Telegram bot starting (long-polling)...")
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)

        logger.info("GCode X Bot is live. Waiting for scheduled posts...")
        try:
            # Keep alive until Ctrl+C
            while True:
                await asyncio.sleep(60)
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Shutdown requested.")
        finally:
            await app.updater.stop()
            await app.stop()
            sched.shutdown(wait=False)
            logger.info("Bot stopped cleanly.")


async def _run_now() -> None:
    """Trigger a single post immediately (for testing/manual use)."""
    import config  # noqa: F401 — validates env
    import state
    import workflow

    state.init_db()

    from telegram_bot import get_application
    app = get_application()
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)

        logger.info("Running one post immediately (--now mode)...")
        await workflow.run_daily_post()

        # Keep alive long enough for approval callbacks
        import config as cfg
        logger.info("Waiting up to %d seconds for your Telegram response...", cfg.APPROVAL_TIMEOUT_SECS + 120)
        try:
            await asyncio.sleep(cfg.APPROVAL_TIMEOUT_SECS + 120)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            await app.updater.stop()
            await app.stop()


if __name__ == "__main__":
    if "--now" in sys.argv:
        asyncio.run(_run_now())
    else:
        asyncio.run(_run_bot())
