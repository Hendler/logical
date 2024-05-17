import openai
import re  # Importing the re module for regular expression operations
from pyswip import Prolog
import pendulum
import os
import logging
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(filename='openai_requests.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

load_dotenv(find_dotenv())

OPEN_AI_MODEL_TYPE = os.getenv("OPEN_AI_MODEL_TYPE")


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
    # Log the input messages
    logging.info(f"System message: {system_message}")
    logging.info(f"User message: {user_message}")

    # Check if the function is called in a test environment
    if os.getenv("OPENAI_API_KEY") == "fake-api-key":
        # Return a mock response
        return {"prolog": "Mocked response", "notes": "This is a mock response for testing purposes."}

    messages = []
    messages.append({"role": "system", "content": system_message})
    if example_user_message is not None and example_assistant_message is not None:
        messages.append({"role": "user", "content": example_user_message})
        messages.append({"role": "assistant", "content": example_assistant_message})
    messages.append(
        {"role": "user", "content": user_message},
    )

    try:
        # Instantiate a new OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Use the new method for creating chat completions
        result = client.chat.completions.create(
            model=OPEN_AI_MODEL_TYPE,
            messages=messages
        )

        # Update response handling to use the new Pydantic model accessors
        response_content = result.choices[0].message.content
        # Log the response from OpenAI API
        logging.info(f"OpenAI response: {response_content}")

        # Check if the response is wrapped in triple backticks indicating a code block
        if "```prolog" in response_content:
            # Extract the Prolog code from within the triple backticks
            prolog_code_match = re.search(r"```prolog\r?\n?([\s\S]*?)\r?\n?```", response_content)
            if prolog_code_match:
                prolog_code = prolog_code_match.group(1)
                notes = ""
            else:
                # If the regex search fails, log the error and return an appropriate message
                logging.error(f"Failed to extract Prolog code from response: {response_content}")
                return {"prolog": "", "notes": "Error: Failed to extract Prolog code from response."}
        elif response_content.startswith('{') and response_content.endswith('}'):
            try:
                # Attempt to parse the response content as JSON
                response_json = json.loads(response_content)
                prolog_code = response_json.get("prolog", "Error: Prolog code not found.")
                notes = response_json.get("notes", "")
            except json.JSONDecodeError:
                # Log the error and return an appropriate message if JSON parsing fails
                logging.error(f"Failed to parse OpenAI response as JSON: {response_content}")
                return {"prolog": "", "notes": "Error: Failed to parse OpenAI response as JSON."}
        else:
            # Handle plain Prolog code response
            prolog_code = response_content.strip()
            notes = ""
            if not prolog_code.endswith('.'):
                logging.error(f"Invalid Prolog code format: {response_content}")
                return {"prolog": "", "notes": "Error: Invalid Prolog code format."}

        return {"prolog": prolog_code, "notes": notes}
    except openai.AuthenticationError:
        # Handle invalid API key error
        return {"prolog": "", "notes": "Error: Invalid OpenAI API key."}
    except openai.RateLimitError:
        # Handle API rate limit exceeded error
        return {"prolog": "", "notes": "Error: OpenAI API rate limit exceeded."}
    except openai.OpenAIError as e:
        # Handle general OpenAI API errors
        return {"prolog": "", "notes": f"Error: An unexpected OpenAI API error occurred: {str(e)}"}
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

    # Extract the Prolog code from the OpenAI response
    prolog_code = openai_response.get("prolog", "")

    # Check if the response is valid Prolog before processing
    if not prolog_code:
        # Handle invalid or mocked response from OpenAI API
        return "Error: Invalid response from OpenAI API."
    # Additional validation to ensure the response is in valid Prolog format
    elif not is_valid_prolog(prolog_code):
        # Handle response that is not in valid Prolog syntax
        return f"Error: The response from OpenAI API is not valid Prolog. Response: {prolog_code}"
    # Further semantic validation of the Prolog response
    elif not is_semantically_valid_prolog(prolog_code):
        # Handle response that is not semantically valid Prolog
        return f"Error: The response from OpenAI API is not semantically valid Prolog. Response: {prolog_code}"

    # Process the response through run_parser to generate Prolog
    return run_parser(input_text, prolog_code)


def is_valid_prolog(response: str) -> bool:
    """
    Validates if the given response string is in valid Prolog format.
    This is a basic check and may need to be expanded for more complex validations.
    """
    # Basic checks for Prolog syntax validity
    if not response.endswith('.'):
        return False
    # Removed the incorrect check for ':-' followed by a period
    return True

def is_semantically_valid_prolog(response: str) -> bool:
    """
    Validates if the given response string is semantically valid Prolog.
    This is a simplified check that looks for common patterns and structures in Prolog statements.
    """
    # Simplified semantic validation checks
    # Check for valid implication structure
    if ':-' in response:
        parts = response.split(':-')
        if len(parts) != 2:
            return False
        # Check for valid predicate structure with a more permissive regex pattern
        if not all(re.match(r'^[a-z][a-zA-Z0-9_]*(\(.*\))?$', part.strip()) for part in parts):
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


def run_logic(input_text: str):
    # export all prolog to new file
    all_prolog = write_all_prolog()
    prolog = Prolog()

    # get query
    query = parse_logic(
        f"user query: {input_text}, \noriginal: {all_prolog}",
        query_only=True,
    )
    print(f"*** sending query {query} \n***")
    parse_error = None
    query_error = None
    solutions = []
    # export prolog to file
    try:
        prolog.consult(PROLOG_FILE_NAME)
    except Exception as e:
        parse_error = str(e)
        print(parse_error)

    try:
        solutions = [solution for solution in prolog.query(query)]
    except Exception as e:
        query_error = str(e)
        print(query_error)

    for solution in solutions:
        print(solution)
    message = f"original: {all_prolog}"
    message += f"query: {query}"
    message += f"\n prolog out: {solutions}"
    message += f"\nErrors: {parse_error} {query_error}"
    result = parse_query(message)

    return result
