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
    "have six legs": "have_six_legs"
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
# Translate English statements into Prolog
def translate_to_prolog(statement, truth_value):
    prolog_statement = ""
    words = statement.split()
    parentheses_stack = []
    current_quantifier = ""
    current_entity = ""
    last_predicate_added = False
    implies_opened = False

    for i, word in enumerate(words):
        if word in quantifiers:
            current_quantifier = word
            last_predicate_added = False
        elif word in entities:
            current_entity = word
        elif word in predicates:
            prolog_predicate = predicates[word]
            last_predicate_added = True
            if current_quantifier == "All":
                prolog_statement += f"forall(X, (is_a(X, {current_entity}) -> {prolog_predicate}(X))). "
            elif current_quantifier == "No":
                prolog_statement += f"forall(X, (is_a(X, {current_entity}) -> ~{prolog_predicate}(X))). "
            elif current_quantifier == "Some":
                prolog_statement += f"exists(X, (is_a(X, {current_entity}) & {prolog_predicate}(X))). "
        elif word in connectives:
            if last_predicate_added:
                if word == "implies":
                    implies_opened = not implies_opened
                    if implies_opened:
                        prolog_statement += " :- "
                        parentheses_stack.append("(")
                    else:
                        prolog_statement = prolog_statement.rstrip(" ")  # Remove the space from the previous predicate
                        prolog_statement += "). "
                        parentheses_stack.pop()
                elif word == "and":
                    prolog_statement += ", "
                elif word == "or":
                    # Open parentheses before 'or' if not already open
                    if not parentheses_stack or parentheses_stack[-1] != "(":
                        prolog_statement += "("
                        parentheses_stack.append("(")
                    prolog_statement += "; "
                    # Close parentheses after 'or' if the next word is not a predicate
                    if i < len(words) - 1 and words[i + 1] not in predicates:
                        prolog_statement += "). "
                        parentheses_stack.pop()
                last_predicate_added = False
            else:
                # Skip connective if no predicate has been added
                continue

        # Close any open parentheses at the end of the statement
        while parentheses_stack:
            prolog_statement += "). "
            parentheses_stack.pop()

    # Error handling for empty Prolog representations
    if not prolog_statement.strip():
        return f"Translation Error: Could not translate the statement: {statement}"

    return prolog_statement.strip()

# Example usage
if __name__ == "__main__":
    num_statements_to_generate = 900
    new_statements = generate_statements(num_statements_to_generate)
    for statement, truth_value in new_statements:
        prolog_statement = translate_to_prolog(statement, truth_value)
        print(f"{statement} is {truth_value}, Prolog: {prolog_statement if prolog_statement else 'Translation Error'}")
