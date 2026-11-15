"""
StoryForge AI - Structured Logging Configuration

File + console handlers with structured formatting.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured, readable log lines."""

    LEVEL_COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = False):
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = record.levelname.ljust(8)
        module = f"{record.name}:{record.lineno}"

        if self.use_colors:
            color = self.LEVEL_COLORS.get(record.levelname, "")
            level = f"{color}{level}{self.RESET}"

        message = record.getMessage()

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            message += "\n" + self.formatException(record.exc_info)

        return f"[{timestamp}] {level} | {module:<40} | {message}"


def setup_logging() -> None:
    """Configure application-wide logging with file and console handlers."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Ensure log directory exists
    log_dir = settings.logs_path
    log_dir.mkdir(parents=True, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers to avoid duplicates on reload
    root_logger.handlers.clear()

    # ── Console handler ──────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(StructuredFormatter(use_colors=True))
    root_logger.addHandler(console_handler)

    # ── File handler (general) ───────────────────────────────────────
    log_file = log_dir / "storyforge.log"
    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(StructuredFormatter(use_colors=False))
    root_logger.addHandler(file_handler)

    # ── File handler (errors only) ───────────────────────────────────
    error_file = log_dir / "errors.log"
    error_handler = logging.FileHandler(str(error_file), encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter(use_colors=False))
    root_logger.addHandler(error_handler)

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    root_logger.info("Logging configured — level=%s, log_dir=%s", logging.getLevelName(log_level), log_dir)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger for a module."""
    return logging.getLogger(name)
