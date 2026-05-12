import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

APP_LOG_FILE = LOG_DIR / "oilintel_app.log"
EIA_LOG_FILE = LOG_DIR / "eia_pdf_debug.log"


def setup_logging():
    """
    Central logging configuration.

    Creates:
    - logs/oilintel_app.log
    - logs/eia_pdf_debug.log

    Also prints logs to terminal.
    """

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Prevent duplicate logs after uvicorn reload.
    if root_logger.handlers:
        root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    app_file_handler = RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    app_file_handler.setLevel(logging.DEBUG)
    app_file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_file_handler)

    # Dedicated EIA PDF logger.
    eia_logger = logging.getLogger("eia_pdf")
    eia_logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate EIA file handlers.
    eia_logger.handlers.clear()

    eia_file_handler = RotatingFileHandler(
        EIA_LOG_FILE,
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    eia_file_handler.setLevel(logging.DEBUG)
    eia_file_handler.setFormatter(formatter)

    eia_logger.addHandler(eia_file_handler)
    eia_logger.propagate = True

    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    root_logger.info("Logging initialized")
    root_logger.info(f"App log file: {APP_LOG_FILE}")
    root_logger.info(f"EIA log file: {EIA_LOG_FILE}")
