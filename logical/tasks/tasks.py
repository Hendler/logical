from invoke import task
import os
import json
import openai
from .utils import ROOT_REPO_DIR, printlogo
from .functions import _openai_wrapper
from pyswip.prolog import Prolog, PrologError
from .logger import logger
import re
import sys
import logging

# Configure logger to output debug logs to console
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
        # Normalize the statement to ensure consistent handling
        normalized_statement = statement.strip()
        # Check if 'assertz' is present at the start of the normalized statement
        if normalized_statement.startswith('assertz(') and normalized_statement.endswith(').') and normalized_statement.count('assertz(') == 1:
            # Strip 'assertz(' from the start and the trailing '.' to prepare for syntax checking
            normalized_statement = normalized_statement[8:-2]
        # Check for balanced parentheses after potential modifications
        if not is_balanced_parentheses(normalized_statement):
            return False, f"Unbalanced parentheses in statement '{normalized_statement}'."
        # Attempt to assert the normalized Prolog statement into the knowledge base
        try:
            prolog.assertz(normalized_statement)
        except PrologError as e:
            # If a PrologError is caught, the code is invalid
            return False, f"Prolog syntax error in statement '{normalized_statement}': {e}"
    # If no error is caught for any statement, the code is valid
    return True, "Prolog code syntax is correct."

def find_matching_paren(statement, open_paren_index):
    """
    Finds the index of the matching closing parenthesis for the first opening parenthesis in the statement.

    Parameters:
    - statement (str): The Prolog statement to search.
    - open_paren_index (int): The index of the opening parenthesis.

    Returns:
    - int: The index of the matching closing parenthesis, or -1 if no match is found.
    """
    stack = []
    for i in range(open_paren_index, len(statement)):
        if statement[i] == '(':
            stack.append(i)
        elif statement[i] == ')':
            if not stack:
                return -1  # No matching opening parenthesis
            stack.pop()
            if not stack:
                return i  # Found the matching closing parenthesis
    return -1  # No matching closing parenthesis found

def is_balanced_parentheses(statement):
    """
    Checks if parentheses in a statement are balanced.

    Parameters:
    - statement (str): The statement to check.

    Returns:
    - bool: True if parentheses are balanced, False otherwise.
    """
    stack = []
    for char in statement:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if not stack or stack[-1] != '(':
                return False
            stack.pop()
    return not stack

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
        # Normalize the case of the Prolog code
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
            logger.debug(f"Line before formatting: {line}")
            # Ensure 'assertz(' is only added if it is not already present at the start of the statement
            # and the statement is not a well-formed Prolog fact or rule
            if not line.startswith('assertz(') and not is_balanced_parentheses(line):
                # Ensure the line ends with a single period, only add it if it's not already there at the end
                if not line.endswith('.'):
                    line += '.'
                line = f"assertz({line})"
            logger.debug(f"Line after formatting: {line}")
            formatted_lines.append(line)
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

    if prolog_code:
        # Strip comments and ensure no trailing whitespace
        prolog_code = re.sub(r'\s*%.*', '', prolog_code, flags=re.MULTILINE).strip()
        # Validate the Prolog code
        validation_passed, error_message = validate_prolog_code(prolog_code)
        logger.debug(f"Validation result: {validation_passed}, Error message: {error_message}")
        if validation_passed:
            # Ensure the Prolog code ends with a single period and is wrapped with 'assertz' if not already present
            if not prolog_code.endswith('.'):
                prolog_code += '.'
            if not prolog_code.startswith('assertz('):
                prolog_code = f"assertz({prolog_code})"
            # Append the validated Prolog code to world.pl
            append_to_world(prolog_code)
        else:
            logger.error(f"Failed to validate Prolog code: {error_message}")
            return None
    else:
        logger.error("No Prolog code was generated.")
        return None
    logger.debug("interactive_logic function completed")
    return prolog_code

@task
def run_logic_task(c, prolog_code_path, main_predicate=None, arity=None):
    pass
    # ... (rest of the run_logic_task function remains unchanged)
