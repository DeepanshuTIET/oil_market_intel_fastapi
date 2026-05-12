import logging
import re
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

from app.core.config import settings


logger = logging.getLogger(__name__)


COT_SOURCE_NAME = "CFTC_COT_PETROLEUM"


def get_cot_url(mode: str = "futures") -> str:
    mode = (mode or "futures").lower().strip()

    if mode in {"options", "combined", "futures_options"}:
        return settings.CFTC_PETROLEUM_OPTIONS_URL

    return settings.CFTC_PETROLEUM_FUTURES_URL


def fetch_cot_petroleum_text(mode: str = "futures") -> str:
    url = get_cot_url(mode)

    logger.info(f"Fetching CFTC COT Petroleum report mode={mode}, url={url}")

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "oil-market-intel-fastapi/1.0",
        },
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Long-format CFTC pages are text-heavy/fixed-width.
    text = soup.get_text("\n")

    logger.info(f"CFTC COT Petroleum text length={len(text)}")

    return text


def parse_report_date(text: str) -> pd.Timestamp:
    """
    Example text usually contains:
        Disaggregated Commitments of Traders - Futures Only, April 21, 2026
    """

    patterns = [
        r"Futures Only,\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        r"Futures-and-Options.*?,\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        r"Commitments of Traders.*?,\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            parsed = pd.to_datetime(
                match.group(1),
                utc=True,
                errors="coerce",
            )

            if not pd.isna(parsed):
                return parsed

    logger.warning("Could not parse CFTC report date. Using current UTC timestamp.")

    return pd.Timestamp.now(tz="UTC")


def split_contract_blocks(text: str) -> list:
    """
    Split into contract blocks.

    Contract headers look like:
        WTI-PHYSICAL - NEW YORK MERCANTILE EXCHANGE
        BRENT LAST DAY - ICE FUTURES EUROPE
    """

    pattern = (
        r"([A-Z0-9\-\s\/\.\#\(\)]+-\s+"
        r"(?:NEW YORK MERCANTILE EXCHANGE|ICE FUTURES ENERGY DIV|ICE FUTURES EUROPE|"
        r"CHICAGO MERCANTILE EXCHANGE|COMMODITY EXCHANGE INC).*?)"
        r"(?=\n[A-Z0-9\-\s\/\.\#\(\)]+-\s+"
        r"(?:NEW YORK MERCANTILE EXCHANGE|ICE FUTURES ENERGY DIV|ICE FUTURES EUROPE|"
        r"CHICAGO MERCANTILE EXCHANGE|COMMODITY EXCHANGE INC)|\Z)"
    )

    blocks = re.findall(
        pattern,
        text,
        flags=re.DOTALL,
    )

    logger.info(f"CFTC contract blocks found={len(blocks)}")

    return blocks


def clean_contract_name(header: str) -> str:
    return " ".join(header.strip().split())


def extract_numbers(line: str) -> list:
    """
    Extract integer or decimal numbers.
    Handles:
        2,037,857
        -1,234
        100.0
    """

    raw = re.findall(r"-?\d[\d,]*\.?\d*", line)

    nums = []

    for item in raw:
        item = item.replace(",", "")

        try:
            if "." in item:
                nums.append(float(item))
            else:
                nums.append(int(item))
        except Exception:
            continue

    return nums


def find_line_starting(block: str, label: str) -> str | None:
    for line in block.splitlines():
        stripped = line.strip()

        if stripped.startswith(label):
            return stripped

    return None


def parse_all_positions_line(line: str) -> dict[str, Any] | None:
    """
    Parses the 'All :' positions row.

    Expected order for disaggregated petroleum long format:

    Open Interest
    Producer/Merchant Long
    Producer/Merchant Short
    Swap Long
    Swap Short
    Swap Spreading
    Managed Money Long
    Managed Money Short
    Managed Money Spreading
    Other Reportables Long
    Other Reportables Short
    Other Reportables Spreading
    Nonreportable Long
    Nonreportable Short
    """

    nums = extract_numbers(line)

    if len(nums) < 14:
        logger.warning(f"All row has insufficient numbers: len={len(nums)}, line={line}")
        return None

    return {
        "open_interest": nums[0],
        "producer_long": nums[1],
        "producer_short": nums[2],
        "swap_long": nums[3],
        "swap_short": nums[4],
        "swap_spreading": nums[5],
        "mm_long": nums[6],
        "mm_short": nums[7],
        "mm_spreading": nums[8],
        "other_long": nums[9],
        "other_short": nums[10],
        "other_spreading": nums[11],
        "nonrep_long": nums[12],
        "nonrep_short": nums[13],
    }


def parse_change_line(block: str) -> dict[str, Any]:
    """
    Parses line after:
        Changes in Commitments from: ...
    """

    lines = block.splitlines()

    for i, line in enumerate(lines):
        if "Changes in Commitments from" in line:
            # Usually the next non-empty line contains the change numbers.
            for candidate in lines[i + 1 : i + 5]:
                nums = extract_numbers(candidate)

                if len(nums) >= 14:
                    return {
                        "open_interest_change": nums[0],
                        "producer_long_change": nums[1],
                        "producer_short_change": nums[2],
                        "swap_long_change": nums[3],
                        "swap_short_change": nums[4],
                        "swap_spreading_change": nums[5],
                        "mm_long_change": nums[6],
                        "mm_short_change": nums[7],
                        "mm_spreading_change": nums[8],
                        "other_long_change": nums[9],
                        "other_short_change": nums[10],
                        "other_spreading_change": nums[11],
                        "nonrep_long_change": nums[12],
                        "nonrep_short_change": nums[13],
                    }

    return {}


def parse_contract_block(block: str, report_date: pd.Timestamp, mode: str) -> dict[str, Any] | None:
    lines = [x.strip() for x in block.splitlines() if x.strip()]

    if not lines:
        return None

    contract_header = clean_contract_name(lines[0])

    all_line = find_line_starting(block, "All")

    if not all_line:
        logger.warning(f"No All row found for contract={contract_header}")
        return None

    positions = parse_all_positions_line(all_line)

    if not positions:
        return None

    changes = parse_change_line(block)

    row = {
        "date": report_date,
        "contract": contract_header,
        "mode": mode,
        **positions,
        **changes,
    }

    return add_cot_derived_fields(row)


def add_cot_derived_fields(row: dict[str, Any]) -> dict[str, Any]:
    open_interest = row.get("open_interest") or 0

    mm_net = (row.get("mm_long") or 0) - (row.get("mm_short") or 0)
    swap_net = (row.get("swap_long") or 0) - (row.get("swap_short") or 0)
    producer_net = (row.get("producer_long") or 0) - (row.get("producer_short") or 0)

    row["mm_net"] = mm_net
    row["swap_net"] = swap_net
    row["producer_net"] = producer_net

    if open_interest:
        row["mm_net_pct_oi"] = mm_net / open_interest
        row["swap_net_pct_oi"] = swap_net / open_interest
        row["producer_net_pct_oi"] = producer_net / open_interest
        row["mm_long_pct_oi"] = (row.get("mm_long") or 0) / open_interest
        row["mm_short_pct_oi"] = (row.get("mm_short") or 0) / open_interest
    else:
        row["mm_net_pct_oi"] = None
        row["swap_net_pct_oi"] = None
        row["producer_net_pct_oi"] = None
        row["mm_long_pct_oi"] = None
        row["mm_short_pct_oi"] = None

    row["dealer_vs_spec"] = swap_net - mm_net

    mm_net_change = None

    if "mm_long_change" in row and "mm_short_change" in row:
        mm_net_change = (row.get("mm_long_change") or 0) - (row.get("mm_short_change") or 0)

    row["mm_net_change"] = mm_net_change

    return row


def parse_cot_petroleum(mode: str = "futures") -> pd.DataFrame:
    text = fetch_cot_petroleum_text(mode=mode)
    report_date = parse_report_date(text)

    blocks = split_contract_blocks(text)

    rows = []

    for block in blocks:
        try:
            parsed = parse_contract_block(
                block=block,
                report_date=report_date,
                mode=mode,
            )

            if parsed:
                rows.append(parsed)

        except Exception as e:
            logger.exception(f"Failed parsing CFTC contract block: {e}")

    df = pd.DataFrame(rows)

    logger.info(f"CFTC COT Petroleum parsed dataframe shape={df.shape}")

    return df


def normalize_cot_to_raw_observations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert wide COT contract rows into RawObservation rows.

    Example series:
        cot_petroleum_wti_physical_managed_money_net
        cot_petroleum_wti_physical_mm_net_pct_oi
    """

    if df.empty:
        return pd.DataFrame()

    output_rows = []

    metric_cols = [
        "open_interest",
        "producer_long",
        "producer_short",
        "producer_net",
        "producer_net_pct_oi",
        "swap_long",
        "swap_short",
        "swap_net",
        "swap_net_pct_oi",
        "mm_long",
        "mm_short",
        "mm_net",
        "mm_net_pct_oi",
        "mm_long_pct_oi",
        "mm_short_pct_oi",
        "mm_net_change",
        "other_long",
        "other_short",
        "nonrep_long",
        "nonrep_short",
        "dealer_vs_spec",
    ]

    for _, row in df.iterrows():
        contract = str(row["contract"])
        contract_key = (
            contract.lower()
            .replace(" ", "_")
            .replace("-", "_")
            .replace("/", "_")
            .replace(".", "")
            .replace("#", "")
        )

        for metric in metric_cols:
            if metric not in row:
                continue

            value = row.get(metric)

            if pd.isna(value):
                continue

            output_rows.append(
                {
                    "timestamp": row["date"],
                    "source": COT_SOURCE_NAME,
                    "series_name": f"cot_petroleum_{contract_key}_{metric}",
                    "raw_value": float(value),
                    "metadata": {
                        "contract": contract,
                        "mode": row.get("mode"),
                        "metric": metric,
                        "report_date": row["date"].isoformat()
                        if hasattr(row["date"], "isoformat")
                        else str(row["date"]),
                    },
                }
            )

    return pd.DataFrame(output_rows)


def fetch_all_cot_petroleum(mode: str = "futures") -> pd.DataFrame:
    parsed = parse_cot_petroleum(mode=mode)

    return normalize_cot_to_raw_observations(parsed)
