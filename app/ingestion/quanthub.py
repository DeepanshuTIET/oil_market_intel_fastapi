import logging
from typing import Any
from datetime import datetime, timezone

import requests
import pandas as pd

from app.core.config import settings


logger = logging.getLogger(__name__)


class QuantHubClient:
    """
    QuantHub client using generated username/password.

    Flow:
    1. Get generated credentials once from:
       https://qh-api.corp.hertshtengroup.com/api/auth/

    2. Generate token:
       POST https://qh-api.corp.hertshtengroup.com/api/token/
       JSON:
       {
         "username": "...",
         "password": "..."
       }

    3. Use:
       Authorization: Bearer <access_token>
    """

    def __init__(self):
        self.base_url = settings.QUANTHUB_BASE_URL.rstrip("/")
        self.username = settings.QUANTHUB_USERNAME
        self.password = settings.QUANTHUB_PASSWORD
        self.access_token = settings.QUANTHUB_ACCESS_TOKEN
        self.refresh_token = settings.QUANTHUB_REFRESH_TOKEN
        self.timeout = 45

    def _url(self, path: str) -> str:
        return self.base_url + "/" + path.lstrip("/")

    def has_credentials(self) -> bool:
        return bool(
            self.username
            and self.username.strip()
            and self.password
            and self.password.strip()
        )

    def has_access_token(self) -> bool:
        return bool(
            self.access_token
            and self.access_token.strip()
        )

    def generate_token(self) -> dict:
        if not self.has_credentials():
            raise ValueError(
                "QUANTHUB_USERNAME and QUANTHUB_PASSWORD are required. "
                "Use generated QuantHub credentials from /api/auth/, not Microsoft password."
            )

        url = self._url("/api/token/")

        payload = {
            "username": self.username,
            "password": self.password,
        }

        logger.info("Generating QuantHub access token")

        response = requests.post(
            url,
            json=payload,
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        access_token = (
            data.get("access")
            or data.get("access_token")
            or data.get("token")
        )

        refresh_token = (
            data.get("refresh")
            or data.get("refresh_token")
        )

        if not access_token:
            raise ValueError(
                f"QuantHub token response did not include access token. Keys: {list(data.keys())}"
            )

        self.access_token = access_token
        self.refresh_token = refresh_token

        logger.info("QuantHub access token generated successfully")

        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "raw_response_keys": list(data.keys()),
        }

    def headers(self) -> dict:
        if not self.has_access_token():
            self.generate_token()

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    def get(self, path: str, params: dict | None = None) -> Any:
        url = self._url(path)

        logger.info(f"QuantHub GET {url}, params={params}")

        response = requests.get(
            url,
            headers=self.headers(),
            params=params or {},
            timeout=self.timeout,
        )

        if response.status_code in (401, 403):
            logger.warning("QuantHub token rejected. Regenerating token and retrying once.")

            self.generate_token()

            response = requests.get(
                url,
                headers=self.headers(),
                params=params or {},
                timeout=self.timeout,
            )

        response.raise_for_status()

        try:
            return response.json()
        except Exception:
            return {
                "raw_text": response.text,
            }

    def post(self, path: str, payload: dict | None = None) -> Any:
        url = self._url(path)

        logger.info(f"QuantHub POST {url}, payload={payload}")

        response = requests.post(
            url,
            headers=self.headers(),
            json=payload or {},
            timeout=self.timeout,
        )

        if response.status_code in (401, 403):
            logger.warning("QuantHub token rejected. Regenerating token and retrying once.")

            self.generate_token()

            response = requests.post(
                url,
                headers=self.headers(),
                json=payload or {},
                timeout=self.timeout,
            )

        response.raise_for_status()

        try:
            return response.json()
        except Exception:
            return {
                "raw_text": response.text,
            }


def extract_records(payload: Any) -> list:
    if payload is None:
        return []

    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ["data", "results", "rows", "items", "candles", "values"]:
            value = payload.get(key)

            if isinstance(value, list):
                return value

        return [payload]

    return []


def first_present(item: dict, keys: list[str], default=None):
    for key in keys:
        if key in item and item.get(key) is not None:
            return item.get(key)

    return default


def parse_timestamp(item: dict) -> pd.Timestamp:
    """
    Parse timestamps from QuantHub responses.

    QuantHub OHLC v2 appears to return Unix milliseconds:
        1775936000000

    We support:
    - Unix seconds:      10 digits, ~1700000000
    - Unix milliseconds: 13 digits, ~1700000000000
    - Unix microseconds: 16 digits
    - Unix nanoseconds:  19 digits
    - ISO date strings
    """

    value = first_present(
        item,
        [
            "timestamp",
            "datetime",
            "time",
            "date",
            "created_at",
            "updated_at",
            "ts",
            "start",
            "end",
        ],
    )

    if value is None:
        return pd.Timestamp.now(tz="UTC")

    # Numeric Unix timestamp handling.
    if isinstance(value, (int, float)):
        numeric_value = float(value)

        try:
            abs_value = abs(numeric_value)

            if abs_value >= 1e18:
                # nanoseconds
                return pd.to_datetime(
                    numeric_value,
                    unit="ns",
                    utc=True,
                    errors="coerce",
                )

            if abs_value >= 1e15:
                # microseconds
                return pd.to_datetime(
                    numeric_value,
                    unit="us",
                    utc=True,
                    errors="coerce",
                )

            if abs_value >= 1e12:
                # milliseconds
                return pd.to_datetime(
                    numeric_value,
                    unit="ms",
                    utc=True,
                    errors="coerce",
                )

            # seconds
            return pd.to_datetime(
                numeric_value,
                unit="s",
                utc=True,
                errors="coerce",
            )

        except Exception:
            return pd.Timestamp.now(tz="UTC")

    # Numeric string handling.
    if isinstance(value, str):
        stripped = value.strip()

        if stripped.isdigit():
            numeric_value = float(stripped)
            abs_value = abs(numeric_value)

            try:
                if abs_value >= 1e18:
                    return pd.to_datetime(numeric_value, unit="ns", utc=True, errors="coerce")
                if abs_value >= 1e15:
                    return pd.to_datetime(numeric_value, unit="us", utc=True, errors="coerce")
                if abs_value >= 1e12:
                    return pd.to_datetime(numeric_value, unit="ms", utc=True, errors="coerce")
                return pd.to_datetime(numeric_value, unit="s", utc=True, errors="coerce")
            except Exception:
                return pd.Timestamp.now(tz="UTC")

    parsed = pd.to_datetime(
        value,
        utc=True,
        errors="coerce",
    )

    if pd.isna(parsed):
        return pd.Timestamp.now(tz="UTC")

    return parsed


def parse_numeric_value(item: dict, preferred_keys: list[str] | None = None) -> float:
    keys = preferred_keys or [
        "close",
        "price",
        "value",
        "fairvalue",
        "fair_value",
        "premium",
        "spread",
        "last",
        "settle",
        "volume",
        "qty",
    ]

    value = first_present(item, keys, default=0.0)

    try:
        return float(value)
    except Exception:
        return 0.0


def normalize_quanthub_payload(
    payload: Any,
    endpoint_key: str,
    default_series_prefix: str = "quanthub",
) -> pd.DataFrame:
    records = extract_records(payload)

    rows = []

    for item in records:
        if not isinstance(item, dict):
            continue

        timestamp = parse_timestamp(item)

        instrument = first_present(
            item,
            [
                "instrument",
                "instruments",
                "symbol",
                "ticker",
                "product",
                "product_id",
                "id",
                "qh_code",
                "code",
            ],
            default="unknown",
        )

        metric = first_present(
            item,
            [
                "metric",
                "field",
                "type",
                "category",
                "name",
            ],
            default=endpoint_key,
        )

        raw_value = parse_numeric_value(item)

        series_name = f"{default_series_prefix}_{endpoint_key}_{instrument}_{metric}"
        series_name = (
            str(series_name)
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("-", "_")
            .replace(",", "_")
        )

        rows.append(
            {
                "timestamp": timestamp,
                "source": "QUANTHUB",
                "series_name": series_name,
                "raw_value": raw_value,
                "metadata": {
                    "endpoint_key": endpoint_key,
                    "instrument": instrument,
                    "metric": metric,
                    "raw": item,
                },
            }
        )

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).sort_values("timestamp")


def normalize_quanthub_ohlc_payload(
    payload,
    endpoint_key: str = "ohlc_v2",
) -> pd.DataFrame:
    """
    Normalize QuantHub OHLC response.

    Input example:
    [
      {
        "product": "CLN26",
        "time": 1775936000000,
        "open": 99.14,
        "high": 100.81,
        "low": 94.28,
        "close": 97.22,
        "volume": 41733
      }
    ]

    Output raw_observations rows:
    - quanthub_ohlc_v2_CLN26_open
    - quanthub_ohlc_v2_CLN26_high
    - quanthub_ohlc_v2_CLN26_low
    - quanthub_ohlc_v2_CLN26_close
    - quanthub_ohlc_v2_CLN26_volume
    """

    records = extract_records(payload)
    rows = []

    for item in records:
        if not isinstance(item, dict):
            continue

        timestamp = parse_timestamp(item)

        product = first_present(
            item,
            ["product", "instrument", "symbol", "ticker", "id", "code"],
            default="unknown",
        )

        for field in ["open", "high", "low", "close", "volume"]:
            if field not in item:
                continue

            try:
                raw_value = float(item[field])
            except Exception:
                continue

            series_name = f"quanthub_{endpoint_key}_{product}_{field}"
            series_name = (
                str(series_name)
                .lower()
                .replace(" ", "_")
                .replace("/", "_")
                .replace("-", "_")
                .replace(",", "_")
            )

            rows.append(
                {
                    "timestamp": timestamp,
                    "source": "QUANTHUB",
                    "series_name": series_name,
                    "raw_value": raw_value,
                    "metadata": {
                        "endpoint_key": endpoint_key,
                        "product": product,
                        "field": field,
                        "raw": item,
                    },
                }
            )

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).sort_values("timestamp")


def fetch_ohlc_v2(
    instruments: str,
    interval: str,
    count: int | None = 50,
    start: int | None = None,
    end: int | None = None,
) -> pd.DataFrame:
    """
    GET /api/v2/ohlc/

    Required query params:
        instruments: comma-separated QH codes, up to 50
        interval: 1M / 5M / 1H / 1D

    Optional:
        count
        start unix seconds
        end unix seconds
    """

    if not instruments:
        raise ValueError("instruments is required for /api/v2/ohlc/")

    if not interval:
        raise ValueError("interval is required for /api/v2/ohlc/")

    params = {
        "instruments": instruments,
        "interval": interval,
    }

    if count is not None:
        params["count"] = str(count)

    if start is not None:
        params["start"] = str(start)

    if end is not None:
        params["end"] = str(end)

    client = QuantHubClient()

    payload = client.get(
        "/api/v2/ohlc/",
        params=params,
    )

    return normalize_quanthub_ohlc_payload(
        payload,
        endpoint_key="ohlc_v2",
    )


def fetch_tas_v2(
    products: list[dict],
) -> pd.DataFrame:
    """
    POST /api/v2/tas/

    Body model from Swagger:
    {
      "products": [
        {
          "id": "...",
          "dates": [...],
          "start": ...,
          "end": ...
        }
      ]
    }
    """

    if not products:
        raise ValueError("products list is required for /api/v2/tas/")

    payload = {
        "products": products,
    }

    client = QuantHubClient()

    response_payload = client.post(
        "/api/v2/tas/",
        payload=payload,
    )

    return normalize_quanthub_payload(
        response_payload,
        endpoint_key="tas_v2",
    )


def fetch_fairvalue_v2_get(
    products: str,
) -> pd.DataFrame:
    """
    GET /api/v2/fairvalue/

    Query:
        products: comma-separated product IDs or '*'
    """

    if not products:
        raise ValueError("products is required for GET /api/v2/fairvalue/")

    client = QuantHubClient()

    payload = client.get(
        "/api/v2/fairvalue/",
        params={
            "products": products,
        },
    )

    return normalize_quanthub_payload(
        payload,
        endpoint_key="fairvalue_v2",
    )


def fetch_fairvalue_v2_post(
    products: list[str],
) -> pd.DataFrame:
    """
    POST /api/v2/fairvalue/

    Body:
    {
      "products": ["product1", "product2"]
    }
    """

    if not products:
        raise ValueError("products list is required for POST /api/v2/fairvalue/")

    client = QuantHubClient()

    payload = client.post(
        "/api/v2/fairvalue/",
        payload={
            "products": products,
        },
    )

    return normalize_quanthub_payload(
        payload,
        endpoint_key="fairvalue_v2",
    )


def fetch_vap_v2(
    params: dict | None = None,
) -> pd.DataFrame:
    """
    GET /api/v2/vap/

    Swagger screenshot only showed endpoint header.
    Keeping params flexible.
    """

    client = QuantHubClient()

    payload = client.get(
        "/api/v2/vap/",
        params=params or {},
    )

    return normalize_quanthub_payload(
        payload,
        endpoint_key="vap_v2",
    )


def fetch_quanthub_events() -> pd.DataFrame:
    """
    Backward compatible default.
    Uses no default because QuantHub v2 endpoints require product/instrument input.
    """

    raise ValueError(
        "QuantHub endpoint requires parameters. Use /ingest/quanthub/ohlc-v2, "
        "/ingest/quanthub/tas-v2, or /ingest/quanthub/fairvalue-v2."
    )


def test_quanthub_auth() -> dict:
    client = QuantHubClient()

    token_result = client.generate_token()

    access_token = token_result.get("access_token")
    refresh_token = token_result.get("refresh_token")

    return {
        "status": "success",
        "base_url": client.base_url,
        "has_access_token": bool(access_token),
        "has_refresh_token": bool(refresh_token),
        "access_token_preview": access_token[:12] + "..." if access_token else None,
    }


def test_quanthub_ohlc_v2(
    instruments: str,
    interval: str,
    count: int = 5,
) -> dict:
    df = fetch_ohlc_v2(
        instruments=instruments,
        interval=interval,
        count=count,
    )

    return {
        "status": "success",
        "records": len(df),
        "sample": df.head(5).to_dict("records") if not df.empty else [],
    }


def test_quanthub_endpoint(
    endpoint_key: str,
    params: dict | None = None,
) -> dict:
    """
    Test a QuantHub endpoint without storing data.
    """
    try:
        df = fetch_quanthub_endpoint(
            endpoint_key=endpoint_key,
            params=params,
        )

        return {
            "status": "success",
            "endpoint_key": endpoint_key,
            "records": len(df),
            "sample": df.head(5).to_dict("records") if not df.empty else [],
        }

    except Exception as e:
        return {
            "status": "error",
            "endpoint_key": endpoint_key,
            "message": str(e),
            "records": 0,
        }


def fetch_quanthub_endpoint(
    endpoint_key: str,
    params: dict | None = None,
) -> pd.DataFrame:
    """
    Backward-compatible wrapper for old route:
        POST /ingest/quanthub?endpoint_key=...

    Supported endpoint_key values:
        ohlc
        ohlc_v2
        fairvalue
        fairvalue_v2
        vap
        vap_v2

    TAS needs JSON body, so use:
        POST /ingest/quanthub/tas-v2
    """

    params = params or {}

    if endpoint_key in {"ohlc", "ohlc_v2"}:
        instruments = params.get("instruments")
        interval = params.get("interval", "1D")
        count = int(params.get("count", 50))

        if not instruments:
            raise ValueError(
                "OHLC v2 requires instruments. Use: "
                "/ingest/quanthub/ohlc-v2?instruments=YOUR_QH_CODE&interval=1D&count=50"
            )

        return fetch_ohlc_v2(
            instruments=instruments,
            interval=interval,
            count=count,
            start=params.get("start"),
            end=params.get("end"),
        )

    if endpoint_key in {"fairvalue", "fairvalue_v2"}:
        products = params.get("products", "*")

        return fetch_fairvalue_v2_get(
            products=products,
        )

    if endpoint_key in {"vap", "vap_v2"}:
        return fetch_vap_v2(
            params=params,
        )

    if endpoint_key in {"tas", "tas_v2"}:
        raise ValueError(
            "TAS v2 requires JSON body. Use POST /ingest/quanthub/tas-v2 instead."
        )

    raise ValueError(
        f"Unsupported QuantHub endpoint_key={endpoint_key}. "
        "Use ohlc_v2, fairvalue_v2, vap_v2, or dedicated tas-v2 route."
    )
