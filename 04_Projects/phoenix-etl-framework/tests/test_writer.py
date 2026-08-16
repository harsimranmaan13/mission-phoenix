import csv
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from phoenix_etl.models import RejectedRecord, Transaction
from phoenix_etl.writer import (
    write_rejected_records,
    write_rejected_records_to_db,
    write_transactions,
)


def create_rejected_record(
    transaction_id: str,
    pipeline_run_id: str,
) -> RejectedRecord:
    return RejectedRecord(
        original_record={
            "transaction_id": transaction_id,
            "customer_id": "C001",
            "amount": "-100.00",
            "currency": "INR",
            "timestamp": "2026-08-09T10:15:00",
            "source_updated_at": "2026-08-09T10:20:00",
        },
        rejection_reason="amount must be greater than or equal to 0",
        source_file="transactions.csv",
        pipeline_run_id=pipeline_run_id,
        rejected_at=datetime(
            2026,
            8,
            9,
            10,
            30,
            tzinfo=timezone.utc,
        ),
    )


def create_transaction(
    transaction_id: str = "T001",
    customer_id: str = "C001",
    amount: str = "1500.00",
    currency: str = "INR",
    timestamp: datetime | None = None,
    source_updated_at: datetime | None = None,
) -> Transaction:
    if timestamp is None:
        timestamp = datetime(
            2026,
            8,
            9,
            10,
            15,
            tzinfo=timezone.utc,
        )

    if source_updated_at is None:
        source_updated_at = datetime(
            2026,
            8,
            9,
            10,
            20,
            tzinfo=timezone.utc,
        )

    return Transaction(
        transaction_id=transaction_id,
        customer_id=customer_id,
        amount=Decimal(amount),
        currency=currency,
        timestamp=timestamp,
        source_updated_at=source_updated_at,
    )


def read_rows(output_path: Path) -> list[dict[str, str]]:
    with output_path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


# ---------------------------------------------------------------------------
# Transaction writer tests
# ---------------------------------------------------------------------------


def test_write_transactions_empty_records() -> None:
    with patch("phoenix_etl.writer.get_connection") as mock_connection:
        result = write_transactions([])

    assert result == 0
    mock_connection.assert_not_called()


def test_write_transactions_inserts_transactions() -> None:
    transaction = create_transaction()

    with patch("phoenix_etl.writer.get_connection") as mock_connection:
        connection = mock_connection.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value

        result = write_transactions([transaction])

    assert result == 1

    cursor.execute.assert_called_once()

    query, params = cursor.execute.call_args.args

    assert "INSERT INTO phoenix.transactions" in query
    assert "ON CONFLICT (transaction_id)" in query
    assert "DO UPDATE SET" in query
    assert "EXCLUDED.source_updated_at" in query

    assert params["transaction_id"] == "T001"
    assert params["customer_id"] == "C001"
    assert params["amount"] == Decimal("1500.00")
    assert params["currency"] == "INR"


def test_write_transactions_uses_source_updated_at_for_idempotency() -> None:
    transaction = create_transaction()

    with patch("phoenix_etl.writer.get_connection") as mock_connection:
        connection = mock_connection.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value

        write_transactions([transaction])

    query, _ = cursor.execute.call_args.args

    assert "WHERE EXCLUDED.source_updated_at >" in query
    assert "phoenix.transactions.source_updated_at" in query


# ---------------------------------------------------------------------------
# Rejected-record CSV tests
# ---------------------------------------------------------------------------


def test_write_rejected_records(tmp_path: Path) -> None:
    output_path = tmp_path / "rejected_records.csv"

    record = create_rejected_record("T002", "run-001")

    write_rejected_records([record], output_path)

    assert output_path.exists()

    rows = read_rows(output_path)

    assert len(rows) == 1
    assert rows[0]["pipeline_run_id"] == "run-001"
    assert rows[0]["source_file"] == "transactions.csv"
    assert rows[0]["transaction_id"] == "T002"
    assert rows[0]["rejection_reason"] == ("amount must be greater than or equal to 0")

    original_record = json.loads(rows[0]["original_record"])

    assert original_record["transaction_id"] == "T002"
    assert original_record["amount"] == "-100.00"


def test_write_rejected_records_appends_new_run(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "rejected_records.csv"

    write_rejected_records(
        [create_rejected_record("T002", "run-001")],
        output_path,
    )

    write_rejected_records(
        [create_rejected_record("T003", "run-002")],
        output_path,
    )

    rows = read_rows(output_path)

    assert len(rows) == 2
    assert rows[0]["transaction_id"] == "T002"
    assert rows[1]["transaction_id"] == "T003"


def test_same_run_same_transaction_is_not_duplicated(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "rejected_records.csv"

    record = create_rejected_record("T002", "run-001")

    write_rejected_records([record], output_path)
    write_rejected_records([record], output_path)

    rows = read_rows(output_path)

    assert len(rows) == 1


def test_same_transaction_in_different_runs_is_preserved(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "rejected_records.csv"

    write_rejected_records(
        [create_rejected_record("T002", "run-001")],
        output_path,
    )

    write_rejected_records(
        [create_rejected_record("T002", "run-002")],
        output_path,
    )

    rows = read_rows(output_path)

    assert len(rows) == 2
    assert rows[0]["pipeline_run_id"] == "run-001"
    assert rows[1]["pipeline_run_id"] == "run-002"


def test_empty_records_do_not_create_file(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "rejected_records.csv"

    write_rejected_records([], output_path)

    assert not output_path.exists()


# ---------------------------------------------------------------------------
# Rejected-record PostgreSQL writer tests
# ---------------------------------------------------------------------------


def test_write_rejected_records_to_db() -> None:
    record = create_rejected_record("T002", "run-001")

    with patch("phoenix_etl.writer.get_connection") as mock_connection:
        connection = mock_connection.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value

        result = write_rejected_records_to_db([record])

    assert result == 1

    cursor.execute.assert_called_once()

    query, params = cursor.execute.call_args.args

    assert "INSERT INTO phoenix.rejected_records" in query
    assert params["pipeline_run_id"] == "run-001"
    assert params["transaction_id"] == "T002"
    assert params["rejection_reason"] == ("amount must be greater than or equal to 0")


def test_write_rejected_records_to_db_empty_records() -> None:
    with patch("phoenix_etl.writer.get_connection") as mock_connection:
        result = write_rejected_records_to_db([])

    assert result == 0
    mock_connection.assert_not_called()
