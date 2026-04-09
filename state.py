"""
state.py — SQLite wrapper for minimal content-type state tracking.

Tables:
  post_log(id, content_type, posted_at, status)

Functions:
  get_last_3_types()         → list[int]
  record_post(type, status)  → None
  init_db()                  → None
"""

import sqlite3
import os
from contextlib import closing
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "state.db")


def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS post_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type INTEGER NOT NULL,
                posted_at    TEXT    NOT NULL,
                status       TEXT    NOT NULL
            )
        """)
        conn.commit()


def get_last_3_types() -> list[int]:
    """Return the content types of the last 3 posts, most recent first."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        rows = conn.execute(
            "SELECT content_type FROM post_log ORDER BY id DESC LIMIT 3"
        ).fetchall()
    return [r[0] for r in rows]


def record_post(content_type: int, status: str) -> None:
    """Log a post attempt with its content type and status."""
    now = datetime.now(timezone.utc).isoformat()
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT INTO post_log (content_type, posted_at, status) VALUES (?, ?, ?)",
            (content_type, now, status),
        )
        conn.commit()
