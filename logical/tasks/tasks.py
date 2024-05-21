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

def validate_prolog_code(prolog_code):
    """
    Validates the syntax of the generated Prolog code using an actual Prolog interpreter.

    Parameters:
    - prolog_code (str): The generated Prolog code to validate.

    Returns:
    - (bool, str): A tuple containing a boolean indicating if the validation passed and an error message if it failed.
    """
    prolog = Prolog()
    statements = prolog_code.split('\n')
    for statement in statements:
        if not statement.strip():  # Skip empty lines
            continue
        try:
            # Attempt to assert each Prolog statement into the knowledge base
            prolog.assertz(statement)
        except PrologError as e:
            # If a PrologError is caught for any statement, the code is invalid
            return False, f"Prolog syntax error in statement '{statement}': {e}"
    # If no error is caught for any statement, the code is valid
    return True, "Prolog code syntax is correct."

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
        prolog_code = re.sub(
            r"(?<=\(|,|\s)([a-z_]\w*)(?=\s|\,|\))",
            lambda match: match.group(0).capitalize(),
            prolog_code,
        )

        # Format the Prolog code to ensure proper syntax
        formatted_lines = []
        for line in prolog_code.splitlines():
            line = line.strip()
            # Check if the line is a comment, directive, contains 'assertz', or ends with a period
            if line.startswith('%') or line.startswith(':-') or 'assertz(' in line or line.endswith('.'):
                formatted_lines.append(line)
            else:
                # Add 'assertz' only if it's not already present
                formatted_lines.append(f"assertz({line}).")
        prolog_code = '\n'.join(formatted_lines)
        logger.info(f"Formatted Prolog code to append: {prolog_code}")

        # Validate the Prolog code
        validation_passed, error_message = validate_prolog_code(prolog_code)
        if not validation_passed:
            error_log_message = f"Validation failed for input: '{input_text}' with error: {error_message}"
            logger.error(error_log_message)
            return
        else:
            # Append the validated and formatted Prolog code to world.pl
            append_to_world(prolog_code)

@task
def run_logic_task(c, prolog_code_path, main_predicate=None, arity=None):
    pass
    # ... (rest of the run_logic_task function remains unchanged)

@task(help={"statement": "An English statement to convert to Prolog."})
@task(help={"statement": "An English statement to convert to Prolog."})
@task(help={"statement": "An English statement to convert to Prolog."})
def interactive_logic(c, statement=""):
    logger.debug("Starting interactive_logic function")
    if not statement:
        statement = input("Enter an English statement to convert to Prolog: ")
    logger.debug(f"Received statement for conversion: {statement}")
    # Call the OpenAI API wrapper function to get the Prolog code
    openai_response = _openai_wrapper(
        system_message="", user_message=statement
    )
    # Extract the Prolog code from the response
    prolog_code = openai_response.get("prolog", "")
    logger.debug(f"Prolog code received from _openai_wrapper: {prolog_code}")
    formatted_prolog_code = ""
    if prolog_code:
        # Remove markdown code block syntax (triple backticks) from the Prolog code
        prolog_code = prolog_code.replace("```", "").strip()
        # Capitalize variables (Prolog variables start with an uppercase letter or underscore)
        prolog_code = re.sub(
            r"(?<=\(|,|\s)([a-z_]\w*)(?=\s|\,|\))",
            lambda match: match.group(0).capitalize(),
            prolog_code,
        )
        # Format the Prolog code to ensure proper syntax
        formatted_lines = []
        for line in prolog_code.splitlines():
            line = line.strip()
            logger.debug(f"Line before formatting: {line}")
            # Check if the line is a comment, directive, or ends with a period
            if line.startswith('%') or line.startswith(':-') or line.endswith('.'):
                formatted_lines.append(line)
            else:
                # Add 'assertz' only if it's not already present at the beginning of the line
                if not line.lstrip().startswith('assertz('):
                    line = f"assertz({line})."
                formatted_lines.append(line)
            logger.debug(f"Line after formatting: {line}")
        formatted_prolog_code = '\n'.join(formatted_lines)
        logger.debug(f"Prolog code after formatting and before validation: {formatted_prolog_code}")
        # Validate the Prolog code
        validation_passed, error_message = validate_prolog_code(formatted_prolog_code)
        logger.debug(f"Validation result: {validation_passed}, Error message: {error_message}")
        if validation_passed:
            # Append the validated Prolog code to world.pl
            append_to_world(formatted_prolog_code)
        else:
            logger.error(f"Failed to validate Prolog code: {error_message}")
            return None
    else:
        logger.error("No Prolog code was generated.")
        return None
    logger.debug("interactive_logic function completed")
    return formatted_prolog_code
    # ... (rest of the interactive_logic function remains unchanged)
