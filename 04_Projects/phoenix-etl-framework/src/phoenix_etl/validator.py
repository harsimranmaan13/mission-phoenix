from datetime import datetime, timezone

from pydantic import ValidationError

from phoenix_etl.models import RejectedRecord, Transaction


def validate_transaction(
    record: dict[str, str],
    source_file: str,
    pipeline_run_id: str,
) -> tuple[Transaction | None, RejectedRecord | None]:
    """Validate a raw transaction record."""

    try:
        transaction = Transaction.model_validate(record)
        return transaction, None

    except ValidationError as exc:
        rejection_reason = _get_rejection_reason(exc)

        rejected = RejectedRecord(
            original_record=record,
            rejection_reason=rejection_reason,
            source_file=source_file,
            pipeline_run_id=pipeline_run_id,
            rejected_at=datetime.now(timezone.utc),
        )

        return None, rejected


def _get_rejection_reason(exc: ValidationError) -> str:
    """Convert Pydantic validation errors into business-friendly messages."""

    errors = exc.errors()

    if not errors:
        return "transaction validation failed"

    error = errors[0]
    field = error.get("loc", ["unknown"])[0]
    error_type = error.get("type")

    if field == "amount" and error_type == "greater_than_equal":
        return "amount must be greater than or equal to 0"

    if field == "customer_id" and error_type == "string_too_short":
        return "customer_id must not be empty"

    if field == "transaction_id" and error_type == "string_too_short":
        return "transaction_id must not be empty"

    if field == "currency":
        return "currency must be a three-letter uppercase code"

    return error.get("msg", "transaction validation failed")
