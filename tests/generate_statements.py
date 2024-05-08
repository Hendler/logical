import random

# Define logical constructs
quantifiers = ["All", "Some", "No"]
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

    while i < len(words):
        if words[i] in quantifiers:
            if last_predicate_added:
                # Close the previous predicate scope
                prolog_statement += ")" if implies_nesting > 0 else ""
                last_predicate_added = False
            current_quantifier = words[i]
            i += 1
        elif words[i] in entities:
            current_entity = words[i]
            i += 1
        else:
            # Check for multi-word predicates
            for j in range(i, len(words)):
                potential_predicate = ' '.join(words[i:j+1])
                if potential_predicate in predicates:
                    prolog_predicate = predicates[potential_predicate]
                    # Check if the next word is within bounds and is a connective
                    if j+1 < len(words) and words[j+1] in connectives:
                        # Continue processing additional predicates after "and" or "or"
                        prolog_statement += " & " if words[j+1] == "and" else " | "
                        i = j + 2  # Skip the connective for the next iteration
                    else:
                        last_predicate_added = True
                        # Construct the Prolog statement based on the quantifier and truth value
                        prolog_statement += construct_prolog_statement(current_quantifier, current_entity, prolog_predicate, truth_value)
                        i = j + 1
                    break
                elif j+1 < len(words) and words[j+1] in quantifiers:
                    # If the next word is a quantifier, we need to close the current scope and start a new one
                    prolog_statement += ")" if implies_nesting > 0 else ""
                    last_predicate_added = False
                    break
            else:
                # If no predicates are found, check for connectives
                if words[i] in connectives:
                    if last_predicate_added:
                        # Handle the connectives appropriately
                        connective_str, new_implies_nesting = handle_connectives(words[i], implies_nesting)
                        prolog_statement += connective_str
                        implies_nesting = new_implies_nesting
                        last_predicate_added = False
                    i += 1
                else:
                    error_detail = f"Failed to translate part of the statement: {' '.join(words[i:])}"
                    # Provide more specific details about the nature of the translation error
                    if not last_predicate_added:
                        error_detail += f" - Expected a predicate or connective but found '{words[i]}'."
                    return f"Translation Error: Could not translate the statement: {statement}. {error_detail}"

    # Close any open parentheses at the end of the statement
    prolog_statement += ")" * implies_nesting

    if prolog_statement:
        prolog_statement = prolog_statement.strip() + "."

    return prolog_statement

def construct_prolog_statement(quantifier, entity, predicate, truth_value):
    """
    Construct a Prolog statement based on the quantifier, entity, predicate, and truth value.
    """
    if quantifier == "All":
        if truth_value:
            return f"forall(X, (is_a(X, {entity}) -> {predicate}(X)))"
        else:
            return f"forall(X, (is_a(X, {entity}) & ~{predicate}(X)))"
    elif quantifier == "No":
        if truth_value:
            return f"forall(X, (is_a(X, {entity}) & ~{predicate}(X)))"
        else:
            return f"forall(X, (is_a(X, {entity}) -> {predicate}(X)))"
    elif quantifier == "Some":
        if truth_value:
            return f"exists(X, (is_a(X, {entity}) & {predicate}(X)))"
        else:
            return f"exists(X, (is_a(X, {entity}) & ~{predicate}(X)))"
    else:
        raise ValueError(f"Unknown quantifier: {quantifier}")

def handle_connectives(connective, implies_nesting):
    """
    Handle the translation of logical connectives into Prolog syntax.
    """
    if connective == "implies":
        # Increment implies_nesting for a new implication
        implies_nesting += 1
        # Add parentheses for the entire implication if it's the first level
        return (" :- ", implies_nesting)
    elif connective == "and":
        # Use ',' for 'and' connective, no change in implies_nesting
        return (", ", implies_nesting)
    elif connective == "or":
        # Use ';' for 'or' connective, no change in implies_nesting
        return ("; ", implies_nesting)
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
        ("No students are vehicles implies no students have wheels", True)
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
