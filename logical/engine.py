from itertools import tee, islice

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
    def peek(iterable):
        a, b = tee(iterable)
        head = next(b, None)
        return head

    tokens = iter(tokens)  # Convert the list to an iterator

    def primary():
        token = next(tokens)
        if token == "(":
            expr = implication()
            next(tokens)  # Consume closing parenthesis ")"
            return expr
        elif token == "~":
            return Not(primary())
        else:
            return Variable(token)

    def conjunction():
        expr = primary()
        while peek(tokens) == "&":
            next(tokens)  # Consume "&" token
            expr = And(expr, primary())
        return expr

    def disjunction():
        expr = conjunction()
        while peek(tokens) == "|":
            next(tokens)  # Consume "|" token
            expr = Or(expr, conjunction())
        return expr

    def implication():
        expr = disjunction()
        while peek(tokens) == "=>":
            next(tokens)  # Consume "=>" token
            expr = Implies(expr, disjunction())
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