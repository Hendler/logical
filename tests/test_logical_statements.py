import unittest
import subprocess

logical_statements = [
    # ... (previous logical statements) ...
    ("If a shape is a triacontatetragon, it has thirty-four sides. This shape has thirty-four sides. Therefore, this shape is a triacontatetragon.", True, "shape(triacontatetragon)."),
    ("All mammals are vertebrates. A whale is a mammal. Therefore, a whale is a vertebrate.", True, "vertebrate(whale)."),
    ("If an animal is a reptile, it lays eggs. A turtle is a reptile. Therefore, a turtle lays eggs.", True, "lays_eggs(turtle)."),
    ("Every multiple of one hundred and fifty-one is odd. Three hundred and two is a multiple of one hundred and fifty-one. Therefore, three hundred and two is odd.", False, "odd(302)."),
    ("If a shape is a square, it has four sides. This shape has four sides. Therefore, this shape is a square.", True, "shape(square)."),
    # ... (additional logical statements) ...
    # New logical statements
    ("All squares are rectangles but not all rectangles are squares. This shape is a square. Therefore, this shape is a rectangle.", True, "shape(rectangle)."),
    ("If an animal is a bird, it has wings. A penguin is a bird. Therefore, a penguin has wings.", True, "has_wings(penguin)."),
    ("Every prime number is odd except for two. Two is a prime number. Therefore, two is odd.", False, "odd(2)."),
    # Placeholder for additional logical statements to reach a total of 1000
]

class TestLogicalStatements(unittest.TestCase):

    def test_statement_1(self):
        english_statement, expected, prolog_statement = logical_statements[0]
        result = self.evaluate_prolog_statement(prolog_statement)
        self.assertEqual(result, expected, f"Statement failed: {english_statement}")

    def test_statement_2(self):
        english_statement, expected, prolog_statement = logical_statements[1]
        result = self.evaluate_prolog_statement(prolog_statement)
        self.assertEqual(result, expected, f"Statement failed: {english_statement}")

    def test_statement_3(self):
        english_statement, expected, prolog_statement = logical_statements[2]
        result = self.evaluate_prolog_statement(prolog_statement)
        self.assertEqual(result, expected, f"Statement failed: {english_statement}")

    def test_statement_4(self):
        english_statement, expected, prolog_statement = logical_statements[3]
        result = self.evaluate_prolog_statement(prolog_statement)
        self.assertEqual(result, expected, f"Statement failed: {english_statement}")

    def test_statement_5(self):
        english_statement, expected, prolog_statement = logical_statements[4]
        result = self.evaluate_prolog_statement(prolog_statement)
        self.assertEqual(result, expected, f"Statement failed: {english_statement}")

    # New test methods for the new logical statements
    def test_statement_6(self):
        english_statement, expected, prolog_statement = logical_statements[5]
        result = self.evaluate_prolog_statement(prolog_statement)
        self.assertEqual(result, expected, f"Statement failed: {english_statement}")

    def test_statement_7(self):
        english_statement, expected, prolog_statement = logical_statements[6]
        result = self.evaluate_prolog_statement(prolog_statement)
        self.assertEqual(result, expected, f"Statement failed: {english_statement}")

    def test_statement_8(self):
        english_statement, expected, prolog_statement = logical_statements[7]
        result = self.evaluate_prolog_statement(prolog_statement)
        self.assertEqual(result, expected, f"Statement failed: {english_statement}")


    # Placeholder for additional test methods to reach a total of 1000

    def evaluate_prolog_statement(self, prolog_statement):
        """
        Evaluate the given Prolog statement using a Prolog interpreter.
        Returns True if the statement is logically valid, False otherwise.
        """
        command = ['swipl', '-s', 'logical_statements.pl', '-g', prolog_statement, '-t', 'halt']
        print(f"Running Prolog command: {command}")
        try:
            # Call the Prolog interpreter using subprocess
            result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=20)
            # Parse the output from Prolog interpreter
            output_lines = result.stdout.strip().split('\n')
            error_output = result.stderr.strip()
            print(f"Prolog interpreter standard output: {output_lines}")
            print(f"Prolog interpreter error output: {error_output}")
            # Check the last line of output for 'true.' or 'false.'
            if not output_lines[-1] or output_lines[-1].endswith('true.'):
                return True
            elif output_lines[-1].endswith('false.') or "ERROR:" in error_output:
                return False
            else:
                # If the last line is not 'true.' or 'false.', log the output for further investigation
                print(f"Unexpected Prolog interpreter output: {output_lines}")
                return False
        except subprocess.CalledProcessError as e:
            # Log the error for debugging purposes
            print(f"Prolog evaluation failed: {e}")
            print(f"Prolog command error output: {e.stderr.strip()}")
            return False
        except subprocess.TimeoutExpired as e:
            # Log timeout error
            print(f"Prolog command timed out: {e}")
            print(f"Prolog command standard output: {e.stdout.strip()}")
            print(f"Prolog command error output: {e.stderr.strip()}")
            return False
