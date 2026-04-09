"""
scheduler.py — Daily random trigger using APScheduler.

Schedules one job per day at a random minute within the configured UTC window.
Default window: 23:00–01:00 UTC (= 6–8pm US Eastern / 9–11am Sydney).

The job fires workflow.run_daily_post() each day.
"""

import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Callable, Coroutine, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

import config

logger = logging.getLogger(__name__)


def start(job_fn: Callable[[], Coroutine[Any, Any, None]]) -> AsyncIOScheduler:
    """
    Start the APScheduler and schedule the first daily job.

    Args:
        job_fn: Async function to call each day (workflow.run_daily_post).

    Returns:
        The running AsyncIOScheduler instance.
    """
    scheduler = AsyncIOScheduler(timezone="UTC")
    _schedule_next(scheduler, job_fn)
    scheduler.start()
    logger.info("Scheduler started.")
    return scheduler


def _schedule_next(
    scheduler: AsyncIOScheduler,
    job_fn: Callable[[], Coroutine[Any, Any, None]],
) -> None:
    """Schedule the next daily post at a random time within the window."""
    fire_at = _next_fire_time()
    logger.info("Next post scheduled at: %s UTC", fire_at.isoformat())

    async def _wrapper():
        await job_fn()
        # After each run, schedule the next day's post
        _schedule_next(scheduler, job_fn)

    scheduler.add_job(
        _wrapper,
        trigger=DateTrigger(run_date=fire_at),
        id="daily_post",
        replace_existing=True,
    )


def _next_fire_time() -> datetime:
    """
    Calculate the next fire time:
    - Random minute offset within SCHEDULE_WINDOW_MINS
    - Starting from today's SCHEDULE_START_UTC hour
    - If that time is already past for today, schedule for tomorrow
    """
    now = datetime.now(timezone.utc)
    start_hour = config.SCHEDULE_START_UTC
    window_mins = config.SCHEDULE_WINDOW_MINS
    offset_mins = random.randint(0, window_mins - 1)

    # Build candidate time today
    candidate = now.replace(
        hour=start_hour % 24,
        minute=0,
        second=0,
        microsecond=0,
    ) + timedelta(minutes=offset_mins)

    # If window spans midnight (e.g. 23:00 + 120min = up to 01:00 next day)
    # the offset may push into next calendar day — that's fine, timedelta handles it.

    # If candidate is in the past, add 24 hours
    if candidate <= now:
        candidate += timedelta(hours=24)

    return candidate
