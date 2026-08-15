from datetime import datetime, timezone

from phoenix_etl.db import get_connection


def start_pipeline_run(
    pipeline_run_id: str,
    source_file: str,
    started_at: datetime | None = None,
) -> None:
    """Create a pipeline run in STARTED state."""

    if started_at is None:
        started_at = datetime.now(timezone.utc)

    query = """
        INSERT INTO phoenix.pipeline_runs (
            pipeline_run_id,
            source_file,
            started_at,
            status
        )
        VALUES (
            %(pipeline_run_id)s,
            %(source_file)s,
            %(started_at)s,
            'STARTED'
        )
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                {
                    "pipeline_run_id": pipeline_run_id,
                    "source_file": source_file,
                    "started_at": started_at,
                },
            )


def complete_pipeline_run(
    pipeline_run_id: str,
    total_records: int,
    valid_records: int,
    rejected_records: int,
    completed_at: datetime | None = None,
) -> None:
    """Mark a pipeline run as COMPLETED with processing counts."""

    if completed_at is None:
        completed_at = datetime.now(timezone.utc)

    query = """
        UPDATE phoenix.pipeline_runs
        SET
            completed_at = %(completed_at)s,
            total_records = %(total_records)s,
            valid_records = %(valid_records)s,
            rejected_records = %(rejected_records)s,
            status = 'COMPLETED'
        WHERE pipeline_run_id = %(pipeline_run_id)s
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                {
                    "pipeline_run_id": pipeline_run_id,
                    "completed_at": completed_at,
                    "total_records": total_records,
                    "valid_records": valid_records,
                    "rejected_records": rejected_records,
                },
            )


def fail_pipeline_run(
    pipeline_run_id: str,
    error_message: str,
    failed_at: datetime | None = None,
) -> None:
    """Mark a pipeline run as FAILED."""

    if failed_at is None:
        failed_at = datetime.now(timezone.utc)

    query = """
        UPDATE phoenix.pipeline_runs
        SET
            completed_at = %(failed_at)s,
            status = 'FAILED',
            error_message = %(error_message)s
        WHERE pipeline_run_id = %(pipeline_run_id)s
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                {
                    "pipeline_run_id": pipeline_run_id,
                    "failed_at": failed_at,
                    "error_message": error_message,
                },
            )
