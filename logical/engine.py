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
    tokens = []
    current_token = ""
    for c in expr_str:
        if c in " \t\n":
            continue
        if c in "~&|()":
            if current_token:
                tokens.append(current_token)
                current_token = ""
            tokens.append(c)
        elif c == "=":
            current_token += c
        else:
            if current_token == "=":
                current_token += c
                tokens.append(current_token)
                current_token = ""
            else:
                current_token += c
    if current_token:
        tokens.append(current_token)
    return tokens

def parse(tokens):
    stack = []
    for token in tokens:
        if token == ")":
            right = stack.pop()
            op = stack.pop()
            left = stack.pop()
            stack.pop()  # Discard "("
            if op == "&":
                stack.append(And(left, right))
            elif op == "|":
                stack.append(Or(left, right))
            elif op == "=>":
                stack.append(Implies(left, right))
        elif token in "~&|=>":
            stack.append(token)
        elif token == "(":
            stack.append(token)
        else:
            variable = Variable(token)
            if stack and stack[-1] == "~":
                stack.pop()
                stack.append(Not(variable))
            else:
                stack.append(variable)
    return stack[0]

def evaluate(expr, valuation):
    if isinstance(expr, Variable):
        return valuation[expr.name]
    if isinstance(expr, Not):
        return not evaluate(expr.expr, valuation)
    if isinstance(expr, And):
        return evaluate(expr.left, valuation) and evaluate(expr.right, valuation)
    if isinstance(expr, Or):
        return evaluate(expr.left, valuation) or evaluate(expr.right, valuation)
    if isinstance(expr, Implies):
        return not evaluate(expr.left, valuation) or evaluate(expr.right, valuation)
