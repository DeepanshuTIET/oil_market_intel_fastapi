import requests
from app.core.config import settings


def send_teams_alert(payload: dict) -> dict:
    if not settings.TEAMS_WEBHOOK_URL:
        return {'sent': False, 'reason': 'TEAMS_WEBHOOK_URL not configured'}
    text = (
        f"Oil Signal: {payload.get('instrument')} {payload.get('horizon')}\n"
        f"Signal: {payload.get('signal')} | P(up): {payload.get('probability_up'):.2f} | "
        f"Confidence: {payload.get('confidence'):.2f} | Regime: {payload.get('regime')}"
    )
    r = requests.post(settings.TEAMS_WEBHOOK_URL, json={'text': text}, timeout=20)
    return {'sent': r.ok, 'status_code': r.status_code, 'text': r.text[:300]}
