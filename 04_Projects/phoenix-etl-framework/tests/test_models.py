from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from phoenix_etl.models import Transaction


def test_valid_transaction_is_accepted() -> None:
    transaction = Transaction(
        transaction_id="T001",
        customer_id="C001",
        amount=Decimal("1500.00"),
        currency="INR",
        timestamp=datetime(2026, 8, 9, 10, 15),
        source_updated_at=datetime(2026, 8, 9, 10, 15),
    )

    assert transaction.transaction_id == "T001"
    assert transaction.customer_id == "C001"
    assert transaction.amount == Decimal("1500.00")
    assert transaction.currency == "INR"


def test_negative_amount_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="T002",
            customer_id="C002",
            amount=Decimal("-100"),
            currency="INR",
            timestamp=datetime(2026, 8, 9, 10, 15),
            source_updated_at=datetime(2026, 8, 9, 10, 15),
        )


def test_empty_transaction_id_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="",
            customer_id="C003",
            amount=Decimal("100"),
            currency="INR",
            timestamp=datetime(2026, 8, 9, 10, 15),
            source_updated_at=datetime(2026, 8, 9, 10, 15),
        )


def test_empty_customer_id_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="T004",
            customer_id="",
            amount=Decimal("100"),
            currency="INR",
            timestamp=datetime(2026, 8, 9, 10, 15),
            source_updated_at=datetime(2026, 8, 9, 10, 15),
        )


@pytest.mark.parametrize("currency", ["inr", "Inr", "IN", "INRU", "12R"])
def test_invalid_currency_is_rejected(currency: str) -> None:
    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="T005",
            customer_id="C005",
            amount=Decimal("100"),
            currency=currency,
            timestamp=datetime(2026, 8, 9, 10, 15),
            source_updated_at=datetime(2026, 8, 9, 10, 15),
        )


def test_currency_must_be_uppercase() -> None:
    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="T006",
            customer_id="C006",
            amount=Decimal("100"),
            currency="usd",
            timestamp=datetime(2026, 8, 9, 10, 15),
            source_updated_at=datetime(2026, 8, 9, 10, 15),
        )
