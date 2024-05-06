import pytest
from logical import parse, evaluate  # Assuming 'parse' and 'evaluate' are the correct functions from the logical library

# Sample logical statements
logical_statements = [
    ("All men are mortal. Socrates is a man. Therefore, Socrates is mortal.", True),
    ("No birds are dogs. All dogs are animals. Therefore, no birds are animals.", False),
    ("Some mammals are carnivores. All lions are mammals. Therefore, some lions are carnivores.", True),
    ("Laird believes that the most valuable achievement of pure research is its role in expanding knowledge and providing new ideas, while Kim believes that saving lives through medical applications is the most valuable outcome of pure research.", True),
    ("If you eat your meat, then you can have some pudding.", True),
    ("If that animal is a dog, then it is a mammal.", True),
    ("Being unmarried is a necessary condition for being a bachelor.", True),
    ("Being a mammal is a necessary condition for being a dog.", True),
    ("If you spend all day in the sun, you’ll get sunburnt.", False),  # Considering the counterexample of using effective sunblock
    ("All living things deserve moral consideration.", True),
    # ... more logical statements will be added here to reach a total of 100
]

@pytest.mark.parametrize("statement, expected", logical_statements)
def test_logical_statement(statement, expected):
    assert parse_and_evaluate(statement) == expected, f"Statement failed: {statement}"

def parse_and_evaluate(statement):
    # This function will use the "logical" library's functionality to parse and evaluate the statement
    parsed_statement = parse(statement)
    return evaluate(parsed_statement)
