import sys
from invoke import run

def main():
    # Check for command-line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'ask':
            # Invoke the parse task if 'ask' is provided as an argument
            # Pass the English statement as an argument to the parse function
            english_statement = ' '.join(sys.argv[2:])
            run(f"invoke parse --input-text \"{english_statement}\"")
        elif command == 'run-logic':
            # Invoke the run_logic_task if 'run-logic' is provided as an argument
            run("invoke run-logic")
        else:
            print(f"Unknown command: {command}")
            print("Available commands: 'ask', 'run-logic'")
    else:
        print("No command provided.")
        print("Usage: python -m logical [command]")
        print("Available commands: 'ask', 'run-logic'")

if __name__ == "__main__":
    main()
