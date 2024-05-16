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

# Dictionary mapping predicates to logically coherent conclusions
logically_coherent_predicates = {
    "man": {
        "mortal": True,
        "rational": True,
        "philosopher": True,
    },
    "bird": {
        "can_fly": True,
        "has_feathers": True,
        "lays_eggs": True,
        "mortal": True,  # Added "mortal" as a valid predicate for "bird"
    },
    "cat": {
        "is_a_pet": True,
        "has_claws": True,
        "chases_mice": True,
        "mortal": True,  # Added "mortal" as a valid predicate for "cat"
    },
    "dog": {
        "barks": True,
        "is_loyal": True,
        "can_be_trained": True,
        "mortal": True,  # Assuming dogs are also mortal
    },
    "car": {
        "has_wheels": True,
        "requires_fuel": True,
        "can_transport_people": True,
    },
    "tree": {
        "has_leaves": True,
        "grows": True,
        "produces_oxygen": True,
        "mortal": True,  # Assuming trees are also mortal (in the sense that they can die)
    },
    # ... (additional mappings can be added here)
    "electron": {
        "charged": False,  # Electrons are not charged in the context of this logical validation
    },
}

# Dictionary mapping proper nouns to their common noun equivalents for logical coherence checks
proper_noun_mappings = {
    "socrates": "man",
    # ... (additional mappings can be added here)
}

def validate_logical_statement(statement):
    # Check for universally or existentially quantified statements
    quantified_statement_match = re.match(r'^(All|No|Some|Most|Few)\s+([A-Za-z]+)s?\s+(is|are)\s+([a-z]+)\.', statement.strip(), re.IGNORECASE)
    if quantified_statement_match:
        quantifier, subject, verb, predicate = quantified_statement_match.groups()
        subject_key = subject.lower()
        normalized_predicate = predicate.lower()
        subject_key = proper_noun_mappings.get(subject_key, subject_key)
        coherent_conclusions = logically_coherent_predicates.get(subject_key, {})
        if quantifier == "All":
            return subject_key in logically_coherent_predicates and coherent_conclusions.get(normalized_predicate, False)
        elif quantifier in ["Most", "Few"]:
            return coherent_conclusions.get(normalized_predicate, False)
        elif quantifier == "Some":
            return True
        elif quantifier == "No":
            return coherent_conclusions.get(normalized_predicate) == False

    # Enhanced validation to check if the statement contains necessary components
    # and follows a logical structure.
    valid_quantifiers = {"All", "No", "Some", "Most", "Few", "Every", "Any"}
    has_quantifier = any(quantifier + " " in statement for quantifier in valid_quantifiers)
    has_subject_predicate = re.search(r'\b(is|are)\b', statement) is not None
    ends_with_period = statement.endswith(".")
    starts_with_conditional = re.match(r'If\s+([A-Za-z][a-z]*(?:\s+[A-Za-z][a-z]*)*)\s+(is|are)\s+([a-z]+),\s+then\s+([A-Za-z][a-z]*(?:\s+[A-Za-z][a-z]*)*)\s+(is|are)\s+([a-z]+)\s*\.', statement.strip(), re.IGNORECASE) is not None
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

    # Check for semantic inconsistencies which are inherently false
    semantic_inconsistencies = {
        "bachelors": ["married"],
        "dry": ["water"],
        "square": ["circle"]
    }
    for subject, invalid_predicates in semantic_inconsistencies.items():
        if subject in statement and any(invalid_predicate in statement for invalid_predicate in invalid_predicates):
            return False

    # Regular expression pattern for conditional statements
    conditional_pattern = r'If\s+([A-Za-z][a-z]*(?:\s+[A-Za-z][a-z]*)*)\s+(is|are)\s+([a-z]+),\s+then\s+([A-Za-z][a-z]*(?:\s+[A-Za-z][a-z]*)*)\s+(is|are)\s+([a-z]+)\s*\.'
    conditional_match = re.match(conditional_pattern, statement.strip(), re.IGNORECASE)
    if conditional_match:
        subject1, verb1, predicate1, subject2, verb2, predicate2 = conditional_match.groups()
        subject1_key = proper_noun_mappings.get(subject1.lower(), subject1.lower())
        subject2_key = proper_noun_mappings.get(subject2.lower(), subject2.lower())
        if subject1_key != subject2_key:
            return False  # The subjects must be the same for the statement to be coherent
        coherent_conclusions = logically_coherent_predicates.get(subject1_key, {})
        if coherent_conclusions.get(predicate1.lower()) == True:
            return coherent_conclusions.get(predicate2.lower(), False)
        return False

    # Recognize assumption-based "Assuming..." constructs
    if starts_with_assumption:
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
    match = re.match(r'If\s+(.+?)\s+then\s+(.+)\s*$', condition, re.IGNORECASE)
    if match:
        condition_part, conclusion_part = match.groups()
        # Validate both the condition and conclusion parts as individual statements
        valid_condition = validate_statement_part(condition_part.strip().rstrip('.'))
        valid_conclusion = validate_statement_part(conclusion_part.strip().rstrip('.'))
        # Return True only if both condition and conclusion parts are valid
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

    # Handle cases where the predicate is a proper noun or a multi-word phrase
    proper_noun_or_phrase = re.match(r'^([A-Z][a-z]+(?: [A-Z][a-z]+)*) (is|are) ([A-Z][a-z]+(?: [A-Z][a-z]+)*)\.$', part)
    if proper_noun_or_phrase:
        subject, verb, predicate = proper_noun_or_phrase.groups()
        return True

    return False

subjects = ["cat", "dog", "bird", "car", "tree", "Socrates"]
predicates = ["mortal", "fast", "tall", "short", "round", "man"]
logical_connectives = ["and", "or", "if", "then", "not"]

# Function to generate logical examples and their Prolog representations
def generate_examples():
    generated_statements = set()  # Set to keep track of generated statements to avoid duplicates
    while len(generated_statements) < NUM_EXAMPLES_TO_GENERATE:
        try:
            # Generate a logical English statement
            english_statement = generate_logical_statement(len(generated_statements))
            # Validate the logical consistency of the statement
            if validate_logical_statement(english_statement):
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

# Define the number of examples to generate
NUM_EXAMPLES_TO_GENERATE = 1000

# Call the function to generate examples
generate_examples()
