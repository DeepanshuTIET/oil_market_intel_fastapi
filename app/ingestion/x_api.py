from datetime import datetime, timezone
import requests
import pandas as pd

from app.core.config import settings


X_RECENT_SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"


OIL_QUERY = (
    '(oil OR crude OR WTI OR Brent OR OPEC OR "crude oil" OR "oil prices") '
    'lang:en -is:retweet'
)


def classify_x_category(text: str) -> str:
    t = text.lower()

    if any(x in t for x in ["opec", "opec+", "production cut", "output cut", "quota"]):
        return "x_opec_policy"

    if any(x in t for x in ["war", "attack", "sanction", "missile", "red sea", "strait", "pipeline"]):
        return "x_geopolitical_supply_risk"

    if any(x in t for x in ["inventory", "eia", "stockpile", "draw", "build"]):
        return "x_inventory_event"

    if any(x in t for x in ["demand", "china", "recession", "growth", "pmi"]):
        return "x_macro_demand"

    return "x_general_oil"


def simple_x_sentiment(text: str) -> float:
    t = text.lower()

    bullish_terms = [
        "cut",
        "draw",
        "shortage",
        "disruption",
        "sanction",
        "attack",
        "risk premium",
        "tight market",
        "bullish",
    ]

    bearish_terms = [
        "build",
        "surplus",
        "weak demand",
        "recession",
        "increase output",
        "bearish",
        "oversupply",
    ]

    score = 0

    for term in bullish_terms:
        if term in t:
            score += 1

    for term in bearish_terms:
        if term in t:
            score -= 1

    return max(-1.0, min(1.0, score / 3.0))


def fetch_x_oil_events(
    query: str = OIL_QUERY,
    max_results: int = 50,
) -> pd.DataFrame:
    """
    Fetch recent oil-related posts from X API v2 recent search.

    Output schema matches raw_observations:
    timestamp, source, series_name, raw_value, metadata
    """

    if not settings.X_BEARER_TOKEN:
        raise ValueError("X_BEARER_TOKEN is required")

    headers = {
        "Authorization": f"Bearer {settings.X_BEARER_TOKEN}",
    }

    params = {
        "query": query,
        "max_results": max(10, min(max_results, 100)),
        "tweet.fields": "created_at,public_metrics,lang",
    }

    response = requests.get(
        X_RECENT_SEARCH_URL,
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()
    tweets = payload.get("data", [])

    rows = []

    for tweet in tweets:
        text = tweet.get("text", "")
        created_at = tweet.get("created_at")

        if not text or not created_at:
            continue

        category = classify_x_category(text)
        sentiment = simple_x_sentiment(text)

        metrics = tweet.get("public_metrics", {}) or {}

        likes = metrics.get("like_count", 0) or 0
        retweets = metrics.get("retweet_count", 0) or 0
        replies = metrics.get("reply_count", 0) or 0

        engagement = likes + retweets + replies

        # Bounded impact score.
        impact = sentiment * min(1.0, 0.2 + engagement / 1000)

        rows.append(
            {
                "timestamp": pd.to_datetime(created_at, utc=True),
                "source": "X",
                "series_name": category,
                "raw_value": float(impact),
                "metadata": {
                    "tweet_id": tweet.get("id"),
                    "text": text,
                    "sentiment": sentiment,
                    "engagement": engagement,
                    "metrics": metrics,
                },
            }
        )

    return pd.DataFrame(rows).sort_values("timestamp")