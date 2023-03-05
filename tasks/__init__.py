from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

import os
from invoke import Collection
from . import dev

ns = Collection()
ns.add_collection(dev)
