import pandas as pd
import requests

# CFTC Public Reporting Environment Socrata-style endpoint for disaggregated combined report.
# You may need to tune field names depending on selected COT report.
CFTC_DISAGG_COMBINED = 'https://publicreporting.cftc.gov/resource/kh3c-gbw2.json'


def fetch_cot_crude(limit: int = 1000) -> pd.DataFrame:
    params = {
        '$limit': limit,
        '$order': 'report_date_as_yyyy_mm_dd DESC',
        # Contract names can vary. Keep broad; filter later.
        '$where': "upper(contract_market_name) like '%CRUDE OIL%'"
    }
    r = requests.get(CFTC_DISAGG_COMBINED, params=params, timeout=30)
    r.raise_for_status()
    rows = r.json()
    out = []
    for row in rows:
        ts = row.get('report_date_as_yyyy_mm_dd')
        if not ts:
            continue
        long_val = _to_float(row.get('m_money_positions_long_all'))
        short_val = _to_float(row.get('m_money_positions_short_all'))
        oi = _to_float(row.get('open_interest_all'))
        if long_val is None or short_val is None:
            continue
        out.append({
            'timestamp': pd.to_datetime(ts, utc=True),
            'source': 'CFTC_COT',
            'series_name': 'managed_money_net_crude',
            'raw_value': long_val - short_val,
            'metadata': {'long': long_val, 'short': short_val, 'open_interest': oi, 'contract': row.get('contract_market_name')}
        })
    return pd.DataFrame(out).sort_values('timestamp')


def _to_float(x):
    try:
        return float(x)
    except Exception:
        return None
