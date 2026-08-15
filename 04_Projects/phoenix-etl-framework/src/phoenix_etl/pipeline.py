from pathlib import Path

from pydantic import BaseModel

from phoenix_etl.models import RejectedRecord, Transaction
from phoenix_etl.reader import read_transactions
from phoenix_etl.run_tracker import (
    complete_pipeline_run,
    fail_pipeline_run,
    start_pipeline_run,
)
from phoenix_etl.validator import validate_transaction
from phoenix_etl.writer import (
    write_rejected_records,
    write_rejected_records_to_db,
    write_transactions,
)


class PipelineResult(BaseModel):
    """Result produced by a Phoenix ETL pipeline run."""

    valid_records: list[Transaction]
    rejected_records: list[RejectedRecord]

    @property
    def total_records(self) -> int:
        """Return the total number of processed records."""
        return len(self.valid_records) + len(self.rejected_records)

    @property
    def valid_count(self) -> int:
        """Return the number of valid records."""
        return len(self.valid_records)

    @property
    def rejected_count(self) -> int:
        """Return the number of rejected records."""
        return len(self.rejected_records)


def process_file(
    path: Path,
    pipeline_run_id: str,
) -> PipelineResult:
    """Read, validate, and persist all transactions from a CSV file."""

    start_pipeline_run(
        pipeline_run_id=pipeline_run_id,
        source_file=str(path),
    )

    try:
        valid_records: list[Transaction] = []
        rejected_records: list[RejectedRecord] = []

        for record in read_transactions(path):
            transaction, rejected = validate_transaction(
                record,
                source_file=str(path),
                pipeline_run_id=pipeline_run_id,
            )

            if transaction is not None:
                valid_records.append(transaction)

            if rejected is not None:
                rejected_records.append(rejected)

        write_transactions(valid_records)

        write_rejected_records_to_db(rejected_records)

        rejected_path = path.parent / "rejected_records.csv"

        write_rejected_records(
            rejected_records,
            rejected_path,
        )

        complete_pipeline_run(
            pipeline_run_id=pipeline_run_id,
            total_records=len(valid_records) + len(rejected_records),
            valid_records=len(valid_records),
            rejected_records=len(rejected_records),
        )

        return PipelineResult(
            valid_records=valid_records,
            rejected_records=rejected_records,
        )

    except Exception as exc:
        fail_pipeline_run(
            pipeline_run_id=pipeline_run_id,
            error_message=str(exc),
        )
        raise
