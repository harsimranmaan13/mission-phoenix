import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from phoenix_etl.models import RejectedRecord
from phoenix_etl.writer import write_rejected_records


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


def read_rows(output_path: Path) -> list[dict[str, str]]:
    with output_path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


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
