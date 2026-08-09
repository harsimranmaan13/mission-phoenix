import csv
from collections.abc import Iterator
from pathlib import Path


def read_transactions(path: Path) -> Iterator[dict[str, str]]:
    """Read transaction records from a CSV file."""
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            yield dict(row)
