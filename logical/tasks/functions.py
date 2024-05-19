import openai
import re  # Importing the re module for regular expression operations
import json  # Importing the json module for parsing JSON
from pyswip import Prolog
import pendulum
import os
import logging
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(
    filename="openai_requests.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s",
)

load_dotenv(find_dotenv())

OPEN_AI_MODEL_TYPE = os.getenv("OPEN_AI_MODEL_TYPE")

# Define the root directory of the repository
ROOT_REPO_DIR = os.path.dirname(os.path.abspath(__file__))

from .storage import (
    LogicalRow,
    QueryRow,
    write_dataclass_to_csv,
    load_dataclass_from_csv,
    PROLOG_STORAGE_NAME,
    QUERY_FILE_NAME,
    PROLOG_FILE_NAME,
    write_all_prolog,
)


def _openai_wrapper(
    system_message: str,
    user_message: str,
    example_user_message: str = None,
    example_assistant_message: str = None,
):
    """
    Interacts with the OpenAI API to convert English statements to Prolog code.

    This function sends a request to the OpenAI API with a system message and a user message,
    and optionally example messages for context. It processes the API's response, extracting
    the Prolog code and any notes, and handles various potential errors that may occur during
    the request.

    Parameters:
    - system_message (str): A message that provides context to the OpenAI model.
    - user_message (str): The user's input message to be converted into Prolog.
    - example_user_message (str, optional): An example user message for additional context.
    - example_assistant_message (str, optional): An example assistant message for additional context.

    Returns:
    - A dictionary with two keys: "prolog" containing the Prolog code, and "notes" containing any additional comments.

    The function first checks for a test environment and returns a mock response if detected.
    It then constructs the message payload and sends a request to the OpenAI API. The response
    is parsed to extract the Prolog code, handling both JSON and plain text formats. The function
    also includes error handling for common issues such as authentication errors, rate limiting,
    and other OpenAI API errors.
    """
    # Log the input messages
    logging.info(f"System message: {system_message}")
    logging.info(f"User message: {user_message}")

    # Check if the function is called in a test environment
    if os.getenv("OPENAI_API_KEY") == "fake-api-key":
        # Return a mock response
        return {
            "prolog": "Mocked response",
            "notes": "This is a mock response for testing purposes.",
        }

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    try:
        # Instantiate a new OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Use the new method for creating chat completions
        result = client.chat.completions.create(
            model=OPEN_AI_MODEL_TYPE, messages=messages
        )

        # Log the raw response content from OpenAI API
        response_content = result.choices[0].message.content
        logging.info(f"Raw OpenAI response content: {response_content}")

        # Use the response content directly as Prolog code
        prolog_code = (
            response_content if response_content else "Error: Prolog code not found."
        )
        notes = ""  # Currently, no additional notes are provided

        return {"prolog": prolog_code, "notes": notes}
    except openai.AuthenticationError:
        # Handle invalid API key error
        return {"prolog": "", "notes": "Error: Invalid OpenAI API key."}
    except openai.RateLimitError:
        # Handle API rate limit exceeded error
        return {"prolog": "", "notes": "Error: OpenAI API rate limit exceeded."}
    except openai.OpenAIError as e:
        # Handle general OpenAI API errors
        return {
            "prolog": "",
            "notes": f"Error: An unexpected OpenAI API error occurred: {str(e)}",
        }
    except Exception as e:
        # Handle non-OpenAI related exceptions
        return {"prolog": "", "notes": f"Error: An unexpected error occurred: {str(e)}"}


def parse_logic(input_text, query_only=False):
    if query_only:
        output = """a query statement noted by 'user query:' to query over our knowledge base.
        You can use the original prolog starting with 'original:' to make sure the same vocabulary is generated.
        Only output the new prolog query generated from the user query.
        """
    else:
        output = """a set of logical statements, rules, and object definitions in Prolog.
        Be sure all objects are defined before instatiating rules. And be sure there are no infinite recursions."""

    SYSTEM_PARSING_PROMPT = f"""
    Hello. You are a Prolog API which converts English statements to Prolog.
    Output correct and complete Prolog code that can be compiled in swi-prolog.
    Your Prolog output should be thorough, including necessary assumptions about the world.
    Ensure the output is in a simple conditional format for parsing by a boolean logic parser.
    Avoid common errors such as incorrect implications, conditionals without proper predicates, and ensure proper use of quantifiers.
    Thank you!
    """

    ASISSITANT_PARSING_PROMPT = f"""
    Please generate a JSON-formatted response with Prolog code from the following English statement. The response should have two fields: "prolog" for the pure Prolog code that can be run in a Prolog interpreter, and "notes" for any additional comments or context. Ensure the Prolog code is correct and complete, and can be compiled in swi-prolog. Avoid including any extra text outside of the JSON structure.

    Example 1: English: 'If it is raining, then the ground is wet.'
               JSON: '{{"prolog": "raining :- ground_wet.", "notes": ""}}'

    Example 2: English: 'All birds can fly except for penguins.'
               JSON: '{{"prolog": "can_fly(X) :- bird(X), not(penguin(X)).", "notes": ""}}'

    Example 3: English: 'Every human is mortal.'
               JSON: '{{"prolog": "mortal(X) :- human(X).", "notes": ""}}'

    Example 4: English: 'Socrates is a human.'
               JSON: '{{"prolog": "human(socrates).", "notes": ""}}'

    Example 5: English: 'Therefore, Socrates is mortal.'
               JSON: '{{"prolog": "mortal(socrates) :- human(socrates).", "notes": ""}}'

    Please convert the following English statement into Prolog: \n
    """

    # Get the response from the OpenAI API
    openai_response = _openai_wrapper(
        system_message=SYSTEM_PARSING_PROMPT,
        user_message=f"{ASISSITANT_PARSING_PROMPT}{input_text}",
    )

    # Log the full OpenAI response for debugging
    logging.info(f"Full OpenAI response: {openai_response}")

    # Extract the Prolog code from the OpenAI response
    prolog_code = openai_response.get("prolog", "")

    # Log the extracted Prolog code for debugging
    logging.info(f"Extracted Prolog code: {prolog_code}")

    # Check if the response is valid Prolog before processing
    if prolog_code.startswith("Error:"):
        # Handle error messages from the OpenAI API and return immediately
        return prolog_code
    elif not prolog_code:
        # Handle empty Prolog code response and return immediately
        return "Error: No Prolog code was returned from the OpenAI API."
    else:
        # Additional validation to ensure the response is in valid Prolog format
        if not is_valid_prolog(prolog_code):
            # Handle response that is not in valid Prolog syntax
            return f"Error: The response from OpenAI API is not valid Prolog syntax. Response: {prolog_code}"
        # Further semantic validation of the Prolog response
        elif not is_semantically_valid_prolog(prolog_code):
            # Handle response that is not semantically valid Prolog
            return f"Error: The response from OpenAI API is not semantically valid Prolog. Response: {prolog_code}"
        # Process the response through run_parser to generate Prolog
        return run_parser(input_text, prolog_code)


def is_valid_prolog(response: str) -> bool:
    # Initialize the finite state machine states
    NORMAL, IN_STRING, IN_COMMENT, ESCAPE_IN_STRING = range(4)
    state = NORMAL
    comment_depth = 0  # Track the depth of nested comments
    parentheses_stack = []  # Stack to check for balanced parentheses

    # Iterate over each character in the response
    i = 0  # Initialize the loop counter
    while i < len(response):
        char = response[i]
        if state == NORMAL:
            if char == "'":
                state = IN_STRING
            elif char == "(":
                parentheses_stack.append(char)
            elif char == ")":
                if not parentheses_stack or parentheses_stack[-1] != "(":
                    return False
                parentheses_stack.pop()
            elif char == "/" and i < len(response) - 1 and response[i + 1] == "*":
                state = IN_COMMENT
                comment_depth += 1
                i += 1  # Skip the next character as it is part of '/*'
        elif state == IN_STRING:
            if char == "\\":
                state = ESCAPE_IN_STRING
            elif char == "'":
                if i < len(response) - 1 and response[i + 1] == "'":
                    i += 1  # Skip the escaped quote
                else:
                    state = NORMAL
        elif state == ESCAPE_IN_STRING:
            state = IN_STRING  # Return to IN_STRING state after an escape sequence
        elif state == IN_COMMENT:
            if char == "*" and i < len(response) - 1 and response[i + 1] == "/":
                comment_depth -= 1
                if comment_depth == 0:
                    state = NORMAL
                i += 1  # Skip the next character as it is part of '*/'
            elif char == "\n":  # Handle end of line within a comment
                pass
                # No action needed for multi-line comments
                # Single line comments are handled by the '*' and '/' check
        i += 1  # Increment the loop counter

    # Check for unbalanced parentheses
    if parentheses_stack:
        return False

    # Check if the response ends with a period outside of string literals and comments
    return state == NORMAL and response.rstrip().endswith(".")


def is_semantically_valid_prolog(response: str) -> bool:
    # Check for correct usage of operators
    operator_pattern = r"(?<!\S)(:-|;|,|\.)"
    if re.search(operator_pattern, response) and not re.search(
        r"\b[a-z]+\([\w, ]+\)\s*(?::-\s*.+)?\.", response
    ):
        return False

    # Check for directives
    directive_pattern = r":-\s*[a-z_][a-zA-Z0-9_]*(\s*\([\w, ]+\))?\s*(?=\.)"
    if ":-" in response and not re.search(directive_pattern, response):
        return False

    # Check for facts and rules structure
    fact_rule_pattern = r"\b[a-z]+\([\w, ]+\)(\s*:-\s*.+)?\."
    if not re.search(fact_rule_pattern, response):
        return False

    return True


def parse_query(input_text):
    SYSTEM_ASKING_PROMPT = """
    You are an assistant to help understand the output of a prolog statement.
    You will be provided the original prolog as well as the output.
    There may be logical errors in the database, or the query.
    """

    ASSISTANT_ASKING_PROMPT = """
    Please explaing why the logic is correct or incorrect, or what might be missing in the following.  \n

    """

    return _openai_wrapper(
        system_message=SYSTEM_ASKING_PROMPT,
        user_message=f"{ASSISTANT_ASKING_PROMPT}{input_text}",
    )


def run_parser(input_text: str, prolog_statement: str):
    # Check if the Prolog statement is valid before returning
    if prolog_statement.startswith("Error:"):
        # Handle error in Prolog generation
        return prolog_statement

    # Write the Prolog statement to the CSV file
    row = LogicalRow(input_text=input_text, prolog_text=prolog_statement)
    write_dataclass_to_csv(row, PROLOG_STORAGE_NAME)

    return prolog_statement


def run_logic(prolog_code: str):
    if not prolog_code:
        return "Error: No Prolog code provided."

    prolog = Prolog()  # Instantiate the Prolog interpreter object

    try:
        # Assert the Prolog code to the interpreter
        prolog.assertz(prolog_code)
    except Exception as e:
        return f"Error: Invalid Prolog code. {str(e)}"

    # Check if the Prolog code is valid before proceeding
    if prolog_code.startswith("Error:") or not prolog_code:
        return prolog_code  # Return the error message or indicate an empty query

    logging.info(f"*** sending query {prolog_code} ***")
    query_error = None
    solutions = []
    try:
        # Query the Prolog interpreter with the asserted code
        solutions = [solution for solution in prolog.query(prolog_code)]
    except Exception as e:
        query_error = str(e)
        logging.error(query_error)
        return f"Error: Failed to execute Prolog query. {query_error}"

    for solution in solutions:
        logging.info(solution)
    message = f"query: {prolog_code}"
    message += f"\n prolog out: {solutions}"
    message += f"\nErrors: {query_error}"
    result = parse_query(message)

    return result
