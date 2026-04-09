"""
twitter_client.py — Post a tweet via Tweepy v2 (X API Free tier).

Requires OAuth 1.0a credentials (all 4 keys from developer.twitter.com).
Free tier: write-only, 1,500 tweets/month — more than sufficient.
"""

import logging
import tweepy
import config

logger = logging.getLogger(__name__)


def post_tweet(text: str) -> str:
    """
    Post a tweet and return the tweet ID.

    Args:
        text: The tweet text (pipeline enforces ≤300 chars; X standard is 280).

    Returns:
        str: The posted tweet ID.

    Raises:
        tweepy.TweepyException: On API error.
    """
    client = _client()
    response = client.create_tweet(text=text)
    tweet_id = str(response.data["id"])
    logger.info("Posted tweet ID: %s", tweet_id)
    return tweet_id


def _client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=config.X_API_KEY,
        consumer_secret=config.X_API_SECRET,
        access_token=config.X_ACCESS_TOKEN,
        access_token_secret=config.X_ACCESS_TOKEN_SECRET,
    )
