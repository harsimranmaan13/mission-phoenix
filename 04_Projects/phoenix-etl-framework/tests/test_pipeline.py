from pathlib import Path
from unittest.mock import patch

from phoenix_etl.pipeline import process_file


def test_process_file_separates_valid_and_invalid_records(
    tmp_path: Path,
) -> None:
    csv_file = tmp_path / "transactions.csv"

    csv_file.write_text(
        "transaction_id,customer_id,amount,currency,timestamp,source_updated_at\n"
        "T001,C001,1500.00,INR,2026-08-09T10:15:00,2026-08-09T10:20:00\n"
        "T002,C002,-100.00,INR,2026-08-09T10:16:00,2026-08-09T10:21:00\n"
        "T003,,500.00,INR,2026-08-09T10:17:00,2026-08-09T10:22:00\n"
        "T004,C004,3000.00,USD,2026-08-09T10:18:00,2026-08-09T10:23:00\n"
        "T005,C005,250.75,EUR,2026-08-09T10:19:00,2026-08-09T10:24:00\n",
        encoding="utf-8",
    )

    with (
        patch("phoenix_etl.pipeline.start_pipeline_run"),
        patch("phoenix_etl.pipeline.complete_pipeline_run"),
        patch("phoenix_etl.pipeline.fail_pipeline_run"),
        patch("phoenix_etl.pipeline.write_transactions"),
        patch("phoenix_etl.pipeline.write_rejected_records_to_db"),
    ):
        result = process_file(csv_file, "run-001")

    assert result.total_records == 5
    assert result.valid_count == 3
    assert result.rejected_count == 2

    valid_ids = [record.transaction_id for record in result.valid_records]

    rejected_ids = [
        record.original_record["transaction_id"] for record in result.rejected_records
    ]

    assert valid_ids == ["T001", "T004", "T005"]
    assert rejected_ids == ["T002", "T003"]


def test_process_file_preserves_pipeline_run_id(
    tmp_path: Path,
) -> None:
    csv_file = tmp_path / "transactions.csv"

    csv_file.write_text(
        "transaction_id,customer_id,amount,currency,timestamp,source_updated_at\n"
        "T001,,1500.00,INR,2026-08-09T10:15:00,2026-08-09T10:20:00\n",
        encoding="utf-8",
    )

    with (
        patch("phoenix_etl.pipeline.start_pipeline_run"),
        patch("phoenix_etl.pipeline.complete_pipeline_run"),
        patch("phoenix_etl.pipeline.fail_pipeline_run"),
        patch("phoenix_etl.pipeline.write_transactions"),
        patch("phoenix_etl.pipeline.write_rejected_records_to_db"),
    ):
        result = process_file(csv_file, "run-123")

    assert result.total_records == 1
    assert result.valid_count == 0
    assert result.rejected_count == 1
    assert result.rejected_records[0].pipeline_run_id == "run-123"


def test_process_file_writes_rejected_records(
    tmp_path: Path,
) -> None:
    csv_file = tmp_path / "transactions.csv"

    csv_file.write_text(
        "transaction_id,customer_id,amount,currency,timestamp,source_updated_at\n"
        "T001,C001,1500.00,INR,2026-08-09T10:15:00,2026-08-09T10:20:00\n"
        "T002,C002,-100.00,INR,2026-08-09T10:16:00,2026-08-09T10:21:00\n"
        "T003,,500.00,INR,2026-08-09T10:17:00,2026-08-09T10:22:00\n"
        "T004,C004,3000.00,USD,2026-08-09T10:18:00,2026-08-09T10:23:00\n"
        "T005,C005,250.75,EUR,2026-08-09T10:19:00,2026-08-09T10:24:00\n",
        encoding="utf-8",
    )

    with (
        patch("phoenix_etl.pipeline.start_pipeline_run"),
        patch("phoenix_etl.pipeline.complete_pipeline_run"),
        patch("phoenix_etl.pipeline.fail_pipeline_run"),
        patch("phoenix_etl.pipeline.write_transactions"),
        patch("phoenix_etl.pipeline.write_rejected_records_to_db"),
    ):
        result = process_file(csv_file, "run-001")

    assert result.rejected_count == 2

    rejected_path = tmp_path / "rejected_records.csv"

    assert rejected_path.exists()

    content = rejected_path.read_text(encoding="utf-8")

    assert "T002" in content
    assert "T003" in content
    assert "run-001" in content
