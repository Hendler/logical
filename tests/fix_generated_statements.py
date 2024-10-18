import csv
from datetime import datetime

# Define the path to the input file
input_file_path = '/home/ubuntu/logical/tests/generated_statements.txt'
# Define the path to the output file, including a timestamp to make it unique
output_file_path = f'/home/ubuntu/logical/tests/fixed_statements_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'

# Define a function to fix the Prolog translation errors
def fix_prolog_translation(statement):
    # The actual logic will involve parsing the English statements, understanding the logical constructs,
    # and then generating the corresponding Prolog statements.

    # Simplified logic to handle specific translation errors identified in the statements
    # This is a basic example and should be expanded to cover all logical constructs and their Prolog syntax
    fixed_statement = statement
    subject = extract_subject(statement)  # Dynamically determine the subject of the statement

    # Improved handling of negations
    if 'No' in statement:
        # Apply negation to the predicate directly, considering the context and the subject
        predicate = ' '.join(statement.split(' ')[2:])  # Assuming the predicate follows the subject
        fixed_statement = f'not({subject}, {predicate})'

    # Improved handling of universal quantifiers
    if 'All' in statement:
        # Translate 'All' to 'forall' to reflect universal quantification in Prolog
        predicate = ' '.join(statement.split(' ')[2:])  # Assuming the predicate follows the subject
        fixed_statement = f'forall({subject}, {predicate})'

    # Improved handling of existential quantifiers
    if 'Some' in statement:
        # Translate 'Some' to 'exists' to reflect existential quantification in Prolog
        predicate = ' '.join(statement.split(' ')[2:])  # Assuming the predicate follows the subject
        fixed_statement = f'exists({subject}, {predicate})'

    # Improved handling of conditional statements
    if statement.startswith('If'):
        # Translate conditional statements into Prolog implications
        parts = statement.replace('If ', '').split(' then ')
        if len(parts) == 2:
            condition, conclusion = parts
        else:
            # For statements without an explicit 'then', we assume the conclusion is a negation of the condition
            condition = parts[0]
            conclusion = f'not({condition})'
        # Ensure no trailing commas or periods in the Prolog translation
        condition = condition.strip().rstrip(',').rstrip('.')
        conclusion = conclusion.strip().rstrip(',').rstrip('.')
        fixed_statement = f'{conclusion} :- {condition}'

    # Add more translation rules as needed here

    return fixed_statement

# New function to extract the subject from the English statement
def extract_subject(statement):
    # Implement logic to extract the subject from the statement
    # Example implementation (this will need to be refined):
    words = statement.split()
    for i, word in enumerate(words):
        if word.lower() in ['no', 'all', 'some', 'every']:
            return words[i+1]  # Assumes the subject follows these quantifiers
    return "subject"  # Default subject if none found

# Open the input file and create the output file
with open(input_file_path, 'r') as infile, open(output_file_path, 'w', newline='') as outfile:
    # Create a CSV reader and writer
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    # Write the header to the output file
    writer.writerow(['English Statement', 'Prolog Statement', 'Truth Value'])

    # Iterate over each line in the input file
    for row in reader:
        try:
            # Check if the line contains the expected 'Prolog:' separator
            if ', Prolog: ' in row[0]:
                # Split the line into the English statement and the rest
                english_statement, rest = row[0].split(', Prolog: ')
                # Extract the truth value from the rest of the line
                truth_value = 'True' if 'is True' in rest else 'False'
            else:
                # Handle lines without the 'Prolog:' separator
                # Assuming the format 'English statement is True/False'
                if ' is ' in row[0]:
                    parts = row[0].rsplit(' is ', 1)
                    english_statement = parts[0]
                    truth_value = parts[1]
                else:
                    # If ' is ' is not in the line, attempt to determine the truth value based on the statement
                    # This logic should be refined based on the actual requirements for truth value determination
                    english_statement = row[0]
                    # Default truth value for statements without explicit truth value
                    truth_value_keywords = {
                        'false': ['have fur', 'have wheels', 'can fly', 'are bipedal', 'are mortal', 'have wings', 'can speak'],
                        'true': ['have engines', 'can swim', 'are edible', 'require water', 'use electricity']
                    }
                    truth_value = 'False' if any(keyword in english_statement for keyword in truth_value_keywords['false']) else 'True'
                    if truth_value == 'True':
                        truth_value = 'False' if any(keyword in english_statement for keyword in truth_value_keywords['true']) else 'True'

            # Fix the Prolog translation
            prolog_statement = fix_prolog_translation(english_statement)
            # Write the fixed statement and the truth value to the output file
            writer.writerow([english_statement, prolog_statement, truth_value])
        except ValueError as e:
            # Handle lines that do not conform to the expected format
            print(f"Skipping line due to error: {e} - {row[0]}")

print(f"Fixed statements have been written to {output_file_path}")

# Test suite for the extract_subject function
def test_extract_subject():
    test_cases = [
        ("No cats have wings", "cats"),
        ("All dogs are friendly", "dogs"),
        ("Some birds can fly", "birds"),
        ("Every car has wheels", "car"),
        # Add more test cases as needed
    ]

    for statement, expected_subject in test_cases:
        extracted_subject = extract_subject(statement)
        assert extracted_subject == expected_subject, f"Test failed for statement: '{statement}'. Expected subject: '{expected_subject}', got: '{extracted_subject}'"

    print("All tests passed for extract_subject function.")

# Call the test suite
test_extract_subject()

# Test suite for the fix_prolog_translation function
def test_fix_prolog_translation():
    test_cases = [
        ("No cats have wings", "not(cats, have wings)"),
        ("All dogs are friendly", "forall(dogs, are friendly)"),
        ("Some birds can fly", "exists(birds, can fly)"),
        ("If it rains, then the ground is wet", "the ground is wet :- it rains"),
        # Add more test cases as needed
    ]

    for statement, expected_prolog in test_cases:
        fixed_prolog = fix_prolog_translation(statement)
        assert fixed_prolog == expected_prolog, f"Test failed for statement: '{statement}'. Expected Prolog: '{expected_prolog}', got: '{fixed_prolog}'"

    print("All tests passed for fix_prolog_translation function.")

# Call the test suite
test_fix_prolog_translation()
