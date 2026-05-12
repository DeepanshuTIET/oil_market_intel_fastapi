from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Oil Market Intelligence API"
    ENV: str = "dev"

    DATABASE_URL: str = "sqlite:///./oilintel.db"

    # EIA now uses public WPSR PDF, but key can remain optional.
    EIA_API_KEY: str | None = None

    # X / Twitter
    X_BEARER_TOKEN: str | None = None

    # QuantHub new auth flow
    QUANTHUB_BASE_URL: str = "https://qh-api.corp.hertshtengroup.com"

    QUANTHUB_USERNAME: str | None = None
    QUANTHUB_PASSWORD: str | None = None
    
    QUANTHUB_ACCESS_TOKEN: str | None = None
    QUANTHUB_REFRESH_TOKEN: str | None = None

    # Legacy compatibility so old references do not crash
    QUANTHUB_API_KEY: str | None = None
    QUANTHUB_EVENTS_ENDPOINT: str | None = None

    NEWS_API_KEY: str | None = None
    TEAMS_WEBHOOK_URL: str | None = None

    WTI_SYMBOL: str = "WTI"
    BRENT_SYMBOL: str = "BRENT"

    # CFTC COT Petroleum URLs
    CFTC_PETROLEUM_FUTURES_URL: str = "https://www.cftc.gov/dea/futures/petroleum_lf.htm"
    CFTC_PETROLEUM_OPTIONS_URL: str = "https://www.cftc.gov/dea/options/petroleum_lof.htm"
    CFTC_DEFAULT_MODE: str = "futures"


settings = Settings()