Playbook: Simplify Logical Repo

## Overview

We want the logical repo to be a simple invoke task that can be installed via pip. Modify as little code as possible, and do so cleanly.

## Procedure

1. pull in the latest changes from the devin-0 branch
2. notice the refactored files in logical/tasks/
3. make sure it can be instantiated and runs.
4. make sure the desired behavior is achieved for `parse`. Which is that 1) openai converts english to prolog 2) the prolog is validated by running in prolog 3) the valid prolog is saved to world.pl 4) the file world.pl can be loaded
5. make sure the desired behaviror for `interactive-logic` where 1) world.pl is loaded, 2) new sentences can be convereted to prolog and run as a query against the world.pl to determine their truth value
7. some functions in function.py may be unused. remove them if they are completly unused.
8. make sure it can be installed from a clean environment with pip install.

