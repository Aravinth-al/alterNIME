# NO IMPORTS HERE to avoid circular dependency

class KNIMECodeGenerator:
    def __init__(self, target_column=None):
        self.target_column = target_column

    def generate(self, node):
        # Dynamic dispatch based on node class name
        # e.g. FunctionCall -> visit_FunctionCall
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        # Useful error message for debugging
        raise NotImplementedError(f"No visit_{type(node).__name__} method defined in codegen.py")

    def visit_Expression(self, node):
        return self.generate(node.body)

    def visit_FunctionCall(self, node):
        name = node.name.upper()
        args = [self.generate(arg) for arg in node.args]
        
        # MAPPINGS
        if name == "REGEX_REPLACE":
            return f'regexReplace({args[0]}, {args[1]}, {args[2]})'
        elif name == "REGEX_MATCH":
            return f'regexMatcher({args[0]}, {args[1]})'
        elif name == "ISNULL":
            return f'isMissing({args[0]})'
        elif name == "ISEMPTY":
             return f'({args[0]} == "")'
        elif name == "DATETIMESTART":
             return "new Date().toISOString()" # Basic fallback
        elif name == "LEFT":
             # Left(str, len) -> substr(str, 0, len)
             return f'substr({args[0]}, 0, {args[1]})'
        elif name == "REPLACE":
             return f'replace({args[0]}, {args[1]}, {args[2]})'

        return f'{node.name}({", ".join(args)})'

    def visit_IfExpression(self, node):
        cond = self.generate(node.condition)
        true_val = self.generate(node.true_branch)
        false_val = self.generate(node.false_branch)
        return f'({cond}) ? {true_val} : {false_val}'

    def visit_BinaryOp(self, node):
        left = self.generate(node.left)
        right = self.generate(node.right)
        op = node.op
        if op == '=': op = '=='
        if op == '<>': op = '!='
        if op.upper() == 'AND': op = '&&'
        if op.upper() == 'OR': op = '||'
        return f'({left} {op} {right})'

    def visit_ColumnRef(self, node):
        if self.target_column and node.name == self.target_column:
            return "val"
        return f'column("{node.name}")'

    def visit_StringLiteral(self, node):
        return f'"{node.value}"'

    def visit_NumberLiteral(self, node):
        return str(node.value)