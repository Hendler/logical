from invoke import task
import os
import json
import openai
from logical import _openai_wrapper
from logical import ROOT_REPO_DIR
from pyswip.prolog import Prolog, PrologError

# Load the OpenAI API key from the environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

@task
def parse(c, input_text):
    """
    This task takes an English statement as input and uses OpenAI to generate the corresponding Prolog code.
    It logs the input and output for auditing purposes.

    Parameters:
    - c: The context from the invoke task.
    - input_text (str): The English statement to be converted into Prolog.
    """
    # Define the system message for context to the OpenAI model
    system_message = """
    Hello. You are a Prolog API which converts English statements to Prolog.
    Output correct and complete Prolog code that can be compiled in swi-prolog.
    Your Prolog output should be thorough, including necessary assumptions about the world.
    Ensure the output is in a simple conditional format for parsing by a boolean logic parser.
    Avoid common errors such as incorrect implications, conditionals without proper predicates, and ensure proper use of quantifiers.
    Thank you!
    """

    # Call the OpenAI API wrapper function to get the Prolog code
    openai_response = _openai_wrapper(
        system_message=system_message,
        user_message=input_text
    )

    # Extract the Prolog code from the response
    prolog_code = openai_response.get("prolog", "")

    # Check for errors in the response
    if prolog_code.startswith("Error:"):
        # Log and return the error message
        c.run(f"echo '{prolog_code}'")
        return

    # Log the Prolog code for auditing
    c.run(f"echo 'Prolog code: {prolog_code}'")

    # Write the Prolog code to a file for later use
    prolog_file_path = os.path.join(ROOT_REPO_DIR, 'prolog_output.pl')
    with open(prolog_file_path, 'w') as prolog_file:
        prolog_file.write(prolog_code)

@task
def run_logic_task(c, prolog_code_path):
    """
    This task takes a file path to Prolog code as input and runs it to determine its truth value.
    It logs the input and output for auditing purposes.

    The main predicate is dynamically determined by parsing the Prolog code and identifying the first
    non-comment line that contains a predicate definition. This heuristic assumes that the first predicate
    defined in the code is the main one to be queried.

    Parameters:
    - c: The context from the invoke task.
    - prolog_code_path (str): The file path to the Prolog code to be executed.

    Usage:
    To execute this task, provide the file path to the Prolog code as an argument:
    `invoke run-logic-task --prolog-code-path='./path/to/prolog_code.pl'`
    The task will read the Prolog code, determine the main predicate, and execute the query to find its truth value.
    """
    # Read the Prolog code from the file
    try:
        with open(prolog_code_path, 'r') as prolog_file:
            prolog_code = prolog_file.read()
    except FileNotFoundError:
        c.run(f"echo 'Error: Prolog code file not found at {prolog_code_path}'")
        return
    except Exception as e:
        c.run(f"echo 'Error reading Prolog code file: {e}'")
        return

    # Initialize the Prolog interpreter
    prolog = Prolog()

    # Split the Prolog code into individual lines
    prolog_lines = prolog_code.strip().split('\n')
    # Iterate over each line and assert it into the interpreter
    for line in prolog_lines:
        if line and not line.startswith('%'):  # Skip empty lines and comments
            try:
                prolog.assertz(line)
            except PrologError as e:
                c.run(f"echo 'Error in Prolog code: {e}'")
                return

    # Dynamically determine the main predicate from the Prolog code
    # This is a simple heuristic that assumes the first predicate defined is the main one
    lines = prolog_code.strip().split('\n')
    main_predicate = None
    for line in lines:
        if not line.startswith('%') and not line.startswith(':-') and ':-' in line:
            main_predicate = line.split(':-')[0].strip().split('(')[0]
            break

    if not main_predicate:
        c.run(f"echo 'Error: No main predicate found in Prolog code'")
        return

    query = f"{main_predicate}."

    # Query the Prolog interpreter to determine the truth value
    try:
        query_result = list(prolog.query(query))
    except PrologError as e:
        c.run(f"echo 'Error executing Prolog query: {e}'")
        return

    # Determine the truth value based on the query result
    truth_value = bool(query_result)

    # Log the result for auditing
    c.run(f"echo 'The truth value of the Prolog code is: {truth_value}'")

    # Return the truth value
    return truth_value
