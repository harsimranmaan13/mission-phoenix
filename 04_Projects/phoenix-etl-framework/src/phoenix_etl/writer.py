import csv
import json
from pathlib import Path

from phoenix_etl.models import RejectedRecord

REJECTED_RECORD_FIELDS = [
    "pipeline_run_id",
    "source_file",
    "rejected_at",
    "transaction_id",
    "rejection_reason",
    "original_record",
]


def write_rejected_records(
    records: list[RejectedRecord],
    output_path: Path,
) -> None:
    """Append rejected records to the audit store without duplicates."""

    if not records:
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    existing_keys: set[tuple[str, str]] = set()

    if output_path.exists():
        with output_path.open(
            newline="",
            encoding="utf-8",
        ) as file:
            reader = csv.DictReader(file)

            for row in reader:
                existing_keys.add(
                    (
                        row["pipeline_run_id"],
                        row["transaction_id"],
                    )
                )

    new_records = [
        record
        for record in records
        if (
            record.pipeline_run_id,
            record.original_record["transaction_id"],
        )
        not in existing_keys
    ]

    if not new_records:
        return

    file_exists = output_path.exists()

    with output_path.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=REJECTED_RECORD_FIELDS,
        )

        if not file_exists:
            writer.writeheader()

        for record in new_records:
            writer.writerow(
                {
                    "pipeline_run_id": record.pipeline_run_id,
                    "source_file": record.source_file,
                    "rejected_at": record.rejected_at.isoformat(),
                    "transaction_id": record.original_record["transaction_id"],
                    "rejection_reason": record.rejection_reason,
                    "original_record": json.dumps(
                        record.original_record,
                        ensure_ascii=False,
                    ),
                }
            )
