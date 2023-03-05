from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import AIMessage, HumanMessage, SystemMessage


# prompts for chatgpt

SYSTEM_PARSING_PROMPT = """
You are a logic extractor, converting english statements to prolog, checking for the logical consistency of statements.
This requires categorizing and extracting the first class objects, and then their logical relationships.
No explanation is required, and you will output prolog only.

"""

ASISSITANT_PARSING_PROMPT = """
Please generate pure, runnable prolog extracting factual statements from the following. \n

"""

SYSTEM_ASKING_PROMPT = """
You are an assistant who is both reading prolog, and the output of running of the prolog.
It is your job to explain why the the prolog completed or failed. The explanation
should not be about the code itself, but where there might be errors in the original languages logic.
Information could be missing to say conclusively.
"""


ASSISTANT_ASKING_PROMPT = """
Please explaing why the logic is correct or incorrect, or what might be missing.  \n

"""


def run_parser(input_text: str):
    chat = ChatOpenAI(temperature=0)
    messages = [
        SystemMessage(content=SYSTEM_PARSING_PROMPT),
        HumanMessage(content=f"{ASISSITANT_PARSING_PROMPT} {input_text}"),
    ]
    return outchat(messages)


def run_logic(input_text: str):
    chat = ChatOpenAI(temperature=0)
    messages = [
        SystemMessage(content=SYSTEM_ASKING_PROMPT),
        HumanMessage(content=f"{ASSISTANT_ASKING_PROMPT} {input_text}"),
    ]
    return outchat(messages)
