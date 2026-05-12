from datetime import datetime, timezone
import pandas as pd
import requests
from app.core.config import settings

CATEGORY_KEYWORDS = {
    'geopolitical_supply_risk': ['war', 'attack', 'sanction', 'missile', 'red sea', 'strait', 'pipeline'],
    'opec_policy': ['opec', 'opec+', 'quota', 'production cut', 'output cut'],
    'macro_growth': ['recession', 'growth', 'china demand', 'manufacturing', 'pmi'],
    'usd_rates': ['federal reserve', 'rates', 'dollar', 'inflation'],
    'shipping_disruption': ['tanker', 'shipping', 'canal', 'port', 'freight'],
}


def classify_category(text: str) -> str:
    t = text.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(k in t for k in kws):
            return cat
    return 'general_oil_news'


def simple_sentiment(text: str) -> float:
    t = text.lower()
    bullish = ['cut', 'draw', 'shortage', 'disruption', 'sanction', 'attack', 'strong demand']
    bearish = ['build', 'surplus', 'weak demand', 'recession', 'increase output', 'ceasefire']
    score = sum(w in t for w in bullish) - sum(w in t for w in bearish)
    return max(-1.0, min(1.0, score / 3.0))


def fetch_news(query: str = 'crude oil OR WTI OR Brent', page_size: int = 50) -> pd.DataFrame:
    if not settings.NEWS_API_KEY:
        return pd.DataFrame()
    url = 'https://newsapi.org/v2/everything'
    params = {'q': query, 'language': 'en', 'pageSize': page_size, 'sortBy': 'publishedAt', 'apiKey': settings.NEWS_API_KEY}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    articles = r.json().get('articles', [])
    rows = []
    for a in articles:
        text = ' '.join([a.get('title') or '', a.get('description') or ''])
        if not text.strip():
            continue
        category = classify_category(text)
        sentiment = simple_sentiment(text)
        relevance = 1.0 if any(k in text.lower() for k in ['oil', 'crude', 'wti', 'brent', 'opec']) else 0.5
        impact = sentiment * relevance
        rows.append({
            'timestamp': pd.to_datetime(a.get('publishedAt'), utc=True),
            'source': 'NEWS',
            'series_name': f'news_{category}',
            'raw_value': impact,
            'metadata': {'title': a.get('title'), 'url': a.get('url'), 'category': category, 'sentiment': sentiment, 'relevance': relevance}
        })
    return pd.DataFrame(rows).sort_values('timestamp')
