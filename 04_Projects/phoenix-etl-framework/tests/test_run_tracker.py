from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from phoenix_etl.run_tracker import (
    complete_pipeline_run,
    fail_pipeline_run,
    start_pipeline_run,
)


def create_connection_mock() -> tuple[MagicMock, MagicMock]:
    connection = MagicMock()
    context_connection = connection.__enter__.return_value
    cursor = context_connection.cursor.return_value.__enter__.return_value

    return connection, cursor


def test_start_pipeline_run() -> None:
    connection, cursor = create_connection_mock()

    started_at = datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc)

    with patch(
        "phoenix_etl.run_tracker.get_connection",
        return_value=connection,
    ):
        start_pipeline_run(
            pipeline_run_id="run-001",
            source_file="transactions.csv",
            started_at=started_at,
        )

    cursor.execute.assert_called_once()

    query, params = cursor.execute.call_args.args

    assert "INSERT INTO phoenix.pipeline_runs" in query
    assert params["pipeline_run_id"] == "run-001"
    assert params["source_file"] == "transactions.csv"
    assert params["started_at"] == started_at


def test_complete_pipeline_run() -> None:
    connection, cursor = create_connection_mock()

    completed_at = datetime(2026, 8, 12, 10, 5, tzinfo=timezone.utc)

    with patch(
        "phoenix_etl.run_tracker.get_connection",
        return_value=connection,
    ):
        complete_pipeline_run(
            pipeline_run_id="run-001",
            total_records=10,
            valid_records=8,
            rejected_records=2,
            completed_at=completed_at,
        )

    cursor.execute.assert_called_once()

    query, params = cursor.execute.call_args.args

    assert "UPDATE phoenix.pipeline_runs" in query
    assert params["pipeline_run_id"] == "run-001"
    assert params["total_records"] == 10
    assert params["valid_records"] == 8
    assert params["rejected_records"] == 2
    assert params["completed_at"] == completed_at


def test_fail_pipeline_run() -> None:
    connection, cursor = create_connection_mock()

    failed_at = datetime(2026, 8, 12, 10, 5, tzinfo=timezone.utc)

    with patch(
        "phoenix_etl.run_tracker.get_connection",
        return_value=connection,
    ):
        fail_pipeline_run(
            pipeline_run_id="run-001",
            error_message="Database connection failed",
            failed_at=failed_at,
        )

    cursor.execute.assert_called_once()

    query, params = cursor.execute.call_args.args

    assert "UPDATE phoenix.pipeline_runs" in query
    assert params["pipeline_run_id"] == "run-001"
    assert params["error_message"] == "Database connection failed"
    assert params["failed_at"] == failed_at
