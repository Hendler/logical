import os

from invoke import Collection
from . import dev

ns = Collection()
ns.add_collection(dev)
