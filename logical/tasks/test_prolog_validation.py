import re
import os
from pyswip import Prolog

# Define the validate_prolog_code function as it appears in tasks.py
def validate_prolog_code(prolog_code):
    """
    Validates the syntax of the generated Prolog code.

    Parameters:
    - prolog_code (str): The generated Prolog code to validate.

    Returns:
    - (bool, str): A tuple containing a boolean indicating if the validation passed and an error message if it failed.
    """
    print("Entering validate_prolog_code function")

    # Manually remove all comments from the Prolog code to handle nested comments
    def strip_comments(code):
        stripped_code = ""
        stack = []
        i = 0
        while i < len(code):
            if code[i : i + 2] == "/*":
                stack.append("/*")
                i += 2
                continue  # Skip appending characters and move to the next iteration
            elif code[i : i + 2] == "*/" and stack:
                stack.pop()
                i += 2
                continue  # Skip appending characters and move to the next iteration
            elif not stack and code[i] == "%":
                # Skip the rest of the line after a single-line comment
                i = code.find("\n", i)
                if i == -1:  # If no newline is found, we are at the end of the code
                    break
            elif not stack:
                stripped_code += code[i]
            i += 1
        return stripped_code

    stripped_code = strip_comments(prolog_code)

    # Check for balanced parentheses
    parentheses_stack = []
    for char in stripped_code:
        if char == "(":
            parentheses_stack.append(char)
        elif char == ")":
            if not parentheses_stack or parentheses_stack[-1] != "(":
                return False, "Error: Unbalanced parentheses detected."
            parentheses_stack.pop()

    if parentheses_stack:
        return False, "Error: Unbalanced parentheses detected."

    # Define states for the finite state machine
    NORMAL, IN_STRING, ESCAPE_IN_STRING = range(3)
    state = NORMAL

    # Check that each statement ends with a period, handling string literals
    for line in stripped_code.splitlines():
        i = 0
        while i < len(line):
            char = line[i]
            if state == NORMAL:
                if char == "'":
                    state = IN_STRING
            elif state == IN_STRING:
                if char == "\\":
                    state = ESCAPE_IN_STRING
                elif char == "'":
                    state = NORMAL
            elif state == ESCAPE_IN_STRING:
                state = IN_STRING  # Return to IN_STRING state after an escape sequence

            i += 1  # Increment i at the end of each loop iteration

        # Check if the period is at the end of the line, ignoring trailing whitespace
        if state == NORMAL and not line.rstrip().endswith("."):
            return (
                False,
                "Error: Each Prolog statement must end with a period outside of string literals.",
            )
        # Reset state for the next line if not within a string
        if state != IN_STRING:
            state = NORMAL

    def run_prolog_code(prolog_code):
        """
        Runs the given Prolog code using the SWI-Prolog interpreter to validate its syntax and semantics.

        Parameters:
        - prolog_code (str): The generated Prolog code to validate.

        Returns:
        - (bool, str): A tuple containing a boolean indicating if the validation passed and an error message if it failed.
        """
        prolog = Prolog()
        try:
            prolog.assertz(prolog_code)
        except Exception as e:
            return False, f"Prolog interpreter error: {e}"
        finally:
            prolog.retractall(prolog_code)  # Clean up the Prolog environment

        return True, "Prolog code syntax is correct."

    # Replace the regex-based validation with the Prolog interpreter validation
    validation_passed, error_message = run_prolog_code(stripped_code)
    if not validation_passed:
        return False, error_message

    return True, "Prolog code syntax is correct."


print("Current working directory:", os.getcwd())

# The following code block has been removed as it is not necessary for the unit tests
# and the file prolog_syntax_tests.pl does not exist.
# with open("logical/tasks/prolog_syntax_tests.pl", "r") as file:
#     prolog_samples = file.read().split(
#         "\n\n"
#     )  # Assuming each sample is separated by a blank line

# Additional test cases to cover edge cases
additional_tests = {
    "Nested comments": ("/* Comment /* nested comment */ end comment */", True),
    "String with escaped single quote": ("likes(john, 'Soccer\\'s fun').", True),
    "Complex directive": (":- dynamic cow/1.", True),
}

# Combine predefined samples with additional tests
prolog_samples.extend([test[0] for test in additional_tests.values()])

# Test each Prolog code sample
for sample in prolog_samples:
    validation_passed, error_message = validate_prolog_code(sample)
    if validation_passed:
        print(f"Validation passed for sample:\n{sample}")
    else:
        print(f"Validation failed for sample:\n{sample}\nError: {error_message}")

# Test additional edge cases
for description, (sample, expected_result) in additional_tests.items():
    validation_passed, _ = validate_prolog_code(sample)
    assert(validation_passed == expected_result), f"Test failed for {description}: {sample}"

# Additional complex Prolog syntax tests
complex_syntax_tests = {
    "Multiple predicates": ("animal(cow). likes(mary, cow).", True),
    "Rule with multiple conditions": ("flies(X) :- bird(X), not(penguin(X)).", True),
    "Rule with conjunction and disjunction": ("likes(X, Y) :- (cat(X), mouse(Y)); (dog(X), bone(Y)).", True),
    "Fact with negation": ("not(likes(john, rain)).", True),
    "Invalid rule structure": ("flies(X) :- bird(X) not(penguin(X)).", False),  # Missing comma
    "Invalid fact structure": ("animal cow.", False),  # Missing parentheses
    "Valid directive": (":- dynamic animal/1.", True),
    "Invalid directive": (":- dynamic animal.", False),  # Missing arity
}

# Test additional complex Prolog syntax cases
for description, (sample, expected_result) in complex_syntax_tests.items():
    validation_passed, _ = validate_prolog_code(sample)
    assert(validation_passed == expected_result), f"Test failed for {description}: {sample}"
