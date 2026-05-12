import re
import json
import logging
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone
import math

import requests
import pandas as pd
from PyPDF2 import PdfReader

eia_logger = logging.getLogger("eia_pdf")

EIA_WPSR_OVERVIEW_URL = "https://ir.eia.gov/wpsr/overview.pdf"

OUTPUT_DIR = Path("eia_weekly_output")
RAW_DIR = OUTPUT_DIR / "raw"
PROCESSED_DIR = OUTPUT_DIR / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


EIA_PDF_METRICS = {
    # Stocks, million barrels
    "commercial_crude_stocks": {
        "label": "Commercial (Excluding SPR)",
        "section": "stocks",
        "unit": "million_barrels",
        "direction": "lower_is_bullish",
        "weight": 3.0,
    },
    "gasoline_stocks": {
        "label": "Total Motor Gasoline",
        "section": "stocks",
        "unit": "million_barrels",
        "direction": "lower_is_bullish",
        "weight": 2.0,
    },
    "distillate_stocks": {
        "label": "Distillate Fuel Oil",
        "section": "stocks",
        "unit": "million_barrels",
        "direction": "lower_is_bullish",
        "weight": 2.0,
    },
    "propane_stocks": {
        "label": "Propane/Propylene",
        "section": "stocks",
        "unit": "million_barrels",
        "direction": "lower_is_bullish",
        "weight": 0.75,
    },
    "total_stocks_ex_spr": {
        "label": "Total Stocks (Excluding SPR)",
        "section": "stocks",
        "unit": "million_barrels",
        "direction": "lower_is_bullish",
        "weight": 1.0,
    },

    # Crude supply / refinery / trade, thousand barrels per day
    "crude_production": {
        "label": "Domestic Production",
        "section": "supply",
        "unit": "kbd",
        "direction": "lower_is_bullish",
        "weight": 1.0,
    },
    "crude_imports": {
        "label": "Imports",
        "section": "crude_supply",
        "unit": "kbd",
        "direction": "lower_is_bullish",
        "weight": 0.5,
    },
    "crude_exports": {
        "label": "Exports",
        "section": "crude_supply",
        "unit": "kbd",
        "direction": "higher_is_bullish",
        "weight": 0.75,
    },
    "refinery_crude_inputs": {
        "label": "Crude Oil Input to Refineries",
        "section": "supply",
        "unit": "kbd",
        "direction": "higher_is_bullish",
        "weight": 1.0,
    },
    "refinery_utilization": {
        "label": "Percent Utilization",
        "section": "weekly_estimates",
        "unit": "percent",
        "direction": "higher_is_bullish",
        "weight": 1.0,
    },

    # Demand / products supplied, thousand barrels per day
    "total_product_supplied": {
        "label": "Total",
        "section": "products_supplied",
        "unit": "kbd",
        "direction": "higher_is_bullish",
        "weight": 1.25,
    },
    "gasoline_product_supplied": {
        "label": "Finished Motor Gasoline",
        "section": "products_supplied",
        "unit": "kbd",
        "direction": "higher_is_bullish",
        "weight": 1.0,
    },
    "distillate_product_supplied": {
        "label": "Distillate Fuel Oil",
        "section": "products_supplied",
        "unit": "kbd",
        "direction": "higher_is_bullish",
        "weight": 1.0,
    },
}


def download_eia_overview_pdf() -> bytes:
    response = requests.get(EIA_WPSR_OVERVIEW_URL, timeout=60)
    response.raise_for_status()
    return response.content


def extract_pdf_text_from_bytes(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))

    pages = []

    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")

    return "\n".join(pages)


def extract_pdf_text_from_file(pdf_path: str | Path) -> str:
    reader = PdfReader(str(pdf_path))

    pages = []

    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")

    return "\n".join(pages)


def clean_number(value: str) -> float | None:
    if value is None:
        return None

    value = str(value).strip()

    if value in {"–", "-", "", "W", "R"}:
        return None

    value = value.replace(",", "")

    try:
        return float(value)
    except Exception:
        return None


def get_week_ending_date(text: str) -> pd.Timestamp:
    patterns = [
        r"Week Ending\s+(\d{1,2}/\d{1,2}/\d{4})",
        r"Week Ending\s+(\d{1,2}/\d{1,2}/\d{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            return pd.to_datetime(match.group(1), utc=True)

    return pd.Timestamp.now(tz="UTC").normalize()


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("**", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def extract_stock_metric(text: str, label: str) -> dict | None:
    """
    Parses stock rows from Table 1.

    Expected row shape:
    label current week_ago wow wow_pct year_ago yoy yoy_pct
    """

    pattern = (
        re.escape(label)
        + r".{0,120}?"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)"
    )

    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)

    if not match:
        return None

    nums = [clean_number(x) for x in match.groups()]

    return {
        "current": nums[0],
        "week_ago": nums[1],
        "wow_change": nums[2],
        "wow_pct": nums[3],
        "year_ago": nums[4],
        "yoy_change": nums[5],
        "yoy_pct": nums[6],
    }


def extract_supply_metric(text: str, label: str, occurrence: int = 1) -> dict | None:
    """
    Parses supply / demand rows.

    Expected row shape begins:
    label current week_ago wow year_ago yoy ...
    """

    pattern = (
        re.escape(label)
        + r".{0,120}?"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)"
    )

    matches = list(re.finditer(pattern, text, flags=re.IGNORECASE | re.DOTALL))

    if not matches or len(matches) < occurrence:
        return None

    match = matches[occurrence - 1]
    nums = [clean_number(x) for x in match.groups()]

    return {
        "current": nums[0],
        "week_ago": nums[1],
        "wow_change": nums[2],
        "year_ago": nums[3],
        "yoy_change": nums[4],
        "wow_pct": None,
        "yoy_pct": None,
    }


def extract_weekly_estimate_metric(text: str, label: str, occurrence: int = 1) -> dict | None:
    """
    Parses Table 9 weekly estimate rows.

    Table 9 shape:
        label current last_week year_ago two_years_ago four_week_avg_current four_week_avg_year_ago

    For example:
        Percent Utilization 89.6 89.1 88.6 87.5 90.1 87.4

    We calculate:
        wow_change = current - last_week
        yoy_change = current - year_ago
    """

    pattern = (
        re.escape(label)
        + r".{0,160}?"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)\s+"
        + r"(-?\d[\d,]*\.?\d*)"
    )

    matches = list(
        re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
    )

    if not matches or len(matches) < occurrence:
        return None

    match = matches[occurrence - 1]
    nums = [clean_number(x) for x in match.groups()]

    current = nums[0]
    week_ago = nums[1]
    year_ago = nums[2]
    two_years_ago = nums[3]
    four_week_avg = nums[4]
    four_week_avg_year_ago = nums[5]

    wow_change = None
    yoy_change = None
    wow_pct = None
    yoy_pct = None

    if current is not None and week_ago not in (None, 0):
        wow_change = current - week_ago
        wow_pct = (wow_change / week_ago) * 100

    if current is not None and year_ago not in (None, 0):
        yoy_change = current - year_ago
        yoy_pct = (yoy_change / year_ago) * 100

    return {
        "current": current,
        "week_ago": week_ago,
        "wow_change": wow_change,
        "wow_pct": wow_pct,
        "year_ago": year_ago,
        "yoy_change": yoy_change,
        "yoy_pct": yoy_pct,
        "two_years_ago": two_years_ago,
        "four_week_avg": four_week_avg,
        "four_week_avg_year_ago": four_week_avg_year_ago,
    }


def directional_score(direction: str, wow_change: float | None) -> int:
    if wow_change is None:
        return 0

    if direction == "lower_is_bullish":
        if wow_change < 0:
            return 1
        if wow_change > 0:
            return -1
        return 0

    if direction == "higher_is_bullish":
        if wow_change > 0:
            return 1
        if wow_change < 0:
            return -1
        return 0

    return 0


def parse_eia_wpsr_overview_text(text: str) -> dict:
    text = normalize_text(text)
    week_ending = get_week_ending_date(text)

    rows = []

    for metric, meta in EIA_PDF_METRICS.items():
        if meta["section"] == "stocks":
            parsed = extract_stock_metric(text, meta["label"])

        elif metric == "refinery_utilization":
            parsed = extract_weekly_estimate_metric(
                text,
                meta["label"],
                occurrence=1,
            )

        elif metric == "crude_imports":
            # First "Imports" in crude oil supply section should be crude imports.
            parsed = extract_supply_metric(text, meta["label"], occurrence=1)

        elif metric == "crude_exports":
            # First "Exports" in crude oil supply section should be crude exports.
            parsed = extract_supply_metric(text, meta["label"], occurrence=1)

        elif metric == "total_product_supplied":
            # Products Supplied Total row appears after Products Supplied heading.
            products_block_match = re.search(
                r"Products Supplied(.+?)Net Imports of Crude",
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )

            block = products_block_match.group(1) if products_block_match else text
            parsed = extract_supply_metric(block, meta["label"], occurrence=1)

        elif metric == "gasoline_product_supplied":
            products_block_match = re.search(
                r"Products Supplied(.+?)Net Imports of Crude",
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )

            block = products_block_match.group(1) if products_block_match else text
            parsed = extract_supply_metric(block, meta["label"], occurrence=1)

        elif metric == "distillate_product_supplied":
            products_block_match = re.search(
                r"Products Supplied(.+?)Net Imports of Crude",
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )

            block = products_block_match.group(1) if products_block_match else text
            parsed = extract_supply_metric(block, meta["label"], occurrence=1)

        else:
            parsed = extract_supply_metric(text, meta["label"], occurrence=1)

        if not parsed:
            rows.append(
                {
                    "date": week_ending,
                    "metric": metric,
                    "label": meta["label"],
                    "category": meta["section"],
                    "unit": meta["unit"],
                    "direction": meta["direction"],
                    "weight": meta["weight"],
                    "current": None,
                    "week_ago": None,
                    "wow_change": None,
                    "wow_pct": None,
                    "year_ago": None,
                    "yoy_change": None,
                    "yoy_pct": None,
                    "two_years_ago": None,
                    "four_week_avg": None,
                    "four_week_avg_year_ago": None,
                    "directional_score": 0,
                    "weighted_score": 0,
                    "signal": "Missing",
                }
            )
            continue

        score = directional_score(meta["direction"], parsed["wow_change"])
        weighted_score = score * meta["weight"]

        if weighted_score > 0:
            signal = "Bullish"
        elif weighted_score < 0:
            signal = "Bearish"
        else:
            signal = "Neutral"

        rows.append(
            {
                "date": week_ending,
                "metric": metric,
                "label": meta["label"],
                "category": meta["section"],
                "unit": meta["unit"],
                "direction": meta["direction"],
                "weight": meta["weight"],
                "current": parsed["current"],
                "week_ago": parsed["week_ago"],
                "wow_change": parsed["wow_change"],
                "wow_pct": parsed["wow_pct"],
                "year_ago": parsed["year_ago"],
                "yoy_change": parsed["yoy_change"],
                "yoy_pct": parsed["yoy_pct"],
                "two_years_ago": parsed.get("two_years_ago"),
                "four_week_avg": parsed.get("four_week_avg"),
                "four_week_avg_year_ago": parsed.get("four_week_avg_year_ago"),
                "directional_score": score,
                "weighted_score": weighted_score,
                "signal": signal,
            }
        )

    latest = pd.DataFrame(rows)

    total_score = latest["weighted_score"].sum()

    if total_score >= 4:
        headline = "Strong bullish petroleum balance"
    elif total_score >= 1.5:
        headline = "Moderately bullish petroleum balance"
    elif total_score > -1.5:
        headline = "Mixed / neutral petroleum balance"
    elif total_score > -4:
        headline = "Moderately bearish petroleum balance"
    else:
        headline = "Strong bearish petroleum balance"

    summary = {
        "latest_week": str(week_ending.date()),
        "total_score": float(total_score),
        "headline_signal": headline,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "EIA WPSR overview.pdf",
        "source_url": EIA_WPSR_OVERVIEW_URL,
    }

    return {
        "summary": summary,
        "latest": latest,
    }


def make_excel_safe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Excel cannot write timezone-aware datetimes.

    This function converts any timezone-aware datetime columns
    into timezone-naive datetimes before writing to Excel.
    """

    safe = df.copy()

    for col in safe.columns:
        if pd.api.types.is_datetime64_any_dtype(safe[col]):
            try:
                safe[col] = safe[col].dt.tz_localize(None)
            except TypeError:
                # Already timezone-naive
                pass

    return safe


def clean_json_value(value):
    """
    Convert values that break JSON serialization into safe Python values.

    Handles:
    - NaN
    - NaT
    - inf
    - -inf
    - pandas Timestamp
    - nested dict/list
    """

    if value is None:
        return None

    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value

    if isinstance(value, dict):
        return {
            key: clean_json_value(val)
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [
            clean_json_value(item)
            for item in value
        ]

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    return value


def dataframe_to_json_records(df: pd.DataFrame) -> list[dict]:
    """
    Convert DataFrame to JSON-safe records.
    """

    records = df.to_dict("records")

    return [
        clean_json_value(record)
        for record in records
    ]

def run_eia_pdf_report(
    pdf_path: str | None = None,
    save_files: bool = True,
) -> dict:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    eia_logger.info("run_eia_pdf_report started")
    eia_logger.info(f"pdf_path={pdf_path}, save_files={save_files}")

    if pdf_path:
        eia_logger.info(f"Reading local EIA PDF: {pdf_path}")

        text = extract_pdf_text_from_file(pdf_path)
        saved_pdf = str(pdf_path)

    else:
        eia_logger.info(f"Downloading EIA PDF from: {EIA_WPSR_OVERVIEW_URL}")

        pdf_bytes = download_eia_overview_pdf()

        eia_logger.info(f"Downloaded PDF bytes: {len(pdf_bytes)}")

        saved_pdf_path = RAW_DIR / f"eia_wpsr_overview_{timestamp}.pdf"

        if save_files:
            saved_pdf_path.write_bytes(pdf_bytes)
            eia_logger.info(f"Saved raw EIA PDF to: {saved_pdf_path}")

        text = extract_pdf_text_from_bytes(pdf_bytes)
        saved_pdf = str(saved_pdf_path)

    eia_logger.info(f"Extracted text length: {len(text)}")

    parsed = parse_eia_wpsr_overview_text(text)

    latest = parsed["latest"]
    summary = parsed["summary"]

    eia_logger.info(f"Parsed EIA latest rows: {len(latest)}")
    eia_logger.info(f"EIA summary: {summary}")

    missing_metrics = latest[
        latest["signal"].astype(str).str.lower().eq("missing")
    ]["metric"].tolist()

    if missing_metrics:
        eia_logger.warning(f"Missing EIA metrics after PDF parse: {missing_metrics}")
    else:
        eia_logger.info("All EIA metrics parsed successfully")

    latest_csv = PROCESSED_DIR / "latest_eia_pdf_signal.csv"
    summary_json = PROCESSED_DIR / "latest_eia_pdf_summary.json"
    excel_file = PROCESSED_DIR / "latest_eia_pdf_report.xlsx"

    if save_files:
        eia_logger.info(f"Saving latest EIA CSV to: {latest_csv}")
        latest.to_csv(latest_csv, index=False)

        eia_logger.info(f"Saving EIA summary JSON to: {summary_json}")

        with open(summary_json, "w", encoding="utf-8") as f:
            json.dump(
                clean_json_value(summary),
                f,
                indent=2,
            )

        try:
            eia_logger.info(f"Saving EIA Excel report to: {excel_file}")

            latest_excel = make_excel_safe(latest)
            summary_excel = make_excel_safe(pd.DataFrame([summary]))

            with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
                latest_excel.to_excel(
                    writer,
                    sheet_name="latest_signal",
                    index=False,
                )

                summary_excel.to_excel(
                    writer,
                    sheet_name="summary",
                    index=False,
                )

            eia_logger.info("EIA Excel report saved successfully")

        except ModuleNotFoundError as e:
            eia_logger.warning(
                f"Excel export skipped because openpyxl is missing: {e}"
            )
            excel_file = None

        except Exception as e:
            eia_logger.exception(
                f"Excel export failed but EIA parse will continue: {e}"
            )
            excel_file = None

    latest_records = dataframe_to_json_records(latest)
    safe_summary = clean_json_value(summary)

    result = {
        "summary": safe_summary,
        "latest": latest_records,
        "files": {
            "saved_pdf": saved_pdf,
            "latest_csv": str(latest_csv),
            "summary_json": str(summary_json),
            "excel_file": str(excel_file) if excel_file else None,
        },
    }

    result = clean_json_value(result)

    eia_logger.info("run_eia_pdf_report completed successfully")

    return result


def fetch_all_eia(
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    """
    FastAPI ingestion-compatible function.

    Returns raw_observations schema:
    timestamp, source, series_name, raw_value, metadata
    """

    eia_logger.info("fetch_all_eia started")

    result = run_eia_pdf_report(save_files=True)

    latest = pd.DataFrame(result["latest"])

    if latest.empty:
        eia_logger.warning("fetch_all_eia received empty latest dataframe")
        return pd.DataFrame()

    records = []

    for _, row in latest.iterrows():
        current_value = row.get("current")

        if current_value is None:
            continue

        if pd.isna(current_value):
            continue

        ts = pd.to_datetime(row["date"], utc=True)

        if start and ts < pd.to_datetime(start, utc=True):
            continue

        if end and ts > pd.to_datetime(end, utc=True):
            continue

        metadata = {
            "label": row.get("label"),
            "category": row.get("category"),
            "unit": row.get("unit"),
            "direction": row.get("direction"),
            "weight": row.get("weight"),
            "week_ago": row.get("week_ago"),
            "wow_change": row.get("wow_change"),
            "wow_pct": row.get("wow_pct"),
            "year_ago": row.get("year_ago"),
            "two_years_ago": row.get("two_years_ago"),
            "yoy_change": row.get("yoy_change"),
            "yoy_pct": row.get("yoy_pct"),
            "four_week_avg": row.get("four_week_avg"),
            "four_week_avg_year_ago": row.get("four_week_avg_year_ago"),
            "directional_score": row.get("directional_score"),
            "weighted_score": row.get("weighted_score"),
            "signal": row.get("signal"),
            "source_url": EIA_WPSR_OVERVIEW_URL,
        }

        metadata = clean_json_value(metadata)

        records.append(
            {
                "timestamp": ts,
                "source": "EIA_PDF",
                "series_name": row["metric"],
                "raw_value": float(current_value),
                "metadata": metadata,
            }
        )

        wow_change = row.get("wow_change")

        if wow_change is not None and not pd.isna(wow_change):
            records.append(
                {
                    "timestamp": ts,
                    "source": "EIA_PDF",
                    "series_name": f"{row['metric']}_wow_change",
                    "raw_value": float(wow_change),
                    "metadata": clean_json_value(
                        {
                            "parent_metric": row["metric"],
                            "unit": row.get("unit"),
                            "direction": row.get("direction"),
                            "weight": row.get("weight"),
                            "signal": row.get("signal"),
                        }
                    ),
                }
            )

    eia_logger.info(f"fetch_all_eia returning {len(records)} records")

    return pd.DataFrame(records)

    import logging

eia_logger = logging.getLogger("eia_pdf")


def debug_eia_pdf_parse() -> dict:
    """
    Detailed diagnostic endpoint for EIA PDF parsing.

    Use:
        GET /debug/eia/pdf

    This returns:
    - download status
    - extracted text length
    - week ending parse
    - parsed metric rows
    - missing metrics
    - text preview
    """

    eia_logger.info("EIA PDF debug parse started")
    eia_logger.info(f"Downloading PDF from: {EIA_WPSR_OVERVIEW_URL}")

    pdf_bytes = download_eia_overview_pdf()

    eia_logger.info(f"Downloaded PDF bytes: {len(pdf_bytes)}")

    text = extract_pdf_text_from_bytes(pdf_bytes)

    eia_logger.info(f"Extracted PDF text length: {len(text)}")

    normalized = normalize_text(text)

    eia_logger.info(f"Normalized text length: {len(normalized)}")

    week_ending = get_week_ending_date(normalized)

    eia_logger.info(f"Parsed week ending: {week_ending}")

    parsed = parse_eia_wpsr_overview_text(normalized)

    latest = parsed["latest"]
    summary = parsed["summary"]

    missing = latest[
        latest["signal"].astype(str).str.lower().eq("missing")
    ]["metric"].tolist()

    successful = latest[
        ~latest["signal"].astype(str).str.lower().eq("missing")
    ]["metric"].tolist()

    eia_logger.info(f"Successful metrics: {successful}")
    eia_logger.warning(f"Missing metrics: {missing}")

    eia_logger.debug("Latest parsed rows:")
    eia_logger.debug(latest.to_dict("records"))

    text_preview = normalized[:5000]

    return {
        "status": "success",
        "source_url": EIA_WPSR_OVERVIEW_URL,
        "pdf_bytes": len(pdf_bytes),
        "text_length": len(text),
        "normalized_text_length": len(normalized),
        "week_ending": str(week_ending),
        "summary": summary,
        "metrics_total": len(latest),
        "metrics_successful": successful,
        "metrics_missing": missing,
        "latest_rows": latest.to_dict("records"),
        "text_preview_first_5000_chars": text_preview,
    }