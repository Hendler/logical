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
    if isinstance(expr, str):
        return expr
    elif isinstance(expr, tuple):
        return f"({repr_expr(expr[1])} {expr[0]} {repr_expr(expr[2])})"

class LogicalExpression(ast.NodeTransformer):
    def __init__(self, expr_str):
        self.expr = ast.parse(expr_str, mode='eval').body

OP_MAP = {
    ast.And: "&",
    ast.Or: "|",
    ast.BitXor: "=>",
}

class CustomTransformer(ast.NodeTransformer):
    def visit_BoolOp(self, node):
        if len(node.values) == 1:
            return self.visit(node.values[0])
        return f"({self.visit(node.values[0])} {OP_MAP[type(node.op)]} {self.visit(node.values[1])})"

    def visit_UnaryOp(self, node):
        return f"~{self.visit(node.operand)}"

    def visit_Name(self, node):
        return node.id

    def visit_Expr(self, node):
        return self.visit(node.value)



# class CustomTransformer(ast.NodeTransformer):
#     def visit_BoolOp(self, node):
#         self.generic_visit(node)
#         return f"({repr(node.values[0])} {repr(node.op)} {repr(node.values[1])})"

    def visit_And(self, node):
        return "&"

    def visit_Or(self, node):
        return "|"

    def visit_Not(self, node):
        return "~"

    # def visit_Name(self, node):
    #     return node.id  # Return the variable name without quotes

    # def visit_UnaryOp(self, node):
    #     self.generic_visit(node)
    #     return f"({repr(node.op)} {repr(node.operand)})"

    def visit_Eq(self, node):
        return "=="

    def visit_NotEq(self, node):
        return "!="

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = type(node.op)

        if op in OP_MAP:
            return OP_MAP[op], left, right
        return None


def parse(expr_str):
    expr = LogicalExpression(expr_str)
    return CustomTransformer().visit(expr.expr)



