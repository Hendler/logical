import csv
import pendulum
from typing import List
from dataclasses import dataclass


PROLOG_FILE_NAME = "myprolog.csv"


@dataclass
class LogicalRow:
    input_text: str
    prolog_text: str
    prolog_result: str  # runs on all previous text?
    created: pendulum.DateTime = pendulum.now().to_iso8601_string()


def write_dataclass_to_csv(person: LogicalRow) -> None:
    with open(PROLOG_FILE_NAME, mode="a", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["input_text", "prolog_text", "prolog_result", "created"],
        )
        if csv_file.tell() == 0:
            writer.writeheader()
        writer.writerow(person.__dict__)


def load_dataclass_from_csv() -> List[LogicalRow]:
    with open(PROLOG_FILE_NAME, mode="r") as csv_file:
        reader = csv.DictReader(csv_file)
        people = []
        for row in reader:
            people.append(LogicalRow(**row))
        return people
