import openai
from pyswip import Prolog

import pendulum

prolog = Prolog()


def _openai_wrapper(
    system_message: str,
    example_user_message: str,
    example_assistant_message: str,
    user_message: str,
):
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": example_user_message},
            {"role": "assistant", "content": example_assistant_message},
            {"role": "user", "content": user_message},
        ],
    )


def parse_logic(input_text):
    SYSTEM_PARSING_PROMPT = """
    You are a logic extractor, converting english statements to prolog, checking for the logical consistency of statements.
    This requires categorizing and extracting the first class objects, and then their logical relationships.
    No explanation is required, and you will output prolog only.

    """
    ASISSITANT_PARSING_PROMPT = """
    Please generate pure, runnable prolog extracting factual statements from the following. \n

    """

    return _openai_wrapper(
        system_message=SYSTEM_PARSING_PROMPT,
        example_user_message=f"{ASISSITANT_PARSING_PROMPT} jane is red, jim is blue, they are the same color.",
        example_assistant_message="same_color(X,Y) :- jane(X), jim(Y).",
        user_message=f"{ASISSITANT_PARSING_PROMPT}{input_text}",
    )


def parse_query(input_text):
    SYSTEM_ASKING_PROMPT = """
    You are an assistant who is both reading prolog, and the output of running of the prolog.
    It is your job to explain why the the prolog completed or failed. The explanation
    should not be about the code itself, but where there might be errors in the original languages logic.
    Information could be missing to say conclusively.
    """

    ASSISTANT_ASKING_PROMPT = """
    Please explaing why the logic is correct or incorrect, or what might be missing.  \n

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
    write_dataclass_to_csv(row, PROLOG_FILE_NAME)
    return result


def run_logic(input_text: str):
    prolog.consult(PROLOG_FILE_NAME)

    chat = ChatOpenAI(temperature=0)
    messages = [
        SystemMessage(content=SYSTEM_ASKING_PROMPT),
        HumanMessage(content=f"{ASSISTANT_ASKING_PROMPT} {input_text}"),
    ]

    return chat(messages)
