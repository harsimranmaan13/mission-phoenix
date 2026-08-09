from pathlib import Path

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

    result = process_file(csv_file, "run-001")

    assert result.total_records == 5
    assert result.valid_count == 3
    assert result.rejected_count == 2

    assert [record.transaction_id for record in result.valid_records] == [
        "T001",
        "T004",
        "T005",
    ]

    assert [
        record.original_record["transaction_id"] for record in result.rejected_records
    ] == [
        "T002",
        "T003",
    ]


def test_process_file_preserves_pipeline_run_id(
    tmp_path: Path,
) -> None:
    csv_file = tmp_path / "transactions.csv"

    csv_file.write_text(
        "transaction_id,customer_id,amount,currency,timestamp,source_updated_at\n"
        "T001,,1500.00,INR,2026-08-09T10:15:00,2026-08-09T10:20:00\n",
        encoding="utf-8",
    )

    result = process_file(csv_file, "run-123")

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

    result = process_file(csv_file, "run-001")

    assert result.total_records == 5
    assert result.valid_count == 3
    assert result.rejected_count == 2

    rejected_file = tmp_path / "rejected_records.csv"

    assert rejected_file.exists()

    content = rejected_file.read_text(encoding="utf-8")

    assert "T002" in content
    assert "T003" in content
    assert "run-001" in content
    assert "amount must be greater than or equal to 0" in content
    assert "customer_id must not be empty" in content
