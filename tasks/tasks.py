from invoke import task
from .utils import ROOT_REPO_DIR, printlogo
import os
from logical import run_parser, parse_logic, run_logic

@task(help={'text': "Text to parse into Prolog"})
def parse(ctx, text):
    """
    Invoke task to parse English text into Prolog.
    """
    printlogo("Parsing English to Prolog")
    result = parse_logic(text)
    print(result)

@task(help={'text': "Text to run as a Prolog query"})
def run_logic_task(ctx, text):
    """
    Invoke task to run a Prolog query and return the result.
    """
    printlogo("Running Prolog Query")
    result = run_logic(text)
    print(result)
