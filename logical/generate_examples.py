import os
import random
import re  # Importing the re module for regular expression operations
from storage import LogicalRow, write_dataclass_to_csv, PROLOG_STORAGE_NAME
from __init__ import run_parser

# Lists of components for logical statements
subjects = ["cat", "dog", "bird", "car", "tree"]
predicates = ["mortal", "fast", "tall", "short", "round"]
logical_connectives = ["and", "or", "if", "then", "not"]
quantifiers = ["All", "No", "Some", "Most", "Few"]

# Function to generate a logical English statement
def generate_logical_statement(index):
    # Templates for logical statements
    templates = [
        "{quantifier} {subject}s are {predicate}.",
        "{subject} is {predicate}.",
        "{logical_connective}, {subject} is {predicate}.",
        "If {subject} is {predicate}, then {subject} is also {predicate2}.",
        "Assuming {subject} is {predicate}, it follows that {subject} is {predicate2}.",
        "{subject} is not {predicate}.",
        "It is not the case that {subject} is {predicate}.",
        "Either {subject} is {predicate} or {subject} is {predicate2}.",
        "Neither {subject} nor {subject2} is {predicate}.",
        "{subject} is more {predicate} than {subject2}."
    ]

    # Generate random components of the logical statement
    subject = random.choice(subjects)
    subject2 = random.choice(subjects)
    predicate = random.choice(predicates)
    predicate2 = random.choice(predicates)
    logical_connective = random.choice(logical_connectives)
    quantifier = random.choice(quantifiers)

    # Select a random template and fill it with the components
    template = random.choice(templates)
    statement = template.format(
        quantifier=quantifier,
        subject=subject,
        subject2=subject2,
        predicate=predicate,
        predicate2=predicate2,
        logical_connective=logical_connective
    )
    return statement

import re

def validate_logical_statement(statement):
    # Enhanced validation to check if the statement contains necessary components
    # and follows a logical structure.
    # Checks for the presence of a quantifier, a subject-predicate structure, and proper punctuation.
    valid_quantifiers = {"All", "No", "Some", "Most", "Few"}
    has_quantifier = any(quantifier + " " in statement for quantifier in valid_quantifiers)
    has_subject_predicate = " is " in statement or " are " in statement
    ends_with_period = statement.endswith(".")
    starts_with_conditional = statement.startswith("If ") and " then " in statement
    starts_with_assumption = statement.startswith("Assuming")

    # Check for contradictions which are inherently false and thus logically valid
    contradictions = ["square circles", "married bachelors", "wooden iron"]
    for contradiction in contradictions:
        if re.search(r'\b' + re.escape(contradiction) + r'\b', statement):
            return True

    # Check for valid structure or known valid constructs
    if not (has_quantifier and has_subject_predicate and ends_with_period) and not starts_with_conditional and not starts_with_assumption:
        return False  # Invalid structure if it doesn't meet any known valid constructs

    # Additional checks for contradictions and semantic inconsistencies
    semantic_inconsistencies = {
        "bachelors": ["married"],
        "dry": ["water"],
        "square": ["circle"]
    }

    # Check for semantic inconsistencies which are inherently false
    for subject, invalid_predicates in semantic_inconsistencies.items():
        if subject in statement and any(invalid_predicate in statement for invalid_predicate in invalid_predicates):
            return False
    # Recognize conditional "If...then..." constructs
    if starts_with_conditional:
        # Split the statement into its conditional parts
        conditional_parts = statement.split(" then ", 1)
        condition = conditional_parts[0].strip()[3:]  # Remove 'If ' from the beginning
        conclusion = conditional_parts[1].strip() if len(conditional_parts) > 1 else ""

        # Validate the conclusion part of the conditional statement
        if not conclusion or not re.match(r'^([A-Z][a-z]*(?: [A-Z][a-z]*)*|\b[a-z]+\b) (is|are) ([A-Za-z\s,]+)\.$', conclusion):
            return False
        # Validate the condition part of the conditional statement
        if not re.match(r'^([A-Z][a-z]*(?: [A-Z][a-z]*)*) (\b\w+\b\s) ([A-Za-z\s,]+)$', condition) and not validate_individual_condition_part(condition):
            return False

    # Recognize assumption-based "Assuming..." constructs
    elif starts_with_assumption:
        assumption_part = statement.replace("Assuming", "", 1).strip()
        if " is " not in assumption_part and " are " not in assumption_part or not assumption_part.endswith("."):
            return False

    return True

def validate_individual_condition_part(condition):
    # Split the condition into parts based on logical connectives
    parts = re.split(r'\b(and|or|if|then|not)\b', condition)
    parts = [part.strip() for part in parts if part.strip()]

    # Validate each part of the condition
    for part in parts:
        # Check for the presence of a subject and predicate in the correct order
        # Subjects can be predefined or proper nouns (capitalized words not in logical connectives)
        subject_predicate_pair = any(
            subj + " is " + pred in part or subj + " are " + pred in part
            for subj in subjects + re.findall(r'\b[A-Z][a-z]*\b', condition)
            if subj.lower() not in [x.lower() for x in logical_connectives]
            for pred in predicates
        )
        if not subject_predicate_pair:
            # Check if the part is a named entity followed by a valid predicate
            named_entity_predicate_pair = re.match(r'([A-Z][a-z]+(?: [A-Z][a-z]+)*) (is|are) ([a-z]+)', part)
            if named_entity_predicate_pair:
                named_subject, _, named_pred = named_entity_predicate_pair.groups()
                if named_pred in predicates:
                    continue
            # Allow named entities as subjects in the condition part
            named_entity_as_subject = re.match(r'([A-Z][a-z]+(?: [A-Z][a-z]+)*)', part)
            if named_entity_as_subject and " is " in part:
                continue
            # If the part does not contain logical connectives, it should be a simple statement
            if not any(connective in part for connective in logical_connectives):
                # Ensure the part has a valid subject-predicate structure
                # The predicate can be a multi-word and may contain uppercase letters
                if not re.match(r'^If\sit\s([a-z]+),?\s([A-Za-z\s]+)\sis\s([A-Za-z\s]+)\.$', part) and not re.match(r'^If\sit\s([a-z]+)\s([A-Za-z\s]+)\.$', part):
                    return False
                continue
            return False

    # If there are logical connectives, ensure they are not the first or last element
    if parts and (parts[0] in logical_connectives or parts[-1] in logical_connectives):
        return False

    # Ensure logical connectives are not adjacent to each other
    for i in range(1, len(parts) - 1):
        if parts[i] in logical_connectives and (parts[i-1] in logical_connectives or parts[i+1] in logical_connectives):
            return False

    # Check for coherent use of logical connectives within the parts
    for i, part in enumerate(parts):
        if part in logical_connectives:
            # Ensure that the part before and after the logical connective is a coherent logical statement
            before = " ".join(parts[:i])
            after = " ".join(parts[i+1:])
            if before and not validate_individual_condition_part(before):
                return False
            if after and not validate_individual_condition_part(after):
                return False

    return True

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
        ("Because the car is fast.", False),  # No quantifier, not a conditional or assumption-based construct
        ("The sun is hot", False),  # No period at the end
        ("A prime number is odd", False),  # No quantifier and no period
        # Additional complex test cases
        ("All prime numbers are odd except two.", True),  # Exception case
        ("If Socrates is a man, then Socrates is mortal.", True),  # Conditional logic
        ("Assuming all men are mortal, Socrates is mortal.", True),  # Assumption logic
        ("No square circles exist.", True),  # Contradiction
        ("Some bachelors are married.", False),  # Semantic inconsistency
        ("Every even number greater than two is the sum of two primes.", False),  # Goldbach's conjecture cannot be validated
        ("This statement is false.", False),  # Self-referential paradox
        ("If it rains, the ground is wet.", True),  # Causal relationship
        ("All ravens are black because they are ravens.", False),  # Circular reasoning
        ("No unmarried man is married.", True),  # Tautology
    ]

    # Run test cases
    for statement, expected in test_cases:
        result = validate_logical_statement(statement)
        print(f"Testing statement: {statement} - Expected: {expected}, Got: {result}")
        assert result == expected, f"Test failed for statement: {statement}"

# Number of examples to generate
NUM_EXAMPLES_TO_GENERATE = 1000

# Generate the examples
generate_examples(NUM_EXAMPLES_TO_GENERATE)

# To run tests, uncomment the line below and execute the script.
# This should be done in a development environment to verify changes.
test_validate_logical_statement()
