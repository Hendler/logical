import openai
from pyswip import Prolog
import pendulum
import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

load_dotenv(find_dotenv())

OPEN_AI_MODEL_TYPE = os.getenv("OPEN_AI_MODEL_TYPE")


from logical.storage import (
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
    messages = []
    messages.append({"role": "system", "content": system_message})
    if example_user_message is not None and example_assistant_message is not None:
        messages.append({"role": "user", "content": example_user_message})
        messages.append({"role": "assistant", "content": example_assistant_message})
    messages.append(
        {"role": "user", "content": user_message},
    )

    # Instantiate a new OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Use the new method for creating chat completions
    result = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
    )

    # Update response handling to use the new Pydantic model accessors
    return result.choices[0].message.content


def parse_logic(input_text, query_only=False):
    if query_only:
        output = """a query statement noted by 'user query:' to query over our knowledge base.
        You can use the original prolog starting with 'original:' to make sure the same vocabulary is generated.
        Only ouput the new prolog query generated from the user query.
        """
    else:
        output = """a set of logical statements, rules, and object definitions in Prolog.
        Be sure all objects are defined before instatiating rules. And be sure there are no infinite recursions."""

    SYSTEM_PARSING_PROMPT = f"""
    Hello. You are a Prolog API which converts English statements to a set of logical statements, rules, and object definitions in Prolog.
    This requires categorizing and extracting the first class objects, and their logical relationships.
    Do not assume the logic to be correct. No explanation is required on your part.
    You will output correct and complete Prolog only, so running the output in a prolog compiler (We are using swi-prolog.) may find the errors.
    Your Prolog is thorough so that other needed assumptions about the world are included.
    Additionally, ensure the output is in a simple conditional format that can be parsed by a boolean logic parser, such as 'x > 1 and y < 2'.
    Thank you !
    """

    ASISSITANT_PARSING_PROMPT = f"""
    Please generate Prolog, even if the parser fails, by extracting a set of logical statements, rules, and object definitions from the following:
    Ensure the output is in a simple conditional format that can be parsed by a boolean logic parser, such as 'x > 1 and y < 2'. \n
    """

    return _openai_wrapper(
        system_message=SYSTEM_PARSING_PROMPT,
        user_message=f"{ASISSITANT_PARSING_PROMPT}{input_text}",
    )


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
    result = parse_logic(input_text)
    row = LogicalRow(input_text=input_text, prolog_text=result)
    write_dataclass_to_csv(row, PROLOG_STORAGE_NAME)
    return result


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
