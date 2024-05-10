import random

# Define logical constructs
quantifiers = ["all", "some", "no"]
entities = ["men", "birds", "mammals", "students", "vehicles", "insects"]
predicates = {
    "are mortal": "mortal",
    "can fly": "can_fly",
    "have fur": "have_fur",
    "are bipedal": "bipedal",
    "have wheels": "have_wheels",
    "have six legs": "have_six_legs",
    "have wings": "have_wings"  # Added missing predicate
}
connectives = ["and", "or", "implies"]
truth_values = [True, False]

# Generate logical statements
def generate_statements(num_statements):
    statements = []
    for _ in range(num_statements):
        quantifier = random.choice(quantifiers)
        entity = random.choice(entities)
        predicate = random.choice(list(predicates.keys()))
        connective = random.choice(connectives)
        truth_value = random.choice(truth_values)

        # Construct the statement
        if connective == "implies":
            statement = f"If {entity} {predicate}, then it is also true that {entity} {random.choice(list(predicates.keys()))}"
        else:
            # Generate a more complex statement with multiple predicates and connectives
            second_predicate = random.choice(list(predicates.keys()))
            if predicate != second_predicate:
                statement = f"{quantifier} {entity} {predicate} {connective} {entity} {second_predicate}"
            else:
                # Ensure the second predicate is different from the first
                second_predicate = random.choice(list(set(predicates.keys()) - {predicate}))
                statement = f"{quantifier} {entity} {predicate} {connective} {entity} {second_predicate}"

        # Append the statement and its truth value to the list
        statements.append((statement, truth_value))

    return statements

# Translate English statements into Prolog
def translate_to_prolog(statement, truth_value):
    prolog_statement = ""
    words = statement.split()
    current_quantifier = ""
    current_entity = ""
    last_predicate_added = False
    implies_nesting = 0  # Track the depth of nested implications
    i = 0
    error_detail = ""  # Initialize the error detail variable

    # Handle statements beginning with "If" as implications
    if words[0].lower() == "if":
        prolog_statement += ":- ("
        implies_nesting += 1
        words = words[1:]  # Remove "If" from the processing list

    while i < len(words):
        word = words[i].lower()
        # Debug print
        print(f"Current word: {word}, Current quantifier: {current_quantifier}, Current entity: {current_entity}, Last predicate added: {last_predicate_added}")
        if word in quantifiers and not current_quantifier:
            current_quantifier = word
            i += 1
            continue
        elif word in entities and not current_entity:
            current_entity = word
            i += 1
            continue
        # Check for multi-word predicates first
        potential_predicate = word
        for j in range(i+1, len(words)):
            next_word = words[j].lower()
            next_potential = f"{potential_predicate} {next_word}"
            if next_potential in predicates:
                potential_predicate = next_potential
                i = j  # Move index to the last word of the multi-word predicate
            else:
                break  # No longer a valid multi-word predicate
        if potential_predicate in predicates:
            prolog_predicate = predicates[potential_predicate]
            prolog_statement += construct_prolog_statement(current_quantifier, current_entity, prolog_predicate, truth_value)
            last_predicate_added = True
            i += 1  # Move past the predicate
            continue
        # If no multi-word predicate, check for single-word predicates
        if word in predicates and not last_predicate_added:
            prolog_predicate = predicates[word]
            prolog_statement += construct_prolog_statement(current_quantifier, current_entity, prolog_predicate, truth_value)
            last_predicate_added = True
            i += 1
            continue
        # Check for connectives
        if word in connectives:
            connective_str, new_implies_nesting = handle_connectives(word, implies_nesting)
            prolog_statement += connective_str
            implies_nesting = new_implies_nesting
            last_predicate_added = False
            # Look ahead to determine if the next word is an entity
            if i + 1 < len(words) and words[i + 1].lower() in entities:
                # If the next word is an entity, check if it's the same as the current entity
                if words[i + 1].lower() == current_entity:
                    # Continue with the same quantifier and entity
                    i += 2
                    continue
                else:
                    # Reset quantifier and entity for the next clause after a connective
                    current_quantifier = ""
                    current_entity = ""
            i += 1
            continue
        # If no valid predicate or connective is found, and we have a quantifier and entity, attempt to find a predicate
        if not last_predicate_added and current_quantifier and current_entity:
            # Look ahead to find a potential predicate
            found_predicate = False
            for j in range(i, len(words)):
                next_word = words[j].lower()
                next_potential = f"{potential_predicate} {next_word}"
                if next_potential in predicates:
                    potential_predicate = next_potential
                    found_predicate = True
                    i = j  # Adjust index to the last word of the multi-word predicate
                    break
            if found_predicate:
                prolog_predicate = predicates[potential_predicate]
                prolog_statement += construct_prolog_statement(current_quantifier, current_entity, prolog_predicate, truth_value)
                last_predicate_added = True
                i += 1  # Move past the predicate
                continue
            else:
                # If no predicate is found after a quantifier and entity, return an error
                error_detail = f"Failed to translate part of the statement at word index {i}: {' '.join(words[i:])}"
                expected_element = "predicate"
                found_element = "quantifier" if word in quantifiers else "unknown element"
                error_detail += f" - Expected a {expected_element} but found '{found_element}' at word index {i}."
                if i > 0:
                    error_detail += f" Previous element was '{words[i-1]}' at word index {i-1}."
                return f"Translation Error: Could not translate the statement: {statement}. {error_detail}"
        i += 1

    # Close any open parentheses at the end of the statement
    prolog_statement += ")" * implies_nesting if implies_nesting > 0 else ""
    if prolog_statement:
        prolog_statement = prolog_statement.strip() + "."

    return prolog_statement

def construct_prolog_statement(quantifier, entity, predicate, truth_value):
    """
    Construct a Prolog statement based on the quantifier, entity, predicate, and truth value.
    """
    if quantifier == "all":
        if truth_value:
            return f"forall(X, (is_a(X, {entity}) -> {predicate}(X)))"
        else:
            return f"forall(X, (is_a(X, {entity}) & ~{predicate}(X)))"
    elif quantifier == "no":
        if truth_value:
            return f"forall(X, (is_a(X, {entity}) & ~{predicate}(X)))"
        else:
            return f"forall(X, (is_a(X, {entity}) -> {predicate}(X)))"
    elif quantifier == "some":
        if truth_value:
            return f"exists(X, (is_a(X, {entity}) & {predicate}(X)))"
        else:
            return f"exists(X, (is_a(X, {entity}) & ~{predicate}(X)))"
    else:
        raise ValueError(f"Unknown quantifier: {quantifier}")

def handle_connectives(connective, implies_nesting):
    """
    Handle the translation of logical connectives into Prolog syntax.
    Adjust the implies_nesting counter and manage parentheses for nested implications.
    """
    if connective == "implies":
        # Increment implies_nesting for a new implication
        implies_nesting += 1
        # Add parentheses for the entire implication if it's the first level
        return (" :- (", implies_nesting) if implies_nesting == 1 else (" -> (", implies_nesting)
    elif connective == "and":
        # Use ',' for 'and' connective, no change in implies_nesting
        return (", ", implies_nesting)
    elif connective == "or":
        # Use ';' for 'or' connective, no change in implies_nesting
        return ("; ", implies_nesting)
    elif connective == "end_implies":
        # Decrement implies_nesting when closing an implication scope
        implies_nesting -= 1
        # Add closing parenthesis for the implication
        return (")" * (implies_nesting + 1), max(implies_nesting, 0)) if implies_nesting >= 0 else ("", 0)
    else:
        raise ValueError(f"Unknown connective: {connective}")

# Test cases for the translate_to_prolog function
def test_translate_to_prolog():
    test_cases = [
        ("All men are mortal", True),
        ("Some birds can fly", True),
        ("No vehicles have wings", True),
        ("All mammals have fur and all mammals are bipedal", False),
        ("Some insects have six legs or some insects can fly", True),
        ("No students are vehicles implies no students have wheels", True),
        # New test cases
        ("All birds can fly and some birds are colorful", True),
        ("No mammals have wings or some mammals can swim", True),
        ("Some vehicles have wheels and all vehicles can move", True),
        ("All insects have six legs implies some insects are ants", True),
        ("No students are professors or all students are learners", True),
        ("Some birds are bipedal and no birds are quadrupedal", True),
    ]

    for statement, truth_value in test_cases:
        prolog_statement = translate_to_prolog(statement, truth_value)
        print(f"Testing: {statement} is {truth_value}, Prolog: {prolog_statement if prolog_statement else 'Translation Error'}")

# Example usage
if __name__ == "__main__":
    num_statements_to_generate = 900
    new_statements = generate_statements(num_statements_to_generate)
    for statement, truth_value in new_statements:
        prolog_statement = translate_to_prolog(statement, truth_value)
        print(f"{statement} is {truth_value}, Prolog: {prolog_statement if prolog_statement else 'Translation Error'}")

# Moved the test function call to after the translate_to_prolog function definition
test_translate_to_prolog()
