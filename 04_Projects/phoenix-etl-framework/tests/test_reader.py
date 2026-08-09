from pathlib import Path

from phoenix_etl.reader import read_transactions


def test_read_transactions_returns_all_rows(tmp_path: Path) -> None:
    csv_file = tmp_path / "transactions.csv"

    csv_file.write_text(
        "transaction_id,customer_id,amount,currency,timestamp,source_updated_at\n"
        "T001,C001,1500.00,INR,2026-08-09T10:15:00,2026-08-09T10:20:00\n"
        "T002,C002,-100.00,INR,2026-08-09T10:16:00,2026-08-09T10:21:00\n",
        encoding="utf-8",
    )

    records = list(read_transactions(csv_file))

    assert len(records) == 2
    assert records[0]["transaction_id"] == "T001"
    assert records[1]["amount"] == "-100.00"


def test_reader_preserves_raw_values(tmp_path: Path) -> None:
    csv_file = tmp_path / "transactions.csv"

    csv_file.write_text(
        "transaction_id,customer_id,amount,currency,timestamp,source_updated_at\n"
        "T001,C001,1500.00,INR,2026-08-09T10:15:00,2026-08-09T10:20:00\n",
        encoding="utf-8",
    )

    record = next(read_transactions(csv_file))

    assert record["amount"] == "1500.00"
    assert record["currency"] == "INR"
