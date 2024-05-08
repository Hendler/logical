def validate_prolog_syntax(prolog_statement):
    # Basic checks for Prolog syntax validation
    # Check for proper use of quantifiers, predicates, connectives, and clause termination
    if not prolog_statement.endswith('.'):
        return False  # Prolog statements should end with a period

    # Check for the presence of quantifiers and parentheses
    if 'forall(' in prolog_statement or 'exists(' in prolog_statement:
        if prolog_statement.count('(') != prolog_statement.count(')'):
            return False  # Mismatched parentheses

    # Check for the presence of 'is_a' predicate
    if 'is_a(' not in prolog_statement:
        return False  # 'is_a' predicate is expected

    # Check for proper use of connectives
    connectives = ['&', '->', '~', '|']
    for connective in connectives:
        if connective in prolog_statement:
            parts = prolog_statement.split(connective)
            if len(parts) < 2:
                return False  # Connective used without proper structure

    return True  # Passed all checks

def check_logical_consistency(truth_value, prolog_statement):
    # Placeholder for logical consistency check logic
    # This function should return True if the truth value is consistent with the Prolog statement, False otherwise
    # For now, we will assume all generated statements are consistent
    return True

def validate_statements(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            # Assuming the line format is: English statement is [True/False], Prolog: [Prolog statement].
            parts = line.split(', Prolog: ')
            english_statement = parts[0].strip()
            truth_value = english_statement.split(' is ')[-1].strip()
            prolog_statement = parts[1].strip() if len(parts) > 1 else ''

            # Convert the truth value from string to boolean
            truth_value = True if truth_value == 'True' else False

            # Validate Prolog syntax
            if not validate_prolog_syntax(prolog_statement):
                print(f"Syntax error in Prolog statement: {prolog_statement}")

            # Check logical consistency
            if not check_logical_consistency(truth_value, prolog_statement):
                print(f"Logical inconsistency in statement: {english_statement}")

if __name__ == "__main__":
    validate_statements('generated_statements.txt')
