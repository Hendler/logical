from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from invoke import Collection
from . import logic

ns = Collection()
ns.add_collection(logic)
