import csv
import pendulum
from typing import List
from dataclasses import dataclass
import os


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PROLOG_STORAGE_NAME = f"/{ROOT_DIR}/myprolog.csv"
QUERY_FILE_NAME = f"/{ROOT_DIR}/queries.csv"
PROLOG_FILE_NAME = f"/{ROOT_DIR}/myprolog.pl"

@dataclass
class LogicalRow:
    input_text: str
    prolog_text: str
    created: pendulum.DateTime = pendulum.now().to_iso8601_string()


@dataclass
class QueryRow:
    input_text: str
    result: str
    created: pendulum.DateTime = pendulum.now().to_iso8601_string()


@dataclass
class RDFQueryRow:
    input_text: str
    result: str
    created: pendulum.DateTime = pendulum.now().to_iso8601_string()


@dataclass
class RDFLogicalRow:
    input_text: str
    prolog_text: str
    created: pendulum.DateTime = pendulum.now().to_iso8601_string()


def write_dataclass_to_csv(row: LogicalRow, filename=PROLOG_STORAGE_NAME) -> None:
    with open(filename, mode="a", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(row.__dict__.keys()),
        )
        if csv_file.tell() == 0:
            writer.writeheader()
        writer.writerow(row.__dict__)


def write_all_prolog() -> str:
    all_prolog = "\n".join([row.prolog_text for row in load_dataclass_from_csv()])
    handle = open(PROLOG_FILE_NAME, "w")
    # seek out the line you want to overwrite
    handle.seek(0)
    handle.truncate()
    handle.write(all_prolog)
    handle.close()
    return all_prolog


def load_dataclass_from_csv(filename=PROLOG_STORAGE_NAME) -> List[LogicalRow]:
    with open(filename, mode="r") as csv_file:
        reader = csv.DictReader(csv_file)
        people = []
        for row in reader:
            people.append(LogicalRow(**row))
        return people
