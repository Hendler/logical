from invoke import task
import os
import json
import openai
from .utils import ROOT_REPO_DIR, printlogo
from .functions import _openai_wrapper
from pyswip.prolog import Prolog, PrologError
from .logger import logger
import re

# Load the OpenAI API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

def append_to_world(prolog_code):
    """
    Appends the given Prolog code to the world.pl file.

    Parameters:
    - prolog_code (str): The Prolog code to append.
    """
    prolog_file_path = os.path.join(ROOT_REPO_DIR, "world.pl")
    try:
        with open(prolog_file_path, "a") as prolog_file:
            prolog_file.write(f"\n{prolog_code}\n")
        logger.info(f"Appended Prolog code to world.pl: {prolog_code}")
    except Exception as e:
        logger.error(f"Failed to append Prolog code to world.pl: {e}")

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
        system_message=system_message, user_message=input_text
    )

    # Extract the Prolog code from the response
    prolog_code = openai_response.get("prolog", "")
    # Remove markdown code block syntax (triple backticks) from the Prolog code
    prolog_code = prolog_code.replace("```", "").strip()
    logger.info(f"Generated Prolog code: {prolog_code}")

    # Validate and format the Prolog code
    if prolog_code:
        prolog_code = "\n".join([line[0].lower() + line[1:] if line else "" for line in prolog_code.splitlines()])
        prolog_code = prolog_code.strip().lower()
        # Capitalize variables (Prolog variables start with an uppercase letter or underscore)
        # Use a regular expression to find all instances of variables and capitalize them
        # Variables in Prolog are capitalized and not part of a quoted string or comment
        prolog_code = re.sub(
            r"(?<=\(|,|\s)([a-z_]\w*)(?=\s|\,|\))",
            lambda match: match.group(0).capitalize(),
            prolog_code,
        )

        # Format the Prolog code to ensure proper syntax
        formatted_lines = []
        for line in prolog_code.splitlines():
            line = line.strip()
            # Check if the line is a comment, directive, or already contains 'assertz'
            if line.startswith('%') or line.startswith(':-'):
                formatted_lines.append(line)
            else:
                # Add 'assertz' only if it's not already present and the line is not empty
                if line and not line.startswith('assertz('):
                    line = 'assertz(' + line
                # Ensure the line ends with exactly one period
                if not line.endswith('.'):
                    line += '.'
                formatted_lines.append(line)
        prolog_code = '\n'.join(formatted_lines)
        logger.info(f"Formatted Prolog code to append: {prolog_code}")

        # Implement the validate_prolog_code function
        def validate_prolog_code(prolog_code):
            """
            Validates the syntax of the generated Prolog code using an actual Prolog interpreter.

            Parameters:
            - prolog_code (str): The generated Prolog code to validate.

            Returns:
            - (bool, str): A tuple containing a boolean indicating if the validation passed and an error message if it failed.
            """
            prolog = Prolog()
            try:
                # Attempt to assert the Prolog code into the knowledge base
                prolog.assertz(prolog_code)
            except PrologError as e:
                # If a PrologError is caught, the code is invalid
                return False, f"Prolog syntax error: {e}"
            else:
                # If no error is caught, the code is valid
                return True, "Prolog code syntax is correct."

        # Replace the placeholder call with the actual function definition
        validation_passed, error_message = validate_prolog_code(prolog_code)
        if not validation_passed:
            error_log_message = f"Validation failed for input: '{input_text}' with error: {error_message}"
            logger.error(error_log_message)
            return

        # Replace the redundant code blocks with calls to the new function
        append_to_world(prolog_code)

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
        with open(prolog_code_path, "r") as prolog_file:
            prolog_code = prolog_file.read()
    except FileNotFoundError:
        logger.error(f"Error: Prolog code file not found at {prolog_code_path}")
        return
    except Exception as e:
        logger.error(f"Error reading Prolog code file: {e}")
        return

    # Initialize the Prolog interpreter
    prolog = Prolog()

    printlogo()

    # Split the Prolog code into individual lines
    prolog_lines = prolog_code.strip().split("\n")
    # Iterate over each line and handle it appropriately
    for line in prolog_lines:
        if line and not line.startswith("%"):  # Skip empty lines and comments
            line = line.strip()
            if line.startswith(":-"):  # Handle Prolog directives differently
                with open(prolog_code_path, "a") as prolog_file:
                    prolog_file.write(
                        line + "\n"
                    )  # Write the directive directly to the file
            else:
                # Ensure the line is a complete statement with a single period at the end
                # Only add a period if the line does not already end with one
                if not line.endswith("."):
                    line += "."
                try:
                    # Assert the Prolog fact or rule, ensuring no duplicate periods and correct syntax
                    # Do not strip parentheses as they might be part of the Prolog syntax
                    # Check if the line is a rule or fact and handle accordingly
                    if ":-" in line or (
                        line.count("(") == line.count(")") and line.count("(") > 0
                    ):
                        # It's a rule, assert without changes
                        prolog.assertz(line)
                    else:
                        # It's a fact, ensure it ends with a single period
                        prolog.assertz(line)
                except PrologError as e:
                    logger.error(f"Error in Prolog code: {e}")
                    return

    # If main_predicate and arity are not provided, attempt to determine them
    if not main_predicate or arity is None:
        for line in prolog_lines:
            if not line.startswith("%") and ":-" in line:
                # Extract the predicate name and its arguments
                predicate_parts = line.split(":-")[0].strip().split("(")
                main_predicate = predicate_parts[0]
                if len(predicate_parts) > 1:
                    # Count the number of arguments based on commas and closing parenthesis
                    arity = predicate_parts[1].count(",") + (
                        1 if predicate_parts[1].endswith(")") else 0
                    )
                else:
                    arity = 0
                break

    if not main_predicate:
        logger.error(f"Error: No main predicate found in Prolog code")
        return

    # Construct the query using the main predicate and arity
    if arity == 0:
        query = f"{main_predicate}."
    else:
        args = ",".join(["_" for _ in range(arity)])  # Use underscores for variables
        query = f"{main_predicate}({args})."

    # Query the Prolog interpreter to determine the truth value
    try:
        query_result = list(prolog.query(query))
    except PrologError as e:
        logger.error(f"Error executing Prolog query: {e}")
        return

    # Determine the truth value based on the query result
    truth_value = bool(query_result)

    # Log the result for auditing
    logger.info(f"The truth value of the Prolog code is: {truth_value}")

    # Return the truth value
    return truth_value


@task(help={"statement": "An English statement to convert to Prolog."})
def interactive_logic(c, statement=""):
    """
    This task provides an interactive mode for the user to input English statements and receive Prolog queries or truth values in response.
    It utilizes the existing `parse` and `run_logic_task` functionalities to process user input and interact with the Prolog interpreter.

    Parameters:
    - c: The context from the invoke task.
    - statement: An English statement to be processed.
    """
    while True:
        if not statement:
            # Interactive mode: prompt the user for an English statement
            statement = input("Enter an English statement (or type 'exit' to quit): ").strip()
            if statement.lower() == "exit":
                print("Exiting interactive logic mode.")
                break

        # Call the parse task to convert the English statement to Prolog code
        parse(c, statement)

        # Run the resulting Prolog code to determine its truth value
        prolog_code_path = os.path.join(ROOT_REPO_DIR, "world.pl")
        truth_value = run_logic_task(c, prolog_code_path)
        print(f"The truth value of the statement '{statement}' is: {truth_value}")

        # Clear the statement to allow for new input in the next iteration
        statement = ""
