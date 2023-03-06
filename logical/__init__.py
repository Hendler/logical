import openai
from pyswip import Prolog
import pendulum


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

    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    return result["choices"][0]["message"]["content"]


def parse_logic(input_text, query_only=False):
    if query_only:
        output = "a query statement only."
    else:
        output = "a set of logical statements only."

    SYSTEM_PARSING_PROMPT = f"""
    Hello. You are a logic extractor, converting english statements to prolog.
    This requires categorizing and extracting the first class objects, and then their logical relationships.
    Do not assume the logic to be correct.  No explanation is required on your part.
    You can you will output prolog only, so prolog may find the errors.

    The output will be {output}.

    Thank you!
    """
    ASISSITANT_PARSING_PROMPT = f"""
    Very important thaty you only respond with  prolog coding. I won't need an explanation, but I appreciate the thought.
    Please generate prolog, even if the parser fails, by extracting {output} from the following: \n

    """

    return _openai_wrapper(
        system_message=SYSTEM_PARSING_PROMPT,
        example_user_message=f"{ASISSITANT_PARSING_PROMPT} jane is red, jim is blue, they are the same color.",
        example_assistant_message="jane(red), jim(blue), same_color(X,Y) :- jane(X), jim(Y).",
        user_message=f"{ASISSITANT_PARSING_PROMPT}{input_text}",
    )


def parse_query(input_text):
    SYSTEM_ASKING_PROMPT = """
    You are an assistant to help us understand the output of a prolog statement. You will be provided the original prolog as well as the output.
    There may be logical errors in the database, or the query.
    """

    ASSISTANT_ASKING_PROMPT = """
    Please explaing why the logic is correct or incorrect, or what might be missing in the following.  \n

    """

    return _openai_wrapper(
        system_message=SYSTEM_ASKING_PROMPT,
        example_user_message=f"{ASSISTANT_ASKING_PROMPT} jane is red, jim is blue, they are the same color.",
        example_assistant_message="same_color(X,Y) :- jane(X), jim(Y).",
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
        f"user asks: {input_text}\nthe original prolog: \n {all_prolog}",
        query_only=True,
    )
    print(f"*** sending query {query} ***")
    parse_error = None
    query_error = None
    solutions = []
    # export prolog to file
    try:
        prolog.consult(f"/Users/jonathan.hendler/personal/logical/{PROLOG_FILE_NAME}")
    except Exception as e:
        # pyswip.prolog.PrologError: Caused by: 'consult('myprolog.pl')'. Returned: 'error(instantiation_error, context(:(system, /(atom_chars, 2)), _3208))'.
        parse_error = str(e)
        print(parse_error)

    try:
        solutions = [solution for solution in prolog.query(query)]
    except Exception as e:
        # pyswip.prolog.PrologError: Caused by: 'consult('myprolog.pl')'. Returned: 'error(instantiation_error, context(:(system, /(atom_chars, 2)), _3208))'.
        query_error = str(e)
        print(query_error)

    for solution in solutions:
        print(solution)

    message = f"Result: {solutions}"
    message += f"\nErrors: {parse_error} {query_error}"
    result = parse_query(message)

    return result
