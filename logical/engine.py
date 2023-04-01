import ast
import re
from collections import deque


# class LogicalExpression:

#     def __init__(self, expr_str):
#         self.expr_str = expr_str
#         self.expr = self.parse(expr_str)

#     def parse(self, expr_str):
#         return ast.parse(expr_str, mode='eval').body

#     def __repr__(self):
#         return self.expr_str

# class And(ast.BinOp):
#     def __repr__(self):
#         return f"({repr(self.left)} & {repr(self.right)})"

# class Or(ast.BinOp):
#     def __repr__(self):
#         return f"({repr(self.left)} | {repr(self.right)})"

# class Implies(ast.BinOp):
#     def __repr__(self):
#         return f"({repr(self.left)} => {repr(self.right)})"

# class Not(ast.UnaryOp):
#     def __repr__(self):
#         return f"~{repr(self.operand)}"

# class Symbol(ast.Name):
#     def __repr__(self):
#         return self.id

def repr_expr(expr):
    return repr(expr)

class LogicalExpression(ast.NodeTransformer):
    def __init__(self, expr_str):
        self.expr = ast.parse(expr_str, mode='eval').body

class CustomTransformer(ast.NodeTransformer):
    def visit_BoolOp(self, node):
        self.generic_visit(node)
        return f"({repr(node.values[0])} {repr(node.op)} {repr(node.values[1])})"

    def visit_And(self, node):
        return "&"

    def visit_Or(self, node):
        return "|"

    def visit_Not(self, node):
        return "~"

    def visit_Name(self, node):
        return node.id

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        return f"({repr(node.op)} {repr(node.operand)})"

    def visit_Eq(self, node):
        return "=="

    def visit_NotEq(self, node):
        return "!="

def parse(expr_str):
    expr = LogicalExpression(expr_str)
    return CustomTransformer().visit(expr.expr)



