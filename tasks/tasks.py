from invoke import task
import os
import json
import openai
from logical import _openai_wrapper
from logical import ROOT_REPO_DIR
from pyswip.prolog import Prolog, PrologError
import logging

# Configure logging to display info-level messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    print(f"Generated Prolog code: {prolog_code}")

    # Validate and format the Prolog code
    if prolog_code:
        # Ensure the code ends with a period and starts with a lowercase character
        prolog_code = prolog_code.strip().lower()
        if not prolog_code.endswith('.'):
            prolog_code += '.'
        print(f"Formatted Prolog code to append: {prolog_code}")

        # Check for balanced parentheses
        if prolog_code.count('(') != prolog_code.count(')'):
            c.run(f"echo 'Error: Unbalanced parentheses in Prolog code'")
            return

        # Handle different types of logical constructs
        if input_text.lower().startswith('all '):
            parts = input_text[4:].split(' are ', 1)
            if len(parts) == 2:
                subject = parts[0].strip().lower()
                predicate = parts[1].strip().rstrip('.').lower()
                # Ensure subject and predicate are singular for Prolog code
                subject_singular = subject[:-1] if subject.endswith('s') else subject
                predicate_singular = predicate[:-1] if predicate.endswith('s') else predicate
                # Construct the Prolog code for the implication
                prolog_code = f"{predicate_singular}(X) :- {subject_singular}(X)."
                print(f"Prolog code for 'All' statement: {prolog_code}")
        elif input_text.lower().startswith('some '):
            # Extract the subject and predicate from the statement
            parts = input_text[5:].split(' can ', 1)
            if len(parts) == 2:
                subject = parts[0].strip().capitalize()
                predicate = parts[1].strip().rstrip('.').lower()
                # Initialize the Prolog interpreter
                prolog = Prolog()
                # Query the Prolog knowledge base to retrieve all subjects
                prolog_subjects = list(prolog.query(f"{subject.lower()}(Subject)"))
                # Extract the subject names from the query results
                subject_list = [s['Subject'] for s in prolog_subjects if 'Subject' in s]
                # Construct the Prolog code using member to check for at least one instance where the predicate is true for the subject
                prolog_code = f"some_{subject.lower()}(X) :- member(X, [{', '.join(subject_list)}]), {predicate}(X)."
                print(f"Prolog code for 'Some' statement: {prolog_code}")
        elif input_text.lower().startswith('no '):
            # Extract the subject and predicate from the statement
            parts = input_text[3:].split(' ')
            subject = parts[0]
            predicate = ' '.join(parts[1:])
            prolog_code = f"\\+ forall(X, ({subject}(X) -> ({predicate})))"
        elif input_text.lower().startswith('if '):
            # Split the statement into condition and conclusion parts
            parts = input_text[3:].split(' then ')
            if len(parts) == 2:
                condition, conclusion = parts
                # Ensure both condition and conclusion are valid Prolog statements and end with a period
                condition = condition.rstrip('.').lower()
                conclusion = conclusion.rstrip('.').lower()
                if not condition.endswith('.'):
                    condition += '.'
                if not conclusion.endswith('.'):
                    conclusion += '.'
                # Construct the Prolog code for the implication
                prolog_code = f"({condition} -> {conclusion})"

    # Log the Prolog code to be appended to the world.pl file for verification
    logging.info(f"Appending to world.pl: {prolog_code}")

    # Write the validated and formatted Prolog code to a file for later use
    prolog_file_path = os.path.join(ROOT_REPO_DIR, 'world.pl')
    print(f"Attempting to append to world.pl at path: {prolog_file_path}")
    print(f"Prolog code to be appended: {prolog_code}")
    try:
        with open(prolog_file_path, 'a') as prolog_file:
            print(f"Appending the following Prolog code to world.pl:\n{prolog_code}")
            prolog_file.write(prolog_code + '\n')
        print("Prolog code appended to world.pl successfully.")
    except Exception as e:
        print(f"Failed to append Prolog code to world.pl: {e}")

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
            # Trim whitespace from the line
            line = line.strip()
            # Ensure the line is a single valid statement and does not end with a period
            if line.endswith('.'):
                line = line[:-1]
            # Check for balanced parentheses
            if line.count('(') != line.count(')'):
                c.run(f"echo 'Error: Unbalanced parentheses in Prolog code: {line}'")
                return
            try:
                # Assert the Prolog code as a fact or rule
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

@task(help={'input-text': "An English statement to convert to Prolog. If not provided, the task will prompt for input."})
def interactive_logic(c, input_text=None):
    """
    This task provides an interactive mode for the user to input English statements and receive Prolog queries or truth values in response.
    It utilizes the existing `parse` and `run_logic_task` functionalities to process user input and interact with the Prolog interpreter.

    Parameters:
    - c: The context from the invoke task.
    - input_text: Optional. An English statement to be processed.
    """
    if input_text is None:
        # Interactive mode: prompt the user for an English statement
        input_text = input("Enter an English statement (or type 'exit' to quit): ")
        if input_text.lower() == 'exit':
            return

    # Call the parse task to convert the English statement to Prolog code
    parse(c, input_text)

    # Run the resulting Prolog code to determine its truth value
    prolog_code_path = os.path.join(ROOT_REPO_DIR, 'world.pl')
    run_logic_task(c, prolog_code_path)

        # Removed the line that clears the contents of world.pl to allow accumulation of Prolog statements
