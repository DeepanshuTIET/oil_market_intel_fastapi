import logging
import traceback

import pandas as pd

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import RawObservation
from app.services.repository import upsert_raw
from app.ingestion.quanthub import (
    test_quanthub_auth,
    test_quanthub_ohlc_v2,
    fetch_quanthub_endpoint,
    fetch_ohlc_v2,
    fetch_tas_v2,
    fetch_fairvalue_v2_get,
    fetch_vap_v2,
)


logger = logging.getLogger(__name__)

router = APIRouter(tags=["QuantHub"])


@router.get("/debug/quanthub/auth")
def debug_quanthub_auth():
    logger.info("GET /debug/quanthub/auth started")

    try:
        return test_quanthub_auth()

    except Exception as e:
        logger.exception("QuantHub auth debug failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "quanthub_auth_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.get("/debug/quanthub/ohlc-v2")
def debug_quanthub_ohlc_v2(
    instruments: str,
    interval: str = "1D",
    count: int = 5,
):
    logger.info(
        f"GET /debug/quanthub/ohlc-v2 instruments={instruments}, interval={interval}, count={count}"
    )

    try:
        return test_quanthub_ohlc_v2(
            instruments=instruments,
            interval=interval,
            count=count,
        )

    except Exception as e:
        logger.exception("QuantHub OHLC v2 debug failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "quanthub_ohlc_v2_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.post("/ingest/quanthub")
def ingest_quanthub(
    endpoint_key: str = "ohlc_v2",
    instruments: str | None = None,
    interval: str = "1D",
    count: int = 50,
    products: str = "*",
    db: Session = Depends(get_db),
):
    """
    Backward-compatible generic QuantHub ingestion route.

    Recommended:
        POST /ingest/quanthub/ohlc-v2?instruments=CLN26&interval=1D&count=50
    """

    logger.info(
        f"POST /ingest/quanthub endpoint_key={endpoint_key}, "
        f"instruments={instruments}, interval={interval}, count={count}, products={products}"
    )

    try:
        params = {
            "instruments": instruments,
            "interval": interval,
            "count": count,
            "products": products,
        }

        df = fetch_quanthub_endpoint(
            endpoint_key=endpoint_key,
            params=params,
        )

        logger.info(f"QuantHub dataframe shape={df.shape}")

        if df.empty:
            return {
                "status": "no_data",
                "source": "QUANTHUB",
                "endpoint_key": endpoint_key,
                "records": 0,
                "message": "QuantHub returned no rows.",
            }

        count_written = upsert_raw(
            db,
            df.to_dict("records"),
        )

        logger.info(f"QuantHub records written={count_written}")

        return {
            "status": "success",
            "source": "QUANTHUB",
            "endpoint_key": endpoint_key,
            "records": count_written,
            "columns": list(df.columns),
            "sample": df.head(5).to_dict("records"),
        }

    except Exception as e:
        logger.exception("QuantHub generic ingestion failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "quanthub_ingestion_failed",
                "endpoint_key": endpoint_key,
                "message": str(e),
                "traceback": traceback.format_exc(),
                "hint": (
                    "For OHLC use: "
                    "/ingest/quanthub/ohlc-v2?instruments=YOUR_QH_CODE&interval=1D&count=50"
                ),
            },
        )


@router.post("/ingest/quanthub/ohlc-v2")
def ingest_quanthub_ohlc_v2(
    instruments: str,
    interval: str = "1D",
    count: int = 50,
    start: int | None = None,
    end: int | None = None,
    db: Session = Depends(get_db),
):
    logger.info(
        f"POST /ingest/quanthub/ohlc-v2 instruments={instruments}, "
        f"interval={interval}, count={count}, start={start}, end={end}"
    )

    try:
        df = fetch_ohlc_v2(
            instruments=instruments,
            interval=interval,
            count=count,
            start=start,
            end=end,
        )

        if df.empty:
            return {
                "status": "no_data",
                "source": "QUANTHUB",
                "endpoint": "ohlc_v2",
                "records": 0,
            }

        count_written = upsert_raw(
            db,
            df.to_dict("records"),
        )

        return {
            "status": "success",
            "source": "QUANTHUB",
            "endpoint": "ohlc_v2",
            "records": count_written,
            "sample": df.head(5).to_dict("records"),
        }

    except Exception as e:
        logger.exception("QuantHub OHLC v2 ingestion failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "quanthub_ohlc_v2_ingestion_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.post("/ingest/quanthub/tas-v2")
def ingest_quanthub_tas_v2(
    data: dict,
    db: Session = Depends(get_db),
):
    logger.info("POST /ingest/quanthub/tas-v2 started")

    try:
        products = data.get("products", [])

        df = fetch_tas_v2(products=products)

        if df.empty:
            return {
                "status": "no_data",
                "source": "QUANTHUB",
                "endpoint": "tas_v2",
                "records": 0,
            }

        count_written = upsert_raw(db, df.to_dict("records"))

        return {
            "status": "success",
            "source": "QUANTHUB",
            "endpoint": "tas_v2",
            "records": count_written,
            "sample": df.head(5).to_dict("records"),
        }

    except Exception as e:
        logger.exception("QuantHub TAS v2 ingestion failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "quanthub_tas_v2_ingestion_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.post("/ingest/quanthub/fairvalue-v2")
def ingest_quanthub_fairvalue_v2(
    products: str = "*",
    db: Session = Depends(get_db),
):
    logger.info(f"POST /ingest/quanthub/fairvalue-v2 products={products}")

    try:
        df = fetch_fairvalue_v2_get(products=products)

        if df.empty:
            return {
                "status": "no_data",
                "source": "QUANTHUB",
                "endpoint": "fairvalue_v2",
                "records": 0,
            }

        count_written = upsert_raw(db, df.to_dict("records"))

        return {
            "status": "success",
            "source": "QUANTHUB",
            "endpoint": "fairvalue_v2",
            "records": count_written,
            "sample": df.head(5).to_dict("records"),
        }

    except Exception as e:
        logger.exception("QuantHub FairValue v2 ingestion failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "quanthub_fairvalue_v2_ingestion_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.post("/ingest/quanthub/vap-v2")
def ingest_quanthub_vap_v2(
    db: Session = Depends(get_db),
):
    logger.info("POST /ingest/quanthub/vap-v2 started")

    try:
        df = fetch_vap_v2(params={})

        if df.empty:
            return {
                "status": "no_data",
                "source": "QUANTHUB",
                "endpoint": "vap_v2",
                "records": 0,
            }

        count_written = upsert_raw(db, df.to_dict("records"))

        return {
            "status": "success",
            "source": "QUANTHUB",
            "endpoint": "vap_v2",
            "records": count_written,
            "sample": df.head(5).to_dict("records"),
        }

    except Exception as e:
        logger.exception("QuantHub VAP v2 ingestion failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "quanthub_vap_v2_ingestion_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.get("/quanthub/history")
def get_quanthub_history(
    product: str = "CLN26",
    endpoint_key: str = "ohlc_v2",
    limit: int = 300,
    db: Session = Depends(get_db),
):
    logger.info(
        f"GET /quanthub/history product={product}, endpoint_key={endpoint_key}, limit={limit}"
    )

    try:
        product_clean = product.lower().strip()
        endpoint_clean = endpoint_key.lower().strip()

        prefix = f"quanthub_{endpoint_clean}_{product_clean}_"

        rows = db.execute(
            select(RawObservation)
            .where(
                RawObservation.source == "QUANTHUB",
                RawObservation.series_name.like(f"{prefix}%"),
            )
            .order_by(RawObservation.timestamp.asc())
        ).scalars().all()

        raw_records = []

        for row in rows:
            field = row.series_name.replace(prefix, "")

            raw_records.append(
                {
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "product": product,
                    "endpoint_key": endpoint_key,
                    "field": field,
                    "series_name": row.series_name,
                    "value": row.raw_value,
                    "metadata": row.metadata_json or {},
                }
            )

        if not raw_records:
            return {
                "status": "empty",
                "product": product,
                "endpoint_key": endpoint_key,
                "count": 0,
                "latest": {},
                "ohlc": [],
                "raw_rows_count": 0,
                "message": "No stored QuantHub OHLC rows found.",
                "expected_prefix": prefix,
            }

        df = pd.DataFrame(raw_records)

        wide = (
            df.pivot_table(
                index="timestamp",
                columns="field",
                values="value",
                aggfunc="last",
            )
            .reset_index()
            .sort_values("timestamp")
            .tail(limit)
        )

        for col in ["open", "high", "low", "close", "volume"]:
            if col not in wide.columns:
                wide[col] = None

        ohlc_rows = wide[
            ["timestamp", "open", "high", "low", "close", "volume"]
        ].to_dict("records")

        latest = ohlc_rows[-1] if ohlc_rows else {}

        return {
            "status": "success",
            "product": product,
            "endpoint_key": endpoint_key,
            "count": len(ohlc_rows),
            "latest": latest,
            "ohlc": ohlc_rows,
            "raw_rows_count": len(raw_records),
            "expected_prefix": prefix,
        }

    except Exception as e:
        logger.exception("QuantHub history endpoint failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "quanthub_history_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.get("/debug/quanthub/raw")
def debug_quanthub_raw(
    product: str = "CLN26",
    endpoint_key: str = "ohlc_v2",
    limit: int = 25,
    db: Session = Depends(get_db),
):
    product_clean = product.lower().strip()
    endpoint_clean = endpoint_key.lower().strip()
    prefix = f"quanthub_{endpoint_clean}_{product_clean}_"

    rows = db.execute(
        select(RawObservation)
        .where(
            RawObservation.source == "QUANTHUB",
            RawObservation.series_name.like(f"{prefix}%"),
        )
        .order_by(RawObservation.timestamp.desc())
        .limit(limit)
    ).scalars().all()

    return {
        "status": "success",
        "product": product,
        "endpoint_key": endpoint_key,
        "expected_prefix": prefix,
        "count": len(rows),
        "rows": [
            {
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "series_name": row.series_name,
                "raw_value": row.raw_value,
                "metadata": row.metadata_json or {},
            }
            for row in rows
        ],
    }


@router.get("/debug/quanthub/counts")
def debug_quanthub_counts(
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(RawObservation)
        .where(RawObservation.source == "QUANTHUB")
        .order_by(RawObservation.series_name.asc())
    ).scalars().all()

    counts = {}

    for row in rows:
        counts[row.series_name] = counts.get(row.series_name, 0) + 1

    return {
        "status": "success",
        "source": "QUANTHUB",
        "total_rows": len(rows),
        "series_count": len(counts),
        "series_counts": counts,
    }


@router.get("/debug/qh-routes")
def debug_router_routes():
    return {
        "status": "success",
        "routes": [
            {
                "path": route.path,
                "name": route.name,
                "methods": sorted(list(route.methods)) if route.methods else [],
            }
            for route in router.routes
        ],
    }
