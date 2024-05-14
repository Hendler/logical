import os
import random
from logical.storage import LogicalRow, write_dataclass_to_csv, PROLOG_STORAGE_NAME
from logical import run_parser

# Function to generate a logical English statement
def generate_logical_statement(index):
    # This function generates diverse logical statements.
    # For demonstration purposes, it returns a variety of simple logical statements.
    subjects = ["Socrates", "a cat", "the car", "the sun", "a prime number"]
    predicates = ["is mortal", "is on the mat", "is fast", "is hot", "is odd"]
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

# Function to generate logical examples and their Prolog representations
def generate_examples(count):
    generated_statements = set()  # Set to keep track of generated statements to avoid duplicates
    for i in range(count):
        try:
            # Generate a logical English statement
            english_statement = generate_logical_statement(i)
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

# Number of examples to generate
NUM_EXAMPLES_TO_GENERATE = 999

# Generate the examples
generate_examples(NUM_EXAMPLES_TO_GENERATE)
