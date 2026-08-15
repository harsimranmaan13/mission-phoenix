import logging

from phoenix_etl.logging_config import get_logger


def test_get_logger_returns_phoenix_etl_logger() -> None:
    logger = get_logger()

    assert logger.name == "phoenix_etl"


def test_get_logger_returns_named_child_logger() -> None:
    logger = get_logger("pipeline")

    assert logger.name == "phoenix_etl.pipeline"


def test_get_logger_returns_same_logger_for_same_name() -> None:
    first_logger = get_logger("pipeline")
    second_logger = get_logger("pipeline")

    assert first_logger is second_logger


def test_logger_is_logging_logger() -> None:
    logger = get_logger("pipeline")

    assert isinstance(logger, logging.Logger)
