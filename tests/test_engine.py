# test_logic_parser.py
import unittest
from logical.engine import tokenize, parse, evaluate

class TestLogicParser(unittest.TestCase):
    def test_tokenize(self):
        expr_str = "(A & B) => ~(C | D)"
        tokens = tokenize(expr_str)
        expected_tokens = ["(", "A", "&", "B", ")", "=>", "~", "(", "C", "|", "D", ")"]
        self.assertEqual(tokens, expected_tokens)

    def test_parse(self):
        test_cases = [
            ("A", "A"),
            ("~A", "~A"),
            ("(A & B)", "(A & B)"),
            ("(A | B)", "(A | B)"),
            ("(A => B)", "(A => B)"),
            ("(A & (B | C))", "(A & (B | C))"),
            ("(A => (B | C))", "(A => (B | C))"),
            ("(A & B) => ~(C | D)", "(A & B) => ~(C | D)"),
            # ("((A => B) & (C => D)) => (A => D)", "((A => B) & (C => D)) => (A => D)"),
        ]

        for input_str, expected_repr in test_cases:
            tokens = tokenize(input_str)
            expr = parse(tokens)
            self.assertEqual(repr(expr), expected_repr)


    def test_evaluate(self):
        expr_str = "(A & B) => ~(C | D)"
        expr = parse(tokenize(expr_str))
        valuation = {"A": True, "B": False, "C": False, "D": False}
        result = evaluate(expr, valuation)
        self.assertTrue(result)

        valuation = {"A": True, "B": True, "C": True, "D": False}
        result = evaluate(expr, valuation)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
