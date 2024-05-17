import os

from logical import parse_logic

# This script will use the parse_logic function to generate Prolog from a given English statement.

# The English statement to be converted into Prolog.
english_statement = "Some trees are fast."

# Debug: Print the OpenAI API key to verify it's being read correctly.
print(f"Debug: OPENAI_API_KEY from environment: {os.getenv('OPENAI_API_KEY')}")

# Call the parse_logic function and print the result.
prolog_statement = parse_logic(english_statement)
print(f"Generated Prolog statement: {prolog_statement}")
