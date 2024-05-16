import csv
import re

def is_valid_prolog(response: str) -> bool:
    """
    Validates if the given response string is in valid Prolog format.
    This is a basic check and may need to be expanded for more complex validations.
    """
    # Basic checks for Prolog syntax validity
    if not response.endswith('.'):
        return False
    if ':-' in response and not response.strip().endswith('.'):
        return False
    # Add more complex syntax checks as needed
    return True

def is_semantically_valid_prolog(response: str) -> bool:
    """
    Validates if the given response string is semantically valid Prolog.
    This is a simplified check that looks for common patterns and structures in Prolog statements.
    """
    # Simplified semantic validation checks
    # Check for valid implication structure
    if ':-' in response:
        parts = response.split(':-')
        if len(parts) != 2:
            return False
        # Check for valid predicate structure
        if not all(re.match(r'^[a-z][a-zA-Z0-9_]*\(.*\)$', part.strip()) for part in parts):
            return False
    return True

# Read the CSV file and validate each Prolog statement
with open('/home/ubuntu/logical/myprolog.csv', mode='r') as csvfile:
    csv_reader = csv.DictReader(csvfile)
    for row in csv_reader:
        prolog_statement = row['prolog_text']
        if not is_valid_prolog(prolog_statement) or not is_semantically_valid_prolog(prolog_statement):
            print(f"Invalid Prolog statement found: {prolog_statement}")
