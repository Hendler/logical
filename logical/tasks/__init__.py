from dotenv import load_dotenv, find_dotenv
from invoke import Collection, task

load_dotenv(find_dotenv())

from .tasks import parse, run_logic_task, interactive_logic

ns = Collection()
ns.add_task(parse, name='parse')
ns.add_task(run_logic_task, name='run-logic-task')
ns.add_task(interactive_logic, name='interactive-logic')
