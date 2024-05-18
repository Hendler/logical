import re

# Define the validate_prolog_code function as it appears in tasks.py
def validate_prolog_code(prolog_code):
    """
    Validates the syntax of the generated Prolog code.

    Parameters:
    - prolog_code (str): The generated Prolog code to validate.

    Returns:
    - (bool, str): A tuple containing a boolean indicating if the validation passed and an error message if it failed.
    """
    # Remove comments and strip whitespace from each line
    # Handle both single-line (%) and multi-line (/* ... */) comments
    stripped_code_lines = []
    in_multiline_comment = False
    for line in prolog_code.splitlines():
        while '/*' in line or '*/' in line:
            if '/*' in line:
                in_multiline_comment = True
                comment_start_index = line.find('/*')
                comment_end_index = line.find('*/', comment_start_index + 2)
                if comment_end_index != -1:
                    # A complete comment block is found, remove it
                    line = line[:comment_start_index] + line[comment_end_index + 2:]
                    in_multiline_comment = False
                else:
                    # Only the start of a comment block is found, remove from start to end of line
                    line = line[:comment_start_index]
                    break
            elif '*/' in line and in_multiline_comment:
                # End of a comment block is found, remove from start to the end of the comment block
                comment_end_index = line.find('*/') + 2
                line = line[comment_end_index:]
                in_multiline_comment = False
        if not in_multiline_comment:
            line = line.split('%')[0]
        stripped_code_lines.append(line.rstrip())

    stripped_code = "\n".join(stripped_code_lines)

    # Check for balanced parentheses
    parentheses_stack = []
    for char in stripped_code:
        if char == '(':
            parentheses_stack.append(char)
        elif char == ')':
            if not parentheses_stack or parentheses_stack[-1] != '(':
                return False, 'Error: Unbalanced parentheses detected.'
            parentheses_stack.pop()

    if parentheses_stack:
        return False, 'Error: Unbalanced parentheses detected.'

    # Define states for the finite state machine
    NORMAL, IN_STRING, IN_COMMENT, ESCAPE_IN_STRING = range(4)
    state = NORMAL
    comment_depth = 0  # Track the depth of nested comments

    # Check that each statement ends with a period, handling string literals and comments
    for line in stripped_code.splitlines():
        if line:
            i = 0
            while i < len(line):
                char = line[i]
                if state == NORMAL:
                    if char == "'":
                        state = IN_STRING
                    elif char == '%':
                        break  # Ignore the rest of the line after a single-line comment
                    elif char == '/' and i < len(line) - 1 and line[i+1] == '*':
                        state = IN_COMMENT
                        comment_depth += 1
                        i += 1  # Skip the next character as it is part of '/*'
                elif state == IN_STRING:
                    if char == "\\":
                        state = ESCAPE_IN_STRING
                    elif char == "'":
                        state = NORMAL
                elif state == ESCAPE_IN_STRING:
                    state = IN_STRING  # Return to IN_STRING state after an escape sequence
                elif state == IN_COMMENT:
                    if char == '*' and i < len(line) - 1 and line[i+1] == '/':
                        comment_depth -= 1
                        if comment_depth == 0:
                            state = NORMAL
                        i += 1  # Skip the next character as it is part of '*/'
                i += 1
            # Check if the period is at the end of the line, ignoring trailing whitespace
            if state == NORMAL and not line.rstrip().endswith('.'):
                return False, 'Error: Each Prolog statement must end with a period outside of string literals and comments.'
            # Reset state for the next line if not within a string or comment
            if state != IN_COMMENT:
                state = NORMAL

    # Check for correct usage of operators
    operator_pattern = r'(?<!\S)(:-|;|,|\.)'
    if re.search(operator_pattern, stripped_code) and not re.search(r'\b[a-z]+\([\w, ]+\)\s*(?::-\s*.+)?\.', stripped_code):
        return False, 'Error: Missing or incorrect usage of operators.'

    # Check for directives
    directive_pattern = r':-\s*[a-zA-Z_][a-zA-Z0-9_]*\s*(\([\w, ]+\))?\s*(?=\.)'
    if ':-' in stripped_code and not re.search(directive_pattern, stripped_code):
        return False, 'Error: Invalid directive syntax.'

    # Check for facts and rules structure
    fact_rule_pattern = r'\b[a-z]+\([\w, ]+\)(\s*:-\s*.+)?\.'
    if not re.search(fact_rule_pattern, stripped_code):
        return False, 'Error: Invalid facts or rules structure.'

    return True, 'Prolog code syntax is correct.'

# Read the Prolog code samples from prolog_syntax_tests.pl
with open('prolog_syntax_tests.pl', 'r') as file:
    prolog_samples = file.read().split('\n\n')  # Assuming each sample is separated by a blank line

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
    assert validation_passed == expected_result, f"Test failed for {description}: {sample}"
