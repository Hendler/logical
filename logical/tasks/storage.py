import csv
import pendulum
from typing import List
from dataclasses import dataclass
import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
PROLOG_STORAGE_NAME = ROOT_DIR / "myprolog.csv"
QUERY_FILE_NAME = ROOT_DIR / "queries.csv"
PROLOG_FILE_NAME = ROOT_DIR / "world.pl"


def get_current_timestamp():
    """Return the current timestamp as an ISO 8601 formatted string."""
    return pendulum.now().to_iso8601_string()


@dataclass
class LogicalRow:
    input_text: str
    prolog_text: str
    created: pendulum.DateTime = get_current_timestamp()


@dataclass
class QueryRow:
    input_text: str
    result: str
    created: pendulum.DateTime = get_current_timestamp()


@dataclass
class RDFQueryRow:
    input_text: str
    result: str
    created: pendulum.DateTime = get_current_timestamp()


@dataclass
class RDFLogicalRow:
    input_text: str
    prolog_text: str
    created: pendulum.DateTime = get_current_timestamp()


def write_dataclass_to_csv(row: LogicalRow, filename=PROLOG_STORAGE_NAME) -> None:
    with open(filename, mode="a", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(row.__dict__.keys()),
        )
        # Write header only if the file is empty (at the beginning)
        if csv_file.tell() == 0:
            writer.writeheader()
        writer.writerow(row.__dict__)


def write_all_prolog() -> str:
    all_prolog = "\n".join([row.prolog_text for row in load_dataclass_from_csv()])
    with open(PROLOG_FILE_NAME, "w") as handle:
        # Overwrite the file with the new Prolog code
        handle.write(all_prolog)
    return all_prolog


def load_dataclass_from_csv(filename=PROLOG_STORAGE_NAME) -> List[LogicalRow]:
    with open(filename, mode="r") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = []
        for row in reader:
            rows.append(LogicalRow(**row))
        return rows
