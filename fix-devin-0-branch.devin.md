Playbook: Simplify Logical Repo

## Overview

We want the logical repo to be a simple invoke task that can be installed via pip. Modify as little code as possible, and do so cleanly.

## Procedure

1. pull in the latest changes from the devin-0 branch
2. notice the refactored files in logical/tasks/
3. make sure it can be instantiated and runs.
4. make sure the desired behavior is achieved for `parse`. Which is that 1) openai converts english to prolog 2) the prolog is validated by running in prolog 3) the valid prolog is saved to world.pl 4) the file world.pl can be loaded
5. make sure the desired behaviror for `interactive-logic` where 1) world.pl is loaded, 2) new sentences can be convereted to prolog and run as a query against the world.pl to determine their truth value
6. ensure the user experience is one where a user can enter various english sentences, even several paragraphs and continually add it to world.py in the proper sections so that facts and other statements accumulate. Then the user should be able to query that world in interactive mode. Tests should be set up so that a 500 words of english can be parsed into prolog logic, saved to world.pl to create a fact database, then a user can ask logical questions about that world with natural language. This user experience is critical. The code should be easy to follow and understand, and the "quick start" documentation in the readme should be accurate and easy to understand.
7. some functions in function.py may be unused. remove them if they are completly unused.
8. make sure it can be installed from a clean environment with pip install.

