import ast
import re
from collections import deque



def repr_expr(expr):
    return expr

class LogicalExpression(ast.NodeTransformer):
    def __init__(self, expr_str):
        self.expr = ast.parse(expr_str, mode='eval').body

OP_MAP = {
    ast.BitAnd: "&",
    ast.BitOr: "|",
    ast.BitXor: "=>",
}


class CustomTransformer(ast.NodeTransformer):
    def visit_BoolOp(self, node):
        if len(node.values) == 1:
            return self.visit(node.values[0])

        left = self.visit(node.values[0])
        right = self.visit(node.values[1])

        for i in range(2, len(node.values)):
            right = f"({right} {OP_MAP[type(node.op)]} {self.visit(node.values[i])})"

        return f"({left} {OP_MAP[type(node.op)]} {right})"

    def visit_UnaryOp(self, node):
        return f"~{self.visit(node.operand)}"

    def visit_Name(self, node):
        return node.id

    def visit_Expr(self, node):
        return self.visit(node.value)


    def visit_BitAnd(self, node):
        return "&"

    def visit_BitOr(self, node):
        return "|"

    def visit_BitXor(self, node):
        return "=>"

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = self.visit(node.op)

        return f"({left} {op} {right})"




def parse(expr_str):
    expr = LogicalExpression(expr_str)
    return CustomTransformer().visit(expr.expr)



