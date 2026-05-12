import math
from datetime import datetime, timezone

import pandas as pd

from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.db.models import RawObservation, OilFeature, OilSignal


def clean_value(value):
    """
    Make values SQLite-safe and JSON-safe.

    Key fix:
    SQLite does not handle timezone-aware datetime primary keys reliably.
    So we convert all datetimes to timezone-naive UTC before storing.
    """

    if value is None:
        return None

    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None

        # Convert timezone-aware pandas Timestamp to UTC naive datetime.
        if value.tzinfo is not None:
            value = value.tz_convert("UTC").tz_localize(None)

        return value.to_pydatetime()

    if isinstance(value, datetime):
        # Convert timezone-aware datetime to UTC naive datetime.
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)

        return value

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

        return value

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    return value


def clean_dict(d: dict) -> dict:
    if not d:
        return {}

    out = {}

    for key, value in d.items():
        if isinstance(value, dict):
            out[key] = clean_dict(value)

        elif isinstance(value, list):
            out[key] = [clean_value(item) for item in value]

        else:
            out[key] = clean_value(value)

    return out


def upsert_raw(db: Session, records: list[dict]) -> int:
    """
    SQLite-safe upsert for raw observations.

    Unique key:
        timestamp + source + series_name
    """

    if not records:
        return 0

    written = 0

    try:
        for record in records:
            timestamp = clean_value(record.get("timestamp"))
            source = record.get("source")
            series_name = record.get("series_name")

            if timestamp is None or not source or not series_name:
                continue

            existing = db.execute(
                select(RawObservation).where(
                    RawObservation.timestamp == timestamp,
                    RawObservation.source == source,
                    RawObservation.series_name == series_name,
                )
            ).scalar_one_or_none()

            if existing:
                existing.raw_value = clean_value(record.get("raw_value"))
                existing.metadata_json = clean_dict(record.get("metadata", {}))

            else:
                obj = RawObservation(
                    timestamp=timestamp,
                    source=source,
                    series_name=series_name,
                    raw_value=clean_value(record.get("raw_value")),
                    metadata_json=clean_dict(record.get("metadata", {})),
                )

                db.add(obj)

            written += 1

        db.commit()

        return written

    except Exception:
        db.rollback()
        raise


def upsert_features(db: Session, records: list[dict]) -> int:
    """
    SQLite-safe upsert for engineered features.

    Unique key:
        timestamp + feature_name
    """

    if not records:
        return 0

    written = 0

    try:
        for record in records:
            timestamp = clean_value(record.get("timestamp"))
            feature_name = record.get("feature_name")

            if timestamp is None or not feature_name:
                continue

            standardized_value = clean_value(record.get("standardized_value"))

            if standardized_value is None:
                continue

            existing = db.execute(
                select(OilFeature).where(
                    OilFeature.timestamp == timestamp,
                    OilFeature.feature_name == feature_name,
                )
            ).scalar_one_or_none()

            if existing:
                existing.source = record.get("source")
                existing.raw_value = clean_value(record.get("raw_value"))
                existing.standardized_value = standardized_value
                existing.confidence = clean_value(record.get("confidence", 1.0)) or 1.0
                existing.decay = clean_value(record.get("decay", 1.0)) or 1.0
                existing.horizon = record.get("horizon", "5d")
                existing.directional_impact = record.get("directional_impact")
                existing.metadata_json = clean_dict(record.get("metadata", {}))

            else:
                obj = OilFeature(
                    timestamp=timestamp,
                    feature_name=feature_name,
                    source=record.get("source"),
                    raw_value=clean_value(record.get("raw_value")),
                    standardized_value=standardized_value,
                    confidence=clean_value(record.get("confidence", 1.0)) or 1.0,
                    decay=clean_value(record.get("decay", 1.0)) or 1.0,
                    horizon=record.get("horizon", "5d"),
                    directional_impact=record.get("directional_impact"),
                    metadata_json=clean_dict(record.get("metadata", {})),
                )

                db.add(obj)

            written += 1

        db.commit()

        return written

    except Exception:
        db.rollback()
        raise


def load_raw_df(db: Session) -> pd.DataFrame:
    rows = db.execute(
        select(RawObservation).order_by(RawObservation.timestamp)
    ).scalars().all()

    data = []

    for row in rows:
        data.append(
            {
                "timestamp": row.timestamp,
                "source": row.source,
                "series_name": row.series_name,
                "raw_value": row.raw_value,
                "metadata": row.metadata_json,
            }
        )

    return pd.DataFrame(data)


def load_feature_matrix(
    db: Session,
    limit_days: int = 1000,
) -> pd.DataFrame:
    rows = db.execute(
        select(OilFeature).order_by(OilFeature.timestamp)
    ).scalars().all()

    data = []

    for row in rows:
        data.append(
            {
                "timestamp": row.timestamp,
                "feature_name": row.feature_name,
                "value": row.standardized_value,
            }
        )

    df = pd.DataFrame(data)

    if df.empty:
        return df

    matrix = df.pivot_table(
        index="timestamp",
        columns="feature_name",
        values="value",
        aggfunc="last",
    ).sort_index()

    return matrix.tail(limit_days)


def latest_features(db: Session) -> list[dict]:
    rows = db.execute(
        select(OilFeature)
        .order_by(desc(OilFeature.timestamp))
        .limit(200)
    ).scalars().all()

    output = []

    for row in rows:
        output.append(
            {
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "feature_name": row.feature_name,
                "source": row.source,
                "raw_value": row.raw_value,
                "standardized_value": row.standardized_value,
                "confidence": row.confidence,
                "decay": row.decay,
                "horizon": row.horizon,
                "directional_impact": row.directional_impact,
                "metadata": row.metadata_json,
            }
        )

    return output


def upsert_signal(db: Session, record: dict) -> None:
    """
    SQLite-safe upsert for signals.

    Unique key:
        timestamp + instrument + horizon
    """

    timestamp = clean_value(record.get("timestamp"))
    instrument = record.get("instrument")
    horizon = record.get("horizon")

    if timestamp is None or not instrument or not horizon:
        raise ValueError("Signal requires timestamp, instrument, and horizon")

    try:
        existing = db.execute(
            select(OilSignal).where(
                OilSignal.timestamp == timestamp,
                OilSignal.instrument == instrument,
                OilSignal.horizon == horizon,
            )
        ).scalar_one_or_none()

        if existing:
            existing.probability_up = clean_value(record.get("probability_up"))
            existing.probability_down = clean_value(record.get("probability_down"))
            existing.expected_return = clean_value(record.get("expected_return"))
            existing.confidence = clean_value(record.get("confidence"))
            existing.signal = record.get("signal")
            existing.regime = record.get("regime")
            existing.feature_contributions = clean_dict(
                record.get("feature_contributions", {})
            )
            existing.feature_zscores = clean_dict(
                record.get("feature_zscores", {})
            )

        else:
            obj = OilSignal(
                timestamp=timestamp,
                instrument=instrument,
                horizon=horizon,
                probability_up=clean_value(record.get("probability_up")),
                probability_down=clean_value(record.get("probability_down")),
                expected_return=clean_value(record.get("expected_return")),
                confidence=clean_value(record.get("confidence")),
                signal=record.get("signal"),
                regime=record.get("regime"),
                feature_contributions=clean_dict(
                    record.get("feature_contributions", {})
                ),
                feature_zscores=clean_dict(
                    record.get("feature_zscores", {})
                ),
            )

            db.add(obj)

        db.commit()

    except Exception:
        db.rollback()
        raise


def latest_signal(
    db: Session,
    instrument: str,
    horizon: str,
):
    return db.execute(
        select(OilSignal)
        .where(
            OilSignal.instrument == instrument,
            OilSignal.horizon == horizon,
        )
        .order_by(desc(OilSignal.timestamp))
        .limit(1)
    ).scalar_one_or_none()