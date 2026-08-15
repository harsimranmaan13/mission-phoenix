import logging

LOGGER_NAME = "phoenix_etl"


def get_logger(name: str | None = None) -> logging.Logger:
    """Return the Phoenix ETL application logger."""

    logger_name = LOGGER_NAME if name is None else f"{LOGGER_NAME}.{name}"

    return logging.getLogger(logger_name)


def configure_logging(
    level: int = logging.INFO,
) -> None:
    """Configure application-wide logging for Phoenix ETL."""

    logger = logging.getLogger(LOGGER_NAME)

    if logger.handlers:
        logger.setLevel(level)
        return

    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
