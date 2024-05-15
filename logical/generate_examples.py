import os
import random
import re  # Importing the re module for regular expression operations
from logical.storage import LogicalRow, write_dataclass_to_csv, PROLOG_STORAGE_NAME
from logical import run_parser

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
        "If {subject} is {predicate}, then {subject} is also {predicate2}.",
        "Assuming {subject} is {predicate}, it follows that {subject} is {predicate2}.",
        "Either {subject} is {predicate} or {subject2} is {predicate2}.",
        "Neither {subject} nor {subject2} is {predicate}.",
        "{subject} is not {predicate}.",
        "{subject} is more {predicate} than {subject2}.",
        "It is not the case that {subject} is {predicate}.",
        # Additional templates that ensure logical validity
        "It is always the case that {subject} is {predicate}.",
        "It is never the case that {subject} is {predicate}.",
        "It is possible that {subject} is {predicate}.",
        "It is impossible for {subject} to be {predicate}.",
        "{quantifier} {subject}s, if they are {predicate}, are also {predicate2}.",
        "{quantifier} {subject}s are either {predicate} or {predicate2}.",
        "If {subject} is not {predicate}, then {subject} is {predicate2}.",
        "Whether {subject} is {predicate} or not, it is {predicate2}.",
        "Whenever {subject} is {predicate}, {subject2} is {predicate2}.",
        "Wherever {subject} is {predicate}, {subject2} is {predicate2}.",
    ]

    # Generate random components of the logical statement
    subject = random.choice(subjects)
    subject2 = random.choice(subjects)
    predicate = random.choice(predicates)
    predicate2 = random.choice(predicates)
    quantifier = random.choice(quantifiers)

    # Select a random template and fill it with the components
    template = random.choice(templates)
    statement = template.format(
        quantifier=quantifier,
        subject=subject,
        subject2=subject2,
        predicate=predicate,
        predicate2=predicate2,
    )
    return statement

import re

def validate_logical_statement(statement):
    # List of known conjectures or statements that cannot be definitively proven
    conjectures = [
        "Every even number greater than two is the sum of two primes.",  # Goldbach's conjecture
        # Additional conjectures can be added here
    ]

    # Check if the statement is a known conjecture
    if statement in conjectures:
        return False  # Conjectures cannot be validated as true

    # Enhanced validation to check if the statement contains necessary components
    # and follows a logical structure.
    # Checks for the presence of a quantifier, a subject-predicate structure, and proper punctuation.
    valid_quantifiers = {"All", "No", "Some", "Most", "Few", "Every", "Any"}
    has_quantifier = any(quantifier + " " in statement for quantifier in valid_quantifiers)
    has_subject_predicate = re.search(r'\b(is|are)\b', statement) is not None
    ends_with_period = statement.endswith(".")
    starts_with_conditional = statement.startswith("If ") and ", then " in statement
    starts_with_assumption = statement.startswith("Assuming")
    has_negation = " not " in statement or statement.startswith("It is not the case")
    has_comparative = " more " in statement or " either " in statement or " neither " in statement

    # Check for contradictions which are inherently false and thus logically valid
    contradictions = ["square circles", "married bachelors", "wooden iron"]
    for contradiction in contradictions:
        if re.search(r'\b' + re.escape(contradiction) + r'\b', statement):
            return True

    # Check for valid structure or known valid constructs
    if not (has_quantifier and has_subject_predicate and ends_with_period) and not (starts_with_conditional or starts_with_assumption or has_negation or has_comparative):
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
        conditional_parts = statement.split(", then ", 1)
        condition = conditional_parts[0].strip()[3:]  # Remove 'If ' from the beginning
        conclusion = conditional_parts[1].strip() if len(conditional_parts) > 1 else ""
        # Validate the logical consistency of the conditional statement
        if validate_individual_condition_part(condition) and validate_individual_condition_part(conclusion):
            return True
        else:
            return False

    # Recognize assumption-based "Assuming..." constructs
    elif starts_with_assumption:
        assumption_part = statement.replace("Assuming", "", 1).strip()
        if " is " not in assumption_part and " are " not in assumption_part or not assumption_part.endswith("."):
            return False

    # Recognize negation constructs
    if has_negation:
        negation_part = statement.replace("It is not the case that ", "", 1).strip() if statement.startswith("It is not the case that ") else statement
        if " is " not in negation_part and " are " not in negation_part or not negation_part.endswith("."):
            return False

    # Recognize comparative constructs
    if has_comparative:
        comparative_match = re.match(r'(.+) is more (.+) than (.+)\.', statement)
        if not comparative_match:
            return False
        subject, predicate, subject2 = comparative_match.groups()
        if not subject or not predicate or not subject2:
            return False

    return True

def validate_individual_condition_part(condition):
    # Use regular expressions to match the pattern of a conditional statement
    # The regular expression now accounts for an optional comma before 'then'
    # and includes proper handling of proper nouns and multi-word predicates
    match = re.match(r'If\s+(.+?)\s+then\s+(.+)\s*$', condition, re.IGNORECASE)
    if match:
        condition_part, conclusion_part = match.groups()
        # Validate both the condition and conclusion parts as individual statements
        valid_condition = validate_statement_part(condition_part.strip().rstrip('.'))
        valid_conclusion = validate_statement_part(conclusion_part.strip().rstrip('.'))
        return valid_condition and valid_conclusion
    else:
        # If the statement does not match the conditional pattern, validate it as a simple statement
        return validate_statement_part(condition.strip().rstrip('.'))

def validate_statement_part(part):
    # Check for the presence of a subject and predicate in the correct order
    # Subjects can be predefined or proper nouns (capitalized words not in logical connectives)
    subject_predicate_pair = any(
        subj + " is " + pred in part or subj + " are " + pred in part
        for subj in subjects + re.findall(r'\b[A-Z][a-z]*\b', part)
        if subj.lower() not in [x.lower() for x in logical_connectives]
        for pred in predicates
    )
    if subject_predicate_pair:
        return True

    # Check if the part is a named entity followed by a valid predicate
    named_entity_predicate_pair = re.match(r'([A-Z][a-z]+(?: [A-Z][a-z]+)*) (is|are) ([A-Za-z\s]+)', part)
    if named_entity_predicate_pair:
        named_subject, _, named_pred = named_entity_predicate_pair.groups()
        # Allow for predicates that are not predefined but form a logically coherent statement
        if named_pred.lower().endswith(('er', 'est')) or named_pred.lower() in [p.lower() for p in predicates]:
            return True

    # If the part does not contain logical connectives, it should be a simple statement
    if not any(connective in part for connective in logical_connectives):
        # Ensure the part has a valid subject-predicate structure
        # The predicate can be a multi-word and may contain uppercase letters
        simple_statement_match = re.match(r'^([A-Z][a-z]+(?: [A-Z][a-z]+)*) (is|are) ([A-Za-z\s]+)\.$', part)
        if simple_statement_match:
            subject, verb, predicate = simple_statement_match.groups()
            # Allow for predicates that are not predefined but form a logically coherent statement
            if predicate.lower().endswith(('er', 'est')) or predicate.lower() in [p.lower() for p in predicates]:
                return True
            # Handle predicates that are proper nouns or multi-word phrases
            if predicate[0].isupper() or ' ' in predicate:
                return True

    return False

# Function to generate logical examples and their Prolog representations
def generate_examples():
    generated_statements = set()  # Set to keep track of generated statements to avoid duplicates
    while len(generated_statements) < NUM_EXAMPLES_TO_GENERATE:
        try:
            # Generate a logical English statement
            english_statement = generate_logical_statement(len(generated_statements))
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
                print(f"Generated example {len(generated_statements)}/{NUM_EXAMPLES_TO_GENERATE}: {english_statement}")
            else:
                print(f"Duplicate statement detected, skipping: {english_statement}")
        except Exception as e:
            print(f"An error occurred while generating example {len(generated_statements)}: {e}")

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
        ("Every even number greater than two is the sum of two primes.", False),  # Goldbach's conjecture is unproven
        ("This statement is false.", False),  # Self-referential paradox
        ("If it rains, the ground is wet.", True),  # Causal relationship
        ("All ravens are black because they are ravens.", False),  # Circular reasoning
        ("No unmarried man is married.", True),  # Tautology
        # New test cases for negation and comparative constructs
        ("It is not the case that a cat is mortal.", True),  # Negation
        ("A cat is more agile than a dog.", True),  # Comparative
        ("Neither a square is round nor a circle is square.", True),  # Neither-nor construct
        ("Either a figure is a square or it is not a square.", True),  # Either-or construct
        ("It is always the case that a bachelor is unmarried.", True),  # Always true
        ("It is never the case that water is dry.", True),  # Never true
        ("It is possible that a coin toss results in heads.", True),  # Possibility
        ("It is impossible for a square to be round.", True),  # Impossibility
        ("All cats, if they are pets, are also animals.", True),  # Conditional with quantifier
        ("All cats are either pets or wild animals.", True),  # Exclusive or with quantifier
        ("If a cat is not on the mat, then it is outside.", True),  # Conditional negation
        ("Whether a cat is on the mat or not, it is a pet.", True),  # Conditional with or without
        ("Whenever a cat is on the mat, a dog is in the yard.", True),  # Temporal conditional
        ("Wherever a cat is on the mat, a dog is in the yard.", True),  # Spatial conditional
        ("A cat is more agile than.", False),  # Incomplete comparative
        ("It is not the case that a cat.", False),  # Incomplete negation
        ("If a cat is more agile than a dog, then a fish is more agile than a bird.", False),  # Illogical comparative
        # Additional test cases for proper nouns and multi-word predicates
        ("If Plato is a philosopher, then Plato is wise.", True),  # Proper noun in condition and conclusion
        ("If the sky is blue, then the ocean is vast and deep.", True),  # Multi-word predicate
        ("If Mount Everest is a mountain, then Mount Everest is high.", True),  # Proper noun with common predicate
        ("If a book is interesting, then the book is a page-turner.", True),  # Multi-word predicate
        ("If Shakespeare wrote Hamlet, then Shakespeare is a playwright.", True),  # Proper noun in condition and conclusion
        ("If a car is electric, then the car is energy-efficient.", True),  # Multi-word predicate
        ("If Socrates is a man, then Socrates is mortal.", True),  # The recurring test case
        ("If a cat is on the mat, then the cat is comfortable.", True),  # Simple conditional statement
        ("If a dog barks, then the dog is not silent.", True),  # Negation in conclusion
        ("If a tree is tall, then the tree has many leaves.", True),  # Common predicate
        ("If a bird flies, then the bird is in the sky.", True),  # Simple conclusion
        ("If a flower is beautiful, then the flower is a rose.", False),  # Illogical conclusion
        ("If a fish swims, then the fish is a bird.", False),  # Illogical conclusion
        ("If a phone is ringing, then the phone is a banana.", False),  # Illogical conclusion
        ("If a computer is on, then the computer is a robot.", False),  # Illogical conclusion
    ]

    # Run test cases
    for statement, expected in test_cases:
        result = validate_logical_statement(statement)
        print(f"Testing statement: {statement} - Expected: {expected}, Got: {result}")
        assert result == expected, f"Test failed for statement: {statement}"

# Number of examples to generate
NUM_EXAMPLES_TO_GENERATE = 1000

# Generate the examples
generate_examples()

# To run tests, uncomment the line below and execute the script.
# This should be done in a development environment to verify changes.
test_validate_logical_statement()
