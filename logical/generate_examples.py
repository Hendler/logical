import os
import random
from logical.storage import LogicalRow, write_dataclass_to_csv, PROLOG_STORAGE_NAME
from logical import run_parser

# Function to generate a logical English statement
def generate_logical_statement(index):
    # This function generates diverse logical statements.
    # For demonstration purposes, it returns a variety of simple logical statements.
    subjects = ["Socrates", "a cat", "the car", "the sun", "a prime number", "an electron", "a molecule", "a mathematician", "a planet", "a galaxy"]
    predicates = ["is mortal", "is on the mat", "is fast", "is hot", "is odd", "is charged", "is tiny", "is brilliant", "is round", "is vast"]
    logical_connectives = ["Therefore", "Because", "Since", "If", "Assuming"]
    quantifiers = ["All", "No", "Some", "Most", "Few"]

    # Generate random components of the logical statement
    subject = random.choice(subjects)
    predicate = random.choice(predicates)
    logical_connective = random.choice(logical_connectives)
    quantifier = random.choice(quantifiers)

    # Construct the logical statement
    statement = f"{quantifier} {subject}s are {predicate}. {subject} is a {subject}. {logical_connective}, {subject} is {predicate}."
    return statement

# Function to validate the logical consistency of a statement
def validate_logical_statement(statement):
    # Basic validation to check if the statement contains necessary components
    # and follows a logical structure.
    # This is a placeholder for a more complex validation logic.
    return (" is " in statement) and (statement.endswith("."))

# Function to generate logical examples and their Prolog representations
def generate_examples(count):
    generated_statements = set()  # Set to keep track of generated statements to avoid duplicates
    for i in range(count):
        try:
            # Generate a logical English statement
            english_statement = generate_logical_statement(i)
            # Validate the logical consistency of the statement
            if not validate_logical_statement(english_statement):
                raise ValueError(f"Invalid logical statement: {english_statement}")
            # Check for uniqueness
            if english_statement not in generated_statements:
                generated_statements.add(english_statement)
                # Convert the English statement to a Prolog representation using the run_parser function
                prolog_statement = run_parser(english_statement)
                # Create a LogicalRow instance
                logical_row = LogicalRow(input_text=english_statement, prolog_text=prolog_statement)
                # Write the LogicalRow instance to the CSV file
                write_dataclass_to_csv(logical_row, PROLOG_STORAGE_NAME)
                print(f"Generated example {i+1}/{count}: {english_statement}")
            else:
                print(f"Duplicate statement detected, skipping: {english_statement}")
        except Exception as e:
            print(f"An error occurred while generating example {i+1}: {e}")

# Test cases for validate_logical_statement function
def test_validate_logical_statement():
    # Test cases with expected outcomes
    test_cases = [
        ("All cats are mortal.", True),
        ("Some suns are hot.", True),
        ("No electron is charged.", True),
        ("Most planets are round.", True),
        ("Few galaxies are vast.", True),
        ("Socrates is.", False),  # Incomplete statement
        ("If a cat then is on the mat.", False),  # Illogical structure
        ("Because the car is fast.", False),  # No quantifier
        ("The sun is hot", False),  # No period at the end
        ("A prime number is odd", False)  # No quantifier and no period
    ]

    # Run test cases
    for statement, expected in test_cases:
        result = validate_logical_statement(statement)
        assert result == expected, f"Test failed for statement: {statement}"

# Number of examples to generate
NUM_EXAMPLES_TO_GENERATE = 999

# Generate the examples
generate_examples(NUM_EXAMPLES_TO_GENERATE)

# Uncomment the line below to run tests
# test_validate_logical_statement()
