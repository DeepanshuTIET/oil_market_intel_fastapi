from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    Text,
    Float,
    JSON,
    PrimaryKeyConstraint,
    UniqueConstraint,
    func,
)

from app.db.session import Base


class RawObservation(Base):
    __tablename__ = "raw_observations"

    # IMPORTANT:
    # SQLite autoincrement requires INTEGER PRIMARY KEY.
    # BigInteger will cause: NOT NULL constraint failed: raw_observations.id
    id = Column(Integer, primary_key=True, autoincrement=True)

    timestamp = Column(DateTime(timezone=True), nullable=False)
    source = Column(Text, nullable=False)
    series_name = Column(Text, nullable=False)
    raw_value = Column(Float)
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "timestamp",
            "source",
            "series_name",
            name="uq_raw_obs",
        ),
    )


class OilFeature(Base):
    __tablename__ = "oil_features"

    timestamp = Column(DateTime(timezone=True), nullable=False)
    feature_name = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    raw_value = Column(Float)
    standardized_value = Column(Float, nullable=False)
    confidence = Column(Float, default=1.0)
    decay = Column(Float, default=1.0)
    horizon = Column(Text, default="5d")
    directional_impact = Column(Text)
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        PrimaryKeyConstraint(
            "timestamp",
            "feature_name",
        ),
    )


class OilPrice(Base):
    __tablename__ = "oil_prices"

    timestamp = Column(DateTime(timezone=True), nullable=False)
    instrument = Column(Text, nullable=False)
    close = Column(Float, nullable=False)
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        PrimaryKeyConstraint(
            "timestamp",
            "instrument",
        ),
    )


class OilSignal(Base):
    __tablename__ = "oil_signals"

    timestamp = Column(DateTime(timezone=True), nullable=False)
    instrument = Column(Text, nullable=False)
    horizon = Column(Text, nullable=False)
    probability_up = Column(Float, nullable=False)
    probability_down = Column(Float, nullable=False)
    expected_return = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    signal = Column(Text, nullable=False)
    regime = Column(Text)
    feature_contributions = Column(JSON, default=dict)
    feature_zscores = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        PrimaryKeyConstraint(
            "timestamp",
            "instrument",
            "horizon",
        ),
    )