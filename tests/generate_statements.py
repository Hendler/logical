import random

# Define logical constructs
quantifiers = ["All", "Some", "No"]
entities = ["men", "birds", "mammals", "students", "vehicles", "insects"]
predicates = ["are mortal", "can fly", "have fur", "are bipedal", "have wheels", "have six legs"]
connectives = ["and", "or", "implies"]
truth_values = [True, False]

# Generate logical statements
def generate_statements(num_statements):
    statements = []
    for _ in range(num_statements):
        quantifier = random.choice(quantifiers)
        entity = random.choice(entities)
        predicate = random.choice(predicates)
        connective = random.choice(connectives)
        truth_value = random.choice(truth_values)

        # Construct the statement
        if connective == "implies":
            statement = f"If {entity} {predicate}, then it is also true that {entity} {random.choice(predicates)}"
        else:
            statement = f"{quantifier} {entity} {predicate} {connective} {entity} {random.choice(predicates)}"

        # Append the statement and its truth value to the list
        statements.append((statement, truth_value))

    return statements

# Translate English statements into Prolog
def translate_to_prolog(statement):
    # This function will parse the English statement and convert it into a Prolog representation
    # For simplicity, we will handle only a subset of possible statements
    prolog_statement = ""
    words = statement.split()
    if "All" in statement:
        subject = words[1]
        predicate = " ".join(words[2:])
        prolog_statement = f"forall(X, (is_a(X, {subject}) -> {predicate.replace(' ', '_')}(X)))."
    elif "Some" in statement:
        subject = words[1]
        predicate = " ".join(words[2:])
        prolog_statement = f"exists(X, (is_a(X, {subject}) & {predicate.replace(' ', '_')}(X)))."
    elif "No" in statement:
        subject = words[1]
        predicate = " ".join(words[2:])
        prolog_statement = f"forall(X, (is_a(X, {subject}) -> ~{predicate.replace(' ', '_')}(X)))."
    elif "implies" in statement:
        antecedent = " ".join(words[1:words.index("implies")])
        consequent = " ".join(words[words.index("implies")+1:])
        prolog_statement = f"implies({antecedent.replace(' ', '_')}, {consequent.replace(' ', '_')})."
    # Return the Prolog representation of the statement
    return prolog_statement

# Example usage
if __name__ == "__main__":
    num_statements_to_generate = 900
    new_statements = generate_statements(num_statements_to_generate)
    for statement, truth_value in new_statements:
        prolog_statement = translate_to_prolog(statement)
        print(f"{statement} is {truth_value}, Prolog: {prolog_statement}")
