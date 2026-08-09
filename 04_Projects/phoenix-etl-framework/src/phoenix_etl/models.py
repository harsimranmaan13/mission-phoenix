from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class Transaction(BaseModel):
    """Validated transaction record for the Phoenix ETL pipeline."""

    transaction_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    amount: Decimal = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    timestamp: datetime
    source_updated_at: datetime

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        """Require a three-letter uppercase currency code."""
        if not value.isalpha() or not value.isupper():
            raise ValueError("currency must be a three-letter uppercase code")
        return value


class RejectedRecord(BaseModel):
    """Record rejected during Phoenix ETL validation."""

    original_record: dict[str, str]
    rejection_reason: str = Field(min_length=1)
    source_file: str = Field(min_length=1)
    pipeline_run_id: str = Field(min_length=1)
    rejected_at: datetime
