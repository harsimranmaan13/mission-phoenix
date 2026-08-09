from pathlib import Path

from pydantic import BaseModel

from phoenix_etl.models import RejectedRecord, Transaction
from phoenix_etl.reader import read_transactions
from phoenix_etl.validator import validate_transaction
from phoenix_etl.writer import write_rejected_records


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
    """Read, validate, and persist rejected transactions from a CSV file."""

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

    rejected_path = path.parent / "rejected_records.csv"

    write_rejected_records(
        rejected_records,
        rejected_path,
    )

    return PipelineResult(
        valid_records=valid_records,
        rejected_records=rejected_records,
    )
