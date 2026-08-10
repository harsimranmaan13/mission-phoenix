from pathlib import Path

import pytest

from phoenix_etl.db import get_connection
from phoenix_etl.pipeline import process_file


@pytest.mark.integration
def test_process_file_persists_valid_transactions(
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
            cursor.execute("""
                DELETE FROM phoenix.transactions
                WHERE transaction_id IN ('T001', 'T004', 'T005')
                """)

    result = process_file(csv_file, pipeline_run_id)

    assert result.total_records == 5
    assert result.valid_count == 3
    assert result.rejected_count == 2

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

    assert transaction_ids == ["T001", "T004", "T005"]
