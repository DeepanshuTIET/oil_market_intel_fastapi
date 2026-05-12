from datetime import datetime
from pydantic import BaseModel, Field


class StandardizedFeatureIn(BaseModel):
    timestamp: datetime
    feature_name: str
    source: str
    raw_value: float | None = None
    standardized_value: float
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    decay: float = Field(default=1.0, ge=0.0, le=1.0)
    horizon: str = '5d'
    directional_impact: str | None = None
    metadata: dict = Field(default_factory=dict)


class SignalOut(BaseModel):
    timestamp: datetime
    instrument: str
    horizon: str
    probability_up: float
    probability_down: float
    expected_return: float
    confidence: float
    signal: str
    regime: str | None = None
    feature_contributions: dict = Field(default_factory=dict)
    feature_zscores: dict = Field(default_factory=dict)
