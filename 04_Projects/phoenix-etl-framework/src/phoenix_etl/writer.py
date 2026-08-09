import json
from collections.abc import Sequence
from csv import DictReader, DictWriter
from pathlib import Path

from phoenix_etl.db import get_connection
from phoenix_etl.models import RejectedRecord, Transaction


def write_transactions(records: Sequence[Transaction]) -> int:
    """Insert new transactions or update them when the source version is newer."""

    if not records:
        return 0

    query = """
        INSERT INTO phoenix.transactions (
            transaction_id,
            customer_id,
            amount,
            currency,
            timestamp,
            source_updated_at
        )
        VALUES (
            %(transaction_id)s,
            %(customer_id)s,
            %(amount)s,
            %(currency)s,
            %(timestamp)s,
            %(source_updated_at)s
        )
        ON CONFLICT (transaction_id)
        DO UPDATE SET
            customer_id = EXCLUDED.customer_id,
            amount = EXCLUDED.amount,
            currency = EXCLUDED.currency,
            timestamp = EXCLUDED.timestamp,
            source_updated_at = EXCLUDED.source_updated_at
        WHERE EXCLUDED.source_updated_at >
              phoenix.transactions.source_updated_at
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for record in records:
                cursor.execute(
                    query,
                    record.model_dump(),
                )

    return len(records)


def write_rejected_records(
    records: Sequence[RejectedRecord],
    output_path: Path,
) -> int:
    """Append unique rejected records to the rejected-records CSV file."""

    if not records:
        return 0

    fieldnames = [
        "pipeline_run_id",
        "source_file",
        "rejected_at",
        "transaction_id",
        "rejection_reason",
        "original_record",
    ]

    existing_keys: set[tuple[str, str | None]] = set()

    if output_path.exists() and output_path.stat().st_size > 0:
        with output_path.open(
            "r",
            newline="",
            encoding="utf-8",
        ) as file:
            reader = DictReader(file)

            for row in reader:
                existing_keys.add(
                    (
                        row["pipeline_run_id"],
                        row["transaction_id"],
                    )
                )

    file_exists = output_path.exists() and output_path.stat().st_size > 0

    written_count = 0

    with output_path.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for record in records:
            data = record.model_dump()

            transaction_id = data["original_record"].get("transaction_id")

            key = (
                data["pipeline_run_id"],
                transaction_id,
            )

            if key in existing_keys:
                continue

            writer.writerow(
                {
                    "pipeline_run_id": data["pipeline_run_id"],
                    "source_file": data["source_file"],
                    "rejected_at": data["rejected_at"].isoformat(),
                    "transaction_id": transaction_id,
                    "rejection_reason": data["rejection_reason"],
                    "original_record": json.dumps(
                        data["original_record"],
                    ),
                }
            )

            existing_keys.add(key)
            written_count += 1

    return written_count
