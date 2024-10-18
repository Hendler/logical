def strip_comments(code):
    stripped_code = ""
    stack = []
    i = 0
    while i < len(code):
        if code[i:i+2] == '/*':
            stack.append('/*')
            i += 2
            continue  # Skip appending characters and move to the next iteration
        elif code[i:i+2] == '*/' and stack:
            stack.pop()
            i += 2
            continue  # Skip appending characters and move to the next iteration
        elif not stack and code[i] == '%':
            # Skip the rest of the line after a single-line comment
            i = code.find('\n', i)
            if i == -1:  # If no newline is found, we are at the end of the code
                break
        elif not stack:
            stripped_code += code[i]
        i += 1
    return stripped_code

# Test cases for the strip_comments function
test_cases = {
    "Nested comments": "/* Comment /* nested comment */ end comment */",
    "Single line comment": "valid_fact(parent(john, doe)). % Single line comment",
    "Block comment": "valid_rule(sibling(X, Y) :- parent(Z, X), parent(Z, Y)). /* Block comment */",
    "Unbalanced nested comment": "/* Unbalanced /* nested */ comment",
    "Comment with % symbol": "/* Comment with % symbol */",
    "Multiple nested comments": "/* First level /* Second level /* Third level */ Second level end */ First level end */"
}

# Run strip_comments function on each test case and print the results
for description, code in test_cases.items():
    stripped = strip_comments(code)
    print(f"Original: {code}")
    print(f"Stripped: {stripped}\n")
