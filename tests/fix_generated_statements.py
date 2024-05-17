import csv
from datetime import datetime

# Define the path to the input file
input_file_path = '/home/ubuntu/logical/tests/generated_statements.txt'
# Define the path to the output file, including a timestamp to make it unique
output_file_path = f'/home/ubuntu/logical/tests/fixed_statements_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'

# Define a function to fix the Prolog translation errors
def fix_prolog_translation(statement):
    # This function will contain the logic to fix the Prolog translation
    # For demonstration purposes, let's assume we replace 'have' with 'possess' and 'and' with 'also'
    # This is a simplified example and does not represent the actual complexity of Prolog translation
    # The actual logic will involve parsing the English statements, understanding the logical constructs,
    # and then generating the corresponding Prolog statements.

    # Simplified logic to handle specific translation errors identified in the statements
    # This is a basic example and should be expanded to cover all logical constructs and their Prolog syntax
    fixed_statement = statement
    if 'have wheels' in statement:
        fixed_statement = fixed_statement.replace('have wheels', 'wheels(Subject)')
    if 'have six legs' in statement:
        fixed_statement = fixed_statement.replace('have six legs', 'six_legs(Subject)')
    if 'bipedal' in statement:
        fixed_statement = fixed_statement.replace('bipedal', 'bipedal(Subject)')
    if 'can fly' in statement:
        fixed_statement = fixed_statement.replace('can fly', 'can_fly(Subject)')

    # Replace 'All' with 'forall' to reflect universal quantification in Prolog
    fixed_statement = fixed_statement.replace('All', 'forall')

    # Add more translation rules as needed here

    return fixed_statement

# Open the input file and create the output file
with open(input_file_path, 'r') as infile, open(output_file_path, 'w', newline='') as outfile:
    # Create a CSV reader and writer
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    # Write the header to the output file
    writer.writerow(['English Statement', 'Prolog Statement', 'Truth Value'])

    # Iterate over each line in the input file
    for row in reader:
        # Split the line into the English statement and the rest
        english_statement, rest = row[0].split(', Prolog: ')
        # Extract the truth value from the rest of the line
        truth_value = 'True' if 'is True' in rest else 'False'
        # Fix the Prolog translation
        prolog_statement = fix_prolog_translation(english_statement)
        # Write the fixed statement and the truth value to the output file
        writer.writerow([english_statement, prolog_statement, truth_value])

print(f"Fixed statements have been written to {output_file_path}")
