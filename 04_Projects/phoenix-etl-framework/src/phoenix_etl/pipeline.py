from pathlib import Path

from pydantic import BaseModel

from phoenix_etl.logging_config import get_logger
from phoenix_etl.models import RejectedRecord, Transaction
from phoenix_etl.reader import read_transactions
from phoenix_etl.run_tracker import (
    complete_pipeline_run,
    fail_pipeline_run,
    start_pipeline_run,
)
from phoenix_etl.validator import validate_transaction
from phoenix_etl.writer import write_rejected_records, write_transactions

logger = get_logger("pipeline")


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

    @property
    def valid_rate(self) -> float:
        """Return the percentage of records that passed validation."""
        if self.total_records == 0:
            return 0.0

        return self.valid_count / self.total_records

    @property
    def rejection_rate(self) -> float:
        """Return the percentage of records rejected during validation."""
        if self.total_records == 0:
            return 0.0

        return self.rejected_count / self.total_records


def process_file(
    path: Path,
    pipeline_run_id: str,
) -> PipelineResult:
    """Read, validate, and persist all transactions from a CSV file."""

    logger.info(
        "Pipeline started: run_id=%s source_file=%s",
        pipeline_run_id,
        path,
    )

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

        total_records = len(valid_records) + len(rejected_records)

        logger.info(
            "Validation completed: run_id=%s total=%d valid=%d rejected=%d",
            pipeline_run_id,
            total_records,
            len(valid_records),
            len(rejected_records),
        )

        write_transactions(valid_records)

        rejected_path = path.parent / "rejected_records.csv"

        write_rejected_records(
            rejected_records,
            rejected_path,
        )

        complete_pipeline_run(
            pipeline_run_id=pipeline_run_id,
            total_records=total_records,
            valid_records=len(valid_records),
            rejected_records=len(rejected_records),
        )

        logger.info(
            "Pipeline completed: run_id=%s total=%d valid=%d rejected=%d",
            pipeline_run_id,
            total_records,
            len(valid_records),
            len(rejected_records),
        )

        return PipelineResult(
            valid_records=valid_records,
            rejected_records=rejected_records,
        )

    except Exception as exc:
        logger.exception(
            "Pipeline failed: run_id=%s error=%s",
            pipeline_run_id,
            str(exc),
        )

        fail_pipeline_run(
            pipeline_run_id=pipeline_run_id,
            error_message=str(exc),
        )

        raise
