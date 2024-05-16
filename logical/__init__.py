import openai
from pyswip import Prolog
import pendulum
import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

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
    # Check if the function is called in a test environment
    if os.getenv("OPENAI_API_KEY") == "fake-api-key":
        # Return a mock response
        return "Mocked response"

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
            messages=messages,
        )

        # Update response handling to use the new Pydantic model accessors
        return result.choices[0].message.content
    except openai.AuthenticationError:
        # Handle invalid API key error
        return "Error: Invalid OpenAI API key."
    except openai.RateLimitError:
        # Handle API rate limit exceeded error
        return "Error: OpenAI API rate limit exceeded."
    except openai.OpenAIError as e:
        # Handle general OpenAI API errors
        return f"Error: An unexpected OpenAI API error occurred: {str(e)}"
    except Exception as e:
        # Handle non-OpenAI related exceptions
        return f"Error: An unexpected error occurred: {str(e)}"


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
    Please generate Prolog, even if the parser fails, by extracting a set of logical statements, rules, and object definitions from the following:
    Ensure the output is in a simple conditional format that can be parsed by a boolean logic parser, such as 'x > 1 and y < 2'.
    Pay special attention to implication structures, conditional predicates, and the correct use of quantifiers to avoid common errors.

    Example 1: English: 'If it is raining, then the ground is wet.'
               Prolog: 'raining :- ground_wet.'

    Example 2: English: 'All birds can fly except for penguins.'
               Prolog: 'can_fly(X) :- bird(X), not(penguin(X)).'

    Example 3: English: 'Every human is mortal.'
               Prolog: 'mortal(X) :- human(X).'

    Example 4: English: 'Socrates is a human.'
               Prolog: 'human(socrates).'

    Example 5: English: 'Therefore, Socrates is mortal.'
               Prolog: 'mortal(socrates) :- human(socrates).'

    Please convert the following English statement into Prolog: \n
    """

    # Get the response from the OpenAI API
    openai_response = _openai_wrapper(
        system_message=SYSTEM_PARSING_PROMPT,
        user_message=f"{ASISSITANT_PARSING_PROMPT}{input_text}",
    )

    # Check if the response is valid Prolog before processing
    if not openai_response or "Mocked response" in openai_response:
        # Handle invalid or mocked response from OpenAI API
        return "Error: Invalid response from OpenAI API."
    # Additional validation to ensure the response is in valid Prolog format
    elif not is_valid_prolog(openai_response):
        # Handle response that is not in valid Prolog syntax
        return "Error: The response from OpenAI API is not valid Prolog."
    # Further semantic validation of the Prolog response
    elif not is_semantically_valid_prolog(openai_response):
        # Handle response that is not semantically valid Prolog
        return "Error: The response from OpenAI API is not semantically valid Prolog."

    # Process the response through run_parser to generate Prolog
    return run_parser(openai_response)


def is_valid_prolog(response: str) -> bool:
    """
    Validates if the given response string is in valid Prolog format.
    This is a basic check and may need to be expanded for more complex validations.
    """
    # Basic checks for Prolog syntax validity
    if not response.endswith('.'):
        return False
    if ':-' in response and not response.strip().endswith('.'):
        return False
    # Add more complex syntax checks as needed
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


def run_parser(input_text: str):
    # Call parse_logic to use OpenAI for generating Prolog from English
    prolog_statement = parse_logic(input_text)

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
