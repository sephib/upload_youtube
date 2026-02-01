# Edited by Claude Code
"""Structured logging setup using loguru for Torah Sync application."""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(
    log_level: str = "INFO",
    log_file: Path | None = None,
    use_json: bool = False,
) -> None:
    """Configure application logging using loguru.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        use_json: Whether to use JSON formatting (loguru serializes automatically)

    Example:
        >>> setup_logging(log_level="DEBUG", use_json=True)
        >>> logger.info("Processing started", parasha="האזינו", aliyah="ראשון")
    """
    # Remove default handler
    logger.remove()

    # Console handler with optional JSON serialization
    if use_json:
        # JSON format with automatic serialization
        logger.add(
            sys.stdout,
            level=log_level.upper(),
            format="{message}",
            serialize=True,  # Automatic JSON serialization
        )
    else:
        # Human-readable format
        logger.add(
            sys.stdout,
            level=log_level.upper(),
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            colorize=True,
        )

    # File handler if log file specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        if use_json:
            # JSON format for file
            logger.add(
                log_file,
                level=log_level.upper(),
                format="{message}",
                serialize=True,
                rotation="10 MB",  # Rotate when file reaches 10MB
                retention="1 week",  # Keep logs for 1 week
                compression="zip",  # Compress rotated logs
            )
        else:
            # Plain text for file
            logger.add(
                log_file,
                level=log_level.upper(),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
                rotation="10 MB",
                retention="1 week",
                compression="zip",
            )


def get_logger(name: str | None = None):
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__). With loguru, this is optional
              as context is automatically tracked.

    Returns:
        Configured logger instance (loguru's global logger)

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.debug(f"{file_path=}, {duration=}")
        # Output: file_path='audio.mp4', duration=612.5
    """
    # loguru uses a global logger, so we just return it
    # Context can be added with logger.bind() if needed
    if name:
        return logger.bind(module=name)
    return logger
