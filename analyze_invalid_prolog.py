import re
import datetime

def process_file(file_path):
    print('Processing file...')
    invalid_statements = {}
    with open(file_path, 'r') as file:
        for line in file:
            match = re.search(r'Invalid Prolog statement found: (.+)', line)
            if match:
                statement = match.group(1)
                # Count occurrences of invalid statements
                if statement in invalid_statements:
                    invalid_statements[statement] += 1
                else:
                    invalid_statements[statement] = 1
    return invalid_statements

def summarize_errors(file_path):
    error_summary = {}
    with open(file_path, 'r') as file:
        for line in file:
            # Look for common error patterns and summarize them
            if ':-' in line:
                error_summary['Implication Error'] = error_summary.get('Implication Error', 0) + 1
            if 'if' in line:
                error_summary['Conditional Error'] = error_summary.get('Conditional Error', 0) + 1
            if 'No' in line or 'All' in line or 'Some' in line or 'Most' in line or 'Few' in line:
                error_summary['Quantifier Error'] = error_summary.get('Quantifier Error', 0) + 1
            if re.search(r'\w+\s:-\s\w+', line):
                error_summary['Predicate Error'] = error_summary.get('Predicate Error', 0) + 1
            if re.search(r'\w+\s:-\s\+\w+', line):
                error_summary['Negation Error'] = error_summary.get('Negation Error', 0) + 1
            if re.search(r'\w+\s:-\s\w+\s:-\s\w+', line):
                error_summary['Chained Predicate Error'] = error_summary.get('Chained Predicate Error', 0) + 1
    return error_summary

# Generate a dynamic output file path based on the current timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
output_file_path = f'/home/ubuntu/full_outputs/analyze_invalid_prolog_{timestamp}.txt'

# Process the file and print a summary of invalid statements
invalid_summary = process_file(output_file_path)
for statement, count in invalid_summary.items():
    print(f'{statement}: {count}')

# Summarize and print common error patterns
error_patterns_summary = summarize_errors(output_file_path)
for error, count in error_patterns_summary.items():
    print(f'{error}: {count}')
