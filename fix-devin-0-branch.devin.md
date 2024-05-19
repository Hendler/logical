Playbook: Simplify Logical Repo

## Overview

Earlier, Devin was refactoring to push to pypi and it broke invoke (logical/tasks.py), and there is functionality in both tasks and logical/__init__.py that is redundant and incomplete.





## Procedure

1. pull in the latest changes from the devin-0 branch
2. don't use invoke. use __main__.py so that when some on pip installs

3. make sure it can be instantiated and runs cleanly
4. make sure all documentation is up to date
8.  move test_prolog_validation and prolog_syntax_tests.pl to /tests
9. move heights_logic.pl to tests
10. make sure it can be installed from a clean environment with pip install. Our desired behavior is that this installs this as a binary which can be run with "logical [commands]"

