import os
import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings


def setup_logging():
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Log file path
    log_file = log_dir / "x-scheduler.log"

    # Configure loguru
    config = {
        "handlers": [
            {
                "sink": sys.stdout,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                "level": settings.LOG_LEVEL,
            },
            {
                "sink": str(log_file),
                "rotation": "10 MB",
                "retention": "1 week",
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                "level": settings.LOG_LEVEL,
            },
        ],
    }

    # Remove default logger and apply configuration
    logger.remove()
    for handler in config["handlers"]:
        logger.add(**handler)

    logger.info(f"Logging configured with level: {settings.LOG_LEVEL}")

    return logger
