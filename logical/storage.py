import csv
import pendulum
from typing import List
from dataclasses import dataclass


PROLOG_FILE_NAME = "myprolog.csv"
QUERY_FILE_NAME = "queries.csv"


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


def write_dataclass_to_csv(row: LogicalRow, filename=PROLOG_FILE_NAME) -> None:
    with open(filename, mode="a", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(row.__dict__.keys()),
        )
        if csv_file.tell() == 0:
            writer.writeheader()
        writer.writerow(row.__dict__)


def load_dataclass_from_csv(filename=PROLOG_FILE_NAME) -> List[LogicalRow]:
    with open(filename, mode="r") as csv_file:
        reader = csv.DictReader(csv_file)
        people = []
        for row in reader:
            people.append(LogicalRow(**row))
        return people
