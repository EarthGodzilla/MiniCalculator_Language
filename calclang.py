import re
'''
python stuff to use: 
(condition_is_false, condition_is_true)[condition]
print(value_if_true if condition else value_if_false)
value_if_true if condition else value_if_false 

'''

#  tokens 
tokens = [
    'NUMBER', 'ID',
    'PLUS', 'MINUS', 'MUL', 'DIV',
    'GT', 'LT', 'EQ', 'GE', 'LE', 'NE',
    'LPAREN', 'RPAREN', 'COMMA', 'ASSIGN',
    'IF', 'THEN', 'ELSE', 'END', 'DEF', 'PRINT', 'RETURN'
]

token_regex = {
    'NUMBER': r'\d+(\.\d+)?',
    'ID': r'[a-zA-Z_]\w*',
    'PLUS': r'\+', 'MINUS': r'-', 'MUL': r'\*', 'DIV': r'/',
    'EQ': r'==', 'GE': r'>=', 'LE': r'<=', 'NE': r'!=',
    'GT': r'>', 'LT': r'<',
    'LPAREN': r'\(', 'RPAREN': r'\)', 'COMMA': r',', 'ASSIGN': r'=',
}

keywords = {
    'if': 'IF', 'then': 'THEN', 'else': 'ELSE',
    'end': 'END', 'def': 'DEF', 'print': 'PRINT',
    'return': 'RETURN'
}

#  lexer 
class Lexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.tokens = []

    def tokenize(self):
        while self.pos < len(self.code):
            match = None
            for token_type, pattern in token_regex.items():
                regex = re.compile(pattern)
                match = regex.match(self.code, self.pos)

                if match:
                    value = match.group(0)

                    if token_type == 'ID' and value in keywords:
                        self.tokens.append((keywords[value], value))
                    else:
                        if token_type == 'NUMBER':
                            value = float(value)
                        self.tokens.append((token_type, value))

                    self.pos = match.end()
                    break

            if not match:
                if self.code[self.pos].isspace():
                    self.pos += 1
                    continue
                raise SyntaxError(f"Unexpected char: {self.code[self.pos]}")

        return self.tokens


#  AST nodes 
class ASTNode: pass

class BinOpNode(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class NumberNode(ASTNode):
    def __init__(self, value):
        self.value = value

class VarNode(ASTNode):
    def __init__(self, name):
        self.name = name

class AssignNode(ASTNode):
    def __init__(self, var, expr):
        self.var = var
        self.expr = expr

class IfNode(ASTNode):
    def __init__(self, cond, then_body, else_body):
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body

class FuncDefNode(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class FuncCallNode(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class PrintNode(ASTNode):
    def __init__(self, expr):
        self.expr = expr

class ReturnNode(ASTNode):
    def __init__(self, expr):
        self.expr = expr


#  parser 
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def eat(self, expected):
        token = self.current_token()
        if token and token[0] == expected:
            self.pos += 1
            return token
        raise SyntaxError(f"Expected {expected}, got {token}")

    def parse_program(self):
        statements = []
        while self.current_token():
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self):
        token = self.current_token()

        if token[0] == 'ID':
            next_token = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None

            if next_token and next_token[0] == 'ASSIGN':
                var = self.eat('ID')[1]
                self.eat('ASSIGN')
                expr = self.parse_expression()
                return AssignNode(var, expr)

            elif next_token and next_token[0] == 'LPAREN':
                return self.parse_expression()

        elif token[0] == 'IF':
            return self.parse_if()

        elif token[0] == 'DEF':
            return self.parse_func_def()

        elif token[0] == 'PRINT':
            self.eat('PRINT')
            return PrintNode(self.parse_expression())

        elif token[0] == 'RETURN':
            self.eat('RETURN')
            return ReturnNode(self.parse_expression())

        return self.parse_expression()

    def parse_if(self):
        self.eat('IF')
        cond = self.parse_expression()
        self.eat('THEN')

        then_body = []
        while self.current_token() and self.current_token()[0] not in ('ELSE', 'END'):
            then_body.append(self.parse_statement())

        else_body = []
        if self.current_token() and self.current_token()[0] == 'ELSE':
            self.eat('ELSE')
            while self.current_token() and self.current_token()[0] != 'END':
                else_body.append(self.parse_statement())

        self.eat('END')
        return IfNode(cond, then_body, else_body)

    def parse_func_def(self):
        self.eat('DEF')
        name = self.eat('ID')[1]

        self.eat('LPAREN')
        params = []
        if self.current_token()[0] != 'RPAREN':
            params.append(self.eat('ID')[1])
            while self.current_token()[0] == 'COMMA':
                self.eat('COMMA')
                params.append(self.eat('ID')[1])
        self.eat('RPAREN')

        body = []
        while self.current_token() and self.current_token()[0] != 'END':
            body.append(self.parse_statement())

        self.eat('END')
        return FuncDefNode(name, params, body)

    def parse_expression(self):
        node = self.parse_term()

        while self.current_token() and self.current_token()[0] in ('PLUS', 'MINUS'):
            op = self.eat(self.current_token()[0])[1]
            node = BinOpNode(op, node, self.parse_term())

        if self.current_token() and self.current_token()[0] in ('GT','LT','EQ','GE','LE','NE'):
            op = self.eat(self.current_token()[0])[1]
            node = BinOpNode(op, node, self.parse_expression())

        return node

    def parse_term(self):
        node = self.parse_factor()

        while self.current_token() and self.current_token()[0] in ('MUL', 'DIV'):
            op = self.eat(self.current_token()[0])[1]
            node = BinOpNode(op, node, self.parse_factor())

        return node

    def parse_factor(self):
        token = self.current_token()

        if token[0] == 'NUMBER':
            return NumberNode(self.eat('NUMBER')[1])

        elif token[0] == 'MINUS':  # unary minus
            self.eat('MINUS')
            return BinOpNode('-', NumberNode(0), self.parse_factor())

        elif token[0] == 'ID':
            name = self.eat('ID')[1]

            if self.current_token() and self.current_token()[0] == 'LPAREN':
                self.eat('LPAREN')
                args = []
                if self.current_token()[0] != 'RPAREN':
                    args.append(self.parse_expression())
                    while self.current_token()[0] == 'COMMA':
                        self.eat('COMMA')
                        args.append(self.parse_expression())
                self.eat('RPAREN')
                return FuncCallNode(name, args)

            return VarNode(name)

        elif token[0] == 'LPAREN':
            self.eat('LPAREN')
            expr = self.parse_expression()
            self.eat('RPAREN')
            return expr

        raise SyntaxError("Invalid factor")


#  interpreter 
class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class Interpreter:
    def __init__(self):
        self.globals = {}
        self.functions = {}
        self.call_stack = []

    def visit(self, node):
        return getattr(self, f'visit_{type(node).__name__}')(node)

    def visit_NumberNode(self, node):
        return node.value

    def visit_VarNode(self, node):
        if self.call_stack:
            if node.name in self.call_stack[-1][1]:
                return self.call_stack[-1][1][node.name]
        if node.name in self.globals:
            return self.globals[node.name]
        raise NameError(f"Undefined variable {node.name}")

    def visit_AssignNode(self, node):
        value = self.visit(node.expr)
        if self.call_stack:
            self.call_stack[-1][1][node.var] = value
        else:
            self.globals[node.var] = value
        return value
#To Do fix, giving false div by 0 error when receiving end; FIXED
    def visit_BinOpNode(self, node):
        l = self.visit(node.left)
        r = self.visit(node.right)

        if node.op == '+':
            return l + r
        elif node.op == '-':
            return l - r
        elif node.op == '*':
            return l * r
        elif node.op == '/':
            if r == 0:
                raise ZeroDivisionError("Division by zero")
            return l / r

        elif node.op == '>':
            return l > r
        elif node.op == '<':
            return l < r
        elif node.op == '==':
            return l == r
        elif node.op == '>=':
            return l >= r
        elif node.op == '<=':
            return l <= r
        elif node.op == '!=':
            return l != r

        else:
            raise ValueError(f"Unknown operator {node.op}")

    def visit_IfNode(self, node):
        print("Evaluating if condition")
        if self.visit(node.cond):
            for stmt in node.then_body:
                self.visit(stmt)
        else:
            for stmt in node.else_body:
                self.visit(stmt)

    def visit_FuncDefNode(self, node):
        self.functions[node.name] = (node.params, node.body)

    def visit_FuncCallNode(self, node):
        if node.name not in self.functions:
            raise NameError(f"Function {node.name} not defined")

        params, body = self.functions[node.name]

        if len(params) != len(node.args):
            raise ValueError("Wrong number of arguments")

        local_scope = {p: self.visit(a) for p, a in zip(params, node.args)}

        self.call_stack.append((node.name, local_scope))

        try:
            result = None
            for stmt in body:
                result = self.visit(stmt)
        except ReturnException as r:
            result = r.value

        self.call_stack.pop()
        return result

    def visit_ReturnNode(self, node):
        raise ReturnException(self.visit(node.expr))

    def visit_PrintNode(self, node):
        val = self.visit(node.expr)
        print(val)
        return val

    def interpret(self, ast):
        for stmt in ast:
            self.visit(stmt)


#  repl 
def repl():
    interpreter = Interpreter()
    buffer = ""

    while True:
        try:
            line = input("CalcLang> ")
            buffer += " " + line

            lexer = Lexer(buffer)
            tokens = lexer.tokenize()

            open_blocks = sum(1 for t in tokens if t[0] in ('IF', 'DEF'))
            close_blocks = sum(1 for t in tokens if t[0] == 'END')

            if open_blocks > close_blocks:
                continue

            parser = Parser(tokens)
            ast = parser.parse_program()

            interpreter.interpret(ast)
            buffer = ""

        except Exception as e:
            print("Error:", e)
            print("Call Stack:")
            for func, scope in interpreter.call_stack:
                print(f"  in {func} with {scope}")
            buffer = ""


if __name__ == "__main__":
    repl()

"""
#Testcases used for stresstesting
#TC0
print 2 + 3 * 4

#TC1  
x = 10
print x + 5

#TC2
print -5 + 2

#TC3
x = -3
if x > 0 then
    print x
else
    print -x
end

#TC4
def add(a, b)
    return a + b
end
print add(5, 3)

#TC5
def fact(n)
    if n == 0 then
        return 1
    else
        return n * fact(n - 1)
    end
end
print fact(5)

#TC6
def test(a)
    return a / 0
end
print test(5)
"""