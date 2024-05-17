from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from invoke import Collection, task
from .logic import run_logic_task

ns = Collection()
ns.add_task(run_logic_task)
