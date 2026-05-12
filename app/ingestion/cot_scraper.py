from io import BytesIO
import zipfile
import requests
import pandas as pd


CFTC_HISTORY_BASE = "https://www.cftc.gov/files/dea/history"


def _download_zip_csv(url: str) -> pd.DataFrame:
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    z = zipfile.ZipFile(BytesIO(response.content))

    csv_or_txt_files = [
        name for name in z.namelist()
        if name.lower().endswith((".csv", ".txt"))
    ]

    if not csv_or_txt_files:
        raise ValueError(f"No CSV/TXT file found inside {url}")

    file_name = csv_or_txt_files[0]

    with z.open(file_name) as f:
        try:
            return pd.read_csv(f)
        except Exception:
            f.seek(0)
            return pd.read_csv(f, low_memory=False)


def fetch_cot_disaggregated_scrape(
    year: int | None = None,
    market_filter: str = "CRUDE OIL",
) -> pd.DataFrame:
    """
    Scrape/download CFTC disaggregated COT historical zip file.

    This uses public CFTC historical files.
    It normalizes managed money long-short into raw_observations.

    The generated output:
    timestamp, source, series_name, raw_value, metadata
    """

    if year is None:
        year = pd.Timestamp.utcnow().year

    # Common CFTC naming convention for disaggregated COT historical file.
    url = f"{CFTC_HISTORY_BASE}/deacot{year}.zip"

    df = _download_zip_csv(url)

    # Normalize columns.
    df.columns = [
        str(c).strip().lower().replace(" ", "_").replace("-", "_")
        for c in df.columns
    ]

    # Try common column names from CFTC disaggregated report.
    date_candidates = [
        "report_date_as_yyyy_mm_dd",
        "report_date_as_yyyy_mm_dd",
        "as_of_date_in_form_yyyy_mm_dd",
        "report_date",
    ]

    market_candidates = [
        "market_and_exchange_names",
        "contract_market_name",
        "market_name",
    ]

    long_candidates = [
        "m_money_positions_long_all",
        "managed_money_positions_long_all",
        "money_manager_long_all",
    ]

    short_candidates = [
        "m_money_positions_short_all",
        "managed_money_positions_short_all",
        "money_manager_short_all",
    ]

    date_col = next((c for c in date_candidates if c in df.columns), None)
    market_col = next((c for c in market_candidates if c in df.columns), None)
    long_col = next((c for c in long_candidates if c in df.columns), None)
    short_col = next((c for c in short_candidates if c in df.columns), None)

    if not date_col:
        raise ValueError(f"Could not find report date column. Columns: {list(df.columns)}")

    if not market_col:
        raise ValueError(f"Could not find market column. Columns: {list(df.columns)}")

    if not long_col or not short_col:
        raise ValueError(f"Could not find managed money long/short columns. Columns: {list(df.columns)}")

    crude = df[
        df[market_col]
        .astype(str)
        .str.upper()
        .str.contains(market_filter.upper(), na=False)
    ].copy()

    rows = []

    for _, row in crude.iterrows():
        try:
            long_value = float(row[long_col])
            short_value = float(row[short_col])
        except Exception:
            continue

        net_position = long_value - short_value

        rows.append(
            {
                "timestamp": pd.to_datetime(row[date_col], utc=True),
                "source": "CFTC_COT_SCRAPE",
                "series_name": "managed_money_net_crude",
                "raw_value": float(net_position),
                "metadata": {
                    "market": row.get(market_col),
                    "long": long_value,
                    "short": short_value,
                    "year": year,
                    "url": url,
                },
            }
        )

    return pd.DataFrame(rows).sort_values("timestamp")