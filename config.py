"""
config.py — Load and validate all environment variables on startup.
Raises clear errors if required keys are missing.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(
            f"Missing required environment variable: {key}\n"
            f"Copy .env.example to .env and fill in all values."
        )
    return val


def _optional(key: str, default: str) -> str:
    return os.getenv(key, default)


# ── Claude ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = _require("ANTHROPIC_API_KEY")

# ── X (Twitter) ───────────────────────────────────────────────────────────────
X_API_KEY: str = _require("X_API_KEY")
X_API_SECRET: str = _require("X_API_SECRET")
X_ACCESS_TOKEN: str = _require("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET: str = _require("X_ACCESS_TOKEN_SECRET")

# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = _require("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: int = int(_require("TELEGRAM_CHAT_ID"))

# ── Tavily ────────────────────────────────────────────────────────────────────
TAVILY_API_KEY: str = _require("TAVILY_API_KEY")

# ── Scheduling ────────────────────────────────────────────────────────────────
SCHEDULE_START_UTC: int = int(_optional("SCHEDULE_START_UTC", "23"))
SCHEDULE_WINDOW_MINS: int = int(_optional("SCHEDULE_WINDOW_MINS", "120"))

# ── Approval timeout ──────────────────────────────────────────────────────────
APPROVAL_TIMEOUT_SECS: int = int(_optional("APPROVAL_TIMEOUT_SECS", "7200"))
