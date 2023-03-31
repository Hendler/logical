class Variable:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

class Not:
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"~{self.expr}"

class And:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left} & {self.right})"

class Or:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left} | {self.right})"

class Implies:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left} => {self.right})"


def tokenize(expr_str):
    expr_str = expr_str.replace("(", " ( ").replace(")", " ) ")
    return expr_str.split()

def parse(tokens):
    def parse_expression(index):
        if tokens[index] == "(":
            left, index = parse_expression(index + 1)
            op = tokens[index]
            right, index = parse_expression(index + 1)
            index += 1  # Skip ")"
            if op == "&":
                return And(left, right), index
            elif op == "|":
                return Or(left, right), index
            elif op == "=>":
                return Implies(left, right), index
        elif tokens[index] == "~":
            expr, index = parse_expression(index + 1)
            return Not(expr), index
        else:
            return Variable(tokens[index]), index + 1

    expr, _ = parse_expression(0)
    return expr

def evaluate(expr, valuation):
    if isinstance(expr, Variable):
        return valuation[expr.name]
    elif isinstance(expr, And):
        return evaluate(expr.left, valuation) and evaluate(expr.right, valuation)
    elif isinstance(expr, Or):
        return evaluate(expr.left, valuation) or evaluate(expr.right, valuation)
    elif isinstance(expr, Implies):
        return not evaluate(expr.left, valuation) or evaluate(expr.right, valuation)
    elif isinstance(expr, Not):
        return not evaluate(expr.expr, valuation)