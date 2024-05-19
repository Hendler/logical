from invoke import task
from .utils import ROOT_REPO_DIR, printlogo
import os
from logical import run_parser, parse_logic, run_logic

# Path to the temporary file that stores the generated Prolog code
PROLOG_CODE_FILE = os.path.join(ROOT_REPO_DIR, 'temp_prolog_code.pl')

@task(help={'text': "Text to parse into Prolog"})
def parse(ctx, text):
    """
    Invoke task to parse English text into Prolog.
    """
    printlogo("Parsing English to Prolog")
    result = parse_logic(text)
    if not result.startswith("Error:"):
        # Write the generated Prolog code to a temporary file
        with open(PROLOG_CODE_FILE, 'w') as file:
            file.write(result)
    print(result)

@task
def run_logic_task(ctx):
    """
    Invoke task to run a Prolog query and return the result.
    """
    printlogo("Running Prolog Query")
    # Read the Prolog code from the temporary file
    if os.path.exists(PROLOG_CODE_FILE):
        with open(PROLOG_CODE_FILE, 'r') as file:
            prolog_code = file.read()
        result = run_logic(prolog_code)
        if "Error:" in result:
            print(f"Error encountered: {result}")
        else:
            print(result)
    else:
        print("Error: No Prolog code was generated. Please run the parse task first.")
