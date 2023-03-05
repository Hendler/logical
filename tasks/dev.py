from invoke import task, run
from .utils import ROOT_REPO_DIR, printlogo
from logical import run_parser, run_logic


@task()
def run(ctx):
    printlogo("WELCOME TO LOGICAL - beep \a beep \a")

    ENDC = "\033[0m"
    WHITE = "\033[1;37m"
    OKBLUE = "\033[1;34m"
    RED = "\033[0;31m"
    YELLOW = "\033[1;33m"

    PROMPT = f"{YELLOW}Logical: {ENDC}"
    ASK_PROMPT = f"{RED}Ask: {ENDC}"
    INPUT_PROMPT = f"{WHITE}Input: {ENDC}"

    help_text = """Commands:
    - help
    - exit
    - parse: input text to extract logic from
    - ask: : ask a logical question

    """

    while True:
        response = input(f"{PROMPT}: ")
        if response == "exit":
            break
        elif response == "help":
            print(help_text)
        elif response == "parse":
            text_to_parse = input(f"{INPUT_PROMPT}: ")
            result = run_parser(text_to_parse)
        elif response == "ask":
            ask_away = input(f"{ASK_PROMPT}: ")
            result = run_logic(ask_away)
        else:
            print("wat")
