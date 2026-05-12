CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS raw_observations (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    series_name TEXT NOT NULL,
    raw_value DOUBLE PRECISION,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, source, series_name)
);
SELECT create_hypertable('raw_observations', 'timestamp', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS oil_features (
    timestamp TIMESTAMPTZ NOT NULL,
    feature_name TEXT NOT NULL,
    source TEXT NOT NULL,
    raw_value DOUBLE PRECISION,
    standardized_value DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    decay DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    horizon TEXT NOT NULL DEFAULT '5d',
    directional_impact TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY(timestamp, feature_name)
);
SELECT create_hypertable('oil_features', 'timestamp', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS oil_prices (
    timestamp TIMESTAMPTZ NOT NULL,
    instrument TEXT NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY(timestamp, instrument)
);
SELECT create_hypertable('oil_prices', 'timestamp', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS oil_signals (
    timestamp TIMESTAMPTZ NOT NULL,
    instrument TEXT NOT NULL,
    horizon TEXT NOT NULL,
    probability_up DOUBLE PRECISION NOT NULL,
    probability_down DOUBLE PRECISION NOT NULL,
    expected_return DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    signal TEXT NOT NULL,
    regime TEXT,
    feature_contributions JSONB DEFAULT '{}'::jsonb,
    feature_zscores JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY(timestamp, instrument, horizon)
);
SELECT create_hypertable('oil_signals', 'timestamp', if_not_exists => TRUE);
