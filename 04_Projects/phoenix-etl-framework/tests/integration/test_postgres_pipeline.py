from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from phoenix_etl.db import get_connection
from phoenix_etl.models import Transaction
from phoenix_etl.pipeline import process_file
from phoenix_etl.writer import write_transactions


@pytest.mark.integration
def test_process_file_persists_valid_and_rejected_records(
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

    pipeline_run_id = "integration-test-001"

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM phoenix.rejected_records
                WHERE pipeline_run_id = %(pipeline_run_id)s
                """,
                {"pipeline_run_id": pipeline_run_id},
            )

            cursor.execute(
                """
                DELETE FROM phoenix.pipeline_runs
                WHERE pipeline_run_id = %(pipeline_run_id)s
                """,
                {"pipeline_run_id": pipeline_run_id},
            )

            cursor.execute("""
                DELETE FROM phoenix.transactions
                WHERE transaction_id IN ('T001', 'T004', 'T005')
                """)

    result = process_file(
        csv_file,
        pipeline_run_id,
    )

    assert result.total_records == 5
    assert result.valid_count == 3
    assert result.rejected_count == 2

    # ------------------------------------------------------------------
    # Verify pipeline run metadata.
    # ------------------------------------------------------------------

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    pipeline_run_id,
                    source_file,
                    total_records,
                    valid_records,
                    rejected_records,
                    rejection_rate,
                    processing_duration_seconds,
                    records_per_second,
                    status,
                    started_at,
                    completed_at,
                    error_message
                FROM phoenix.pipeline_runs
                WHERE pipeline_run_id = %(pipeline_run_id)s
                """,
                {"pipeline_run_id": pipeline_run_id},
            )

            run = cursor.fetchone()

    assert run is not None

    assert run[0] == pipeline_run_id
    assert run[1] == str(csv_file)
    assert run[2] == 5
    assert run[3] == 3
    assert run[4] == 2
    assert run[5] == Decimal("0.400000")
    assert run[6] > 0
    assert run[7] > 0
    assert run[8] == "COMPLETED"
    assert run[9] is not None
    assert run[10] is not None
    assert run[11] is None

    # ------------------------------------------------------------------
    # Verify valid transactions.
    # ------------------------------------------------------------------

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT transaction_id
                FROM phoenix.transactions
                WHERE transaction_id IN ('T001', 'T004', 'T005')
                ORDER BY transaction_id
                """)

            rows = cursor.fetchall()

    transaction_ids = [row[0] for row in rows]

    assert transaction_ids == [
        "T001",
        "T004",
        "T005",
    ]

    # ------------------------------------------------------------------
    # Verify rejected records were persisted to PostgreSQL.
    # ------------------------------------------------------------------

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    pipeline_run_id,
                    source_file,
                    transaction_id,
                    rejection_reason,
                    original_record
                FROM phoenix.rejected_records
                WHERE pipeline_run_id = %(pipeline_run_id)s
                ORDER BY transaction_id
                """,
                {"pipeline_run_id": pipeline_run_id},
            )

            rejected_rows = cursor.fetchall()

    assert len(rejected_rows) == 2

    assert rejected_rows[0][0] == pipeline_run_id
    assert rejected_rows[0][1] == str(csv_file)
    assert rejected_rows[0][2] == "T002"
    assert rejected_rows[0][3] == "amount must be greater than or equal to 0"

    assert rejected_rows[1][0] == pipeline_run_id
    assert rejected_rows[1][1] == str(csv_file)
    assert rejected_rows[1][2] == "T003"
    assert rejected_rows[1][3] == "customer_id must not be empty"

    assert rejected_rows[0][4]["transaction_id"] == "T002"
    assert rejected_rows[0][4]["amount"] == "-100.00"

    assert rejected_rows[1][4]["transaction_id"] == "T003"
    assert rejected_rows[1][4]["customer_id"] == ""

    # ------------------------------------------------------------------
    # Cleanup.
    # ------------------------------------------------------------------

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM phoenix.rejected_records
                WHERE pipeline_run_id = %(pipeline_run_id)s
                """,
                {"pipeline_run_id": pipeline_run_id},
            )

            cursor.execute(
                """
                DELETE FROM phoenix.pipeline_runs
                WHERE pipeline_run_id = %(pipeline_run_id)s
                """,
                {"pipeline_run_id": pipeline_run_id},
            )

            cursor.execute("""
                DELETE FROM phoenix.transactions
                WHERE transaction_id IN ('T001', 'T004', 'T005')
                """)


@pytest.mark.integration
def test_process_file_records_failed_pipeline_run(
    tmp_path: Path,
) -> None:
    csv_file = tmp_path / "transactions.csv"

    csv_file.write_text(
        "transaction_id,customer_id,amount,currency,timestamp,source_updated_at\n"
        "T001,C001,1500.00,INR,2026-08-09T10:15:00,2026-08-09T10:20:00\n",
        encoding="utf-8",
    )

    pipeline_run_id = "integration-failure-test-001"

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM phoenix.pipeline_runs
                WHERE pipeline_run_id = %(pipeline_run_id)s
                """,
                {"pipeline_run_id": pipeline_run_id},
            )

    with pytest.raises(
        RuntimeError,
        match="simulated database failure",
    ):
        with patch(
            "phoenix_etl.pipeline.write_transactions",
            side_effect=RuntimeError("simulated database failure"),
        ):
            process_file(
                csv_file,
                pipeline_run_id,
            )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    pipeline_run_id,
                    source_file,
                    total_records,
                    valid_records,
                    rejected_records,
                    status,
                    started_at,
                    completed_at,
                    error_message
                FROM phoenix.pipeline_runs
                WHERE pipeline_run_id = %(pipeline_run_id)s
                """,
                {"pipeline_run_id": pipeline_run_id},
            )

            run = cursor.fetchone()

    assert run is not None

    assert run[0] == pipeline_run_id
    assert run[1] == str(csv_file)
    assert run[2] == 0
    assert run[3] == 0
    assert run[4] == 0
    assert run[5] == "FAILED"
    assert run[6] is not None
    assert run[7] is not None
    assert run[8] == "simulated database failure"


@pytest.mark.integration
def test_write_transactions_does_not_overwrite_newer_source_version() -> None:
    transaction_id = "IDEMPOTENCY-001"

    newer_version = Transaction(
        transaction_id=transaction_id,
        customer_id="C001",
        amount=Decimal("250.00"),
        currency="INR",
        timestamp=datetime(
            2026,
            8,
            16,
            10,
            30,
            tzinfo=timezone.utc,
        ),
        source_updated_at=datetime(
            2026,
            8,
            16,
            10,
            30,
            tzinfo=timezone.utc,
        ),
    )

    stale_version = Transaction(
        transaction_id=transaction_id,
        customer_id="C001",
        amount=Decimal("50.00"),
        currency="INR",
        timestamp=datetime(
            2026,
            8,
            16,
            9,
            0,
            tzinfo=timezone.utc,
        ),
        source_updated_at=datetime(
            2026,
            8,
            16,
            9,
            0,
            tzinfo=timezone.utc,
        ),
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM phoenix.transactions
                WHERE transaction_id = %(transaction_id)s
                """,
                {"transaction_id": transaction_id},
            )

    result = write_transactions([newer_version])

    assert result == 1

    result = write_transactions([stale_version])

    assert result == 1

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    transaction_id,
                    customer_id,
                    amount,
                    currency,
                    timestamp,
                    source_updated_at
                FROM phoenix.transactions
                WHERE transaction_id = %(transaction_id)s
                """,
                {"transaction_id": transaction_id},
            )

            row = cursor.fetchone()

    assert row is not None

    assert row[0] == transaction_id
    assert row[1] == "C001"
    assert row[2] == Decimal("250.00")
    assert row[3] == "INR"

    assert row[4] == datetime(
        2026,
        8,
        16,
        10,
        30,
        tzinfo=timezone.utc,
    )

    assert row[5] == datetime(
        2026,
        8,
        16,
        10,
        30,
        tzinfo=timezone.utc,
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM phoenix.transactions
                WHERE transaction_id = %(transaction_id)s
                """,
                {"transaction_id": transaction_id},
            )
