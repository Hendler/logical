# test_logic_parser.py
import unittest
from logical.engine import parse, repr_expr

class TestLogicParser(unittest.TestCase):

    def test_parse(self):
        test_cases = [
            ("A", "A"),
            ("A & B", "(A & B)"),
            ("A | B", "(A | B)"),
            ("~A", "~A"),
            ("A ^ B", "(A => B)"),
            ("A & B | C", "((A & B) | C)"),
            ("A | B & C", "(A | (B & C))"),
            ("A ^ B ^ C", "((A => B) => C)"),
            ("A ^ (B ^ C)", "(A => (B => C))"),
        ]

        for expr_str, expected_repr in test_cases:
            expr = parse(expr_str)
            self.assertEqual(repr_expr(expr), expected_repr)

    def test_evaluate(self):
        expr_str = "(A and B) => not (C or D)"
        expr = parse(expr_str)

        def evaluate_expr(expr, valuation):
            if isinstance(expr, str):
                return valuation[expr]
            elif isinstance(expr, tuple):
                op, left, right = expr
                if op == "&":
                    return evaluate_expr(left, valuation) and evaluate_expr(right, valuation)
                elif op == "|":
                    return evaluate_expr(left, valuation) or evaluate_expr(right, valuation)
                elif op == "=>":
                    return not evaluate_expr(left, valuation) or evaluate_expr(right, valuation)

        valuation = {"A": True, "B": False, "C": False, "D": False}
        result = evaluate_expr(expr, valuation)
        self.assertTrue(result)

        valuation = {"A": True, "B": True, "C": True, "D": False}
        result = evaluate_expr(expr, valuation)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
