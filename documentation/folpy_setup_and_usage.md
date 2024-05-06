# FOLPy Setup and Usage Documentation

## Installation
To install FOLPy, run the following command in your virtual environment:
```
pip install folpy
```

## Overview
FOLPy is a First Order Logic Python Library designed to work with structures such as lattices and posets. It provides utilities for creating and manipulating these structures and methods for testing substructures with or without isomorphism filters.

## Example Usage
The following example demonstrates how to use FOLPy to create models and test substructures:

```python
from unittest import TestCase
import random

from folpy.examples import lattices, posets
from folpy.utils.methods import (
    substructures_updown,
    substructures_downup,
    substructures_by_maximals
)

# Define a list of models using functions from folpy.examples
models = [
    lattices.gen_chain(2),
    lattices.gen_chain(3),
    lattices.gen_chain(4),
    lattices.gen_chain(5),
    lattices.gen_chain(2) * lattices.gen_chain(3),
    lattices.rhombus,
    lattices.M3,
    lattices.N5,
    posets.gen_chain(2),
    posets.gen_chain(3),
    posets.gen_chain(4),
    posets.gen_chain(5),
    posets.gen_chain(2) * posets.gen_chain(3),
    posets.rhombus,
    posets.M3
]

# Define a test class using the TestCase class from unittest
class SubstructuresTest(TestCase):
    def test_always_passes(self):
        self.assertTrue(
            self.without_iso(),
            msg="error in substructure without isomorphism"
        )
        self.assertTrue(
            self.with_iso(),
            msg="error in substructure with isomorphism"
        )

    # Helper method to test substructures without isomorphism filters
    def without_iso(self):
        result = True
        for model in random.choices(models, k=5):
            t = len(list(substructures_downup(model, filter_isos=False))) == \
                len(list(substructures_updown(model, filter_isos=False)))
            result = result and t
        for model in random.choices(models, k=5):
            t = len(list(substructures_updown(model, filter_isos=False))) == \
                len(list(substructures_by_maximals(model, filter_isos=False)))
            result = result and t
        return result

    # Helper method to test substructures with isomorphism filters
    def with_iso(self):
        result = True
        for model in random.choices(models, k=5):
            t = len(list(substructures_updown(model, filter_isos=True))) == \
                len(list(substructures_by_maximals(model, filter_isos=True)))
            result = result and t
        return result
```

This example showcases the creation of models using `folpy.examples` and the application of `folpy.utils.methods` to test the substructures of these models.
