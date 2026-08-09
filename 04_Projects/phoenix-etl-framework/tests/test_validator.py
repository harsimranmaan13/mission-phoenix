from phoenix_etl.validator import validate_transaction


def valid_record() -> dict[str, str]:
    return {
        "transaction_id": "T001",
        "customer_id": "C001",
        "amount": "1500.00",
        "currency": "INR",
        "timestamp": "2026-08-09T10:15:00",
        "source_updated_at": "2026-08-09T10:20:00",
    }


def test_valid_transaction_returns_transaction() -> None:
    transaction, rejected = validate_transaction(
        valid_record(),
        "transactions.csv",
        "run-001",
    )

    assert transaction is not None
    assert transaction.transaction_id == "T001"
    assert rejected is None


def test_negative_amount_is_rejected() -> None:
    record = valid_record()
    record["amount"] = "-100.00"

    transaction, rejected = validate_transaction(
        record,
        "transactions.csv",
        "run-001",
    )

    assert transaction is None
    assert rejected is not None
    assert rejected.original_record["amount"] == "-100.00"
    assert rejected.source_file == "transactions.csv"
    assert rejected.pipeline_run_id == "run-001"


def test_missing_customer_id_is_rejected() -> None:
    record = valid_record()
    record["customer_id"] = ""

    transaction, rejected = validate_transaction(
        record,
        "transactions.csv",
        "run-001",
    )

    assert transaction is None
    assert rejected is not None
    assert rejected.original_record["customer_id"] == ""
