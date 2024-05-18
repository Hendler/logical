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
    prolog_file_path = os.path.join(ROOT_REPO_DIR, 'world.pl')
    with open(prolog_file_path, 'a') as prolog_file:
        prolog_file.write(prolog_code)

@task
def run_logic_task(c, prolog_code_path, main_predicate=None, arity=None):
    """
    This task takes a file path to Prolog code as input and runs it to determine its truth value.
    It logs the input and output for auditing purposes.

    The main predicate can be optionally provided. If not, the task will attempt to determine it
    by parsing the Prolog code and identifying the first predicate definition with a body.

    Parameters:
    - c: The context from the invoke task.
    - prolog_code_path (str): The file path to the Prolog code to be executed.
    - main_predicate (str): Optional. The main predicate to query.
    - arity (int): Optional. The arity of the main predicate.

    Usage:
    To execute this task, provide the file path to the Prolog code as an argument:
    `invoke run-logic-task --prolog-code-path='./path/to/prolog_code.pl'`
    Optionally, specify the main predicate and its arity:
    `invoke run-logic-task --prolog-code-path='./path/to/prolog_code.pl' --main-predicate='mortal' --arity=1`
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
            # Remove any surrounding parentheses from the line
            line = line.strip().rstrip('.').strip()
            try:
                prolog.assertz(line)
            except PrologError as e:
                c.run(f"echo 'Error in Prolog code: {e}'")
                return

    # If main_predicate and arity are not provided, attempt to determine them
    if not main_predicate or arity is None:
        for line in prolog_lines:
            if not line.startswith('%') and ':-' in line:
                # Extract the predicate name and its arguments
                predicate_parts = line.split(':-')[0].strip().split('(')
                main_predicate = predicate_parts[0]
                if len(predicate_parts) > 1:
                    # Count the number of arguments based on commas and closing parenthesis
                    arity = predicate_parts[1].count(',') + (1 if predicate_parts[1].endswith(')') else 0)
                else:
                    arity = 0
                break

    if not main_predicate:
        c.run(f"echo 'Error: No main predicate found in Prolog code'")
        return

    # Construct the query using the main predicate and arity
    if arity == 0:
        query = f"{main_predicate}."
    else:
        args = ','.join(['_' for _ in range(arity)])  # Use underscores for variables
        query = f"{main_predicate}({args})."

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
