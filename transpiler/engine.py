from lark import Lark, Transformer, v_args
from .ast_nodes import *

# --- GRAMMAR (Clean) ---
grammar = r"""
    ?start: expression

    ?expression: if_expr
               | boolean_expr

    ?if_expr: "IF" boolean_expr "THEN" expression "ELSE" expression "ENDIF" -> if_expr
            | "IIF" "(" boolean_expr "," expression "," expression ")"      -> iif_expr

    ?boolean_expr: boolean_term
                 | boolean_expr "OR" boolean_term   -> or_op

    ?boolean_term: comparison
                 | boolean_term "AND" comparison    -> and_op

    ?comparison: additive
               | additive "=" additive              -> eq
               | additive "==" additive             -> eq
               | additive "!=" additive             -> neq
               | additive "<>" additive             -> neq
               | additive "<" additive              -> lt
               | additive ">" additive              -> gt
               | additive "<=" additive             -> lte
               | additive ">=" additive             -> gte
               | "NOT" comparison                   -> not_op

    ?additive: term
             | additive "+" term                    -> add
             | additive "-" term                    -> sub
             | additive "&" term                    -> concat

    ?term: factor
         | term "*" factor                          -> mul
         | term "/" factor                          -> div

    ?factor: atom
           | "-" factor                             -> neg

    ?atom: NUMBER                                   -> number
         | STRING_LITERAL                           -> string
         | COLUMN_LITERAL                           -> column_ref
         | NAME "(" [arglist] ")"                   -> function_call
         | "(" expression ")"

    arglist: expression ("," expression)*

    COLUMN_LITERAL: "[" /[^\]]+/ "]"
    STRING_LITERAL: /'[^']*'/ | /"[^"]*"/

    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

# --- TRANSFORMER ---
class AlteryxToAST(Transformer):
    def number(self, n):
        return NumberLiteral(float(n[0]))
    
    def string(self, s):
        raw = s[0].value
        return StringLiteral(raw[1:-1]) 
    
    def column_ref(self, c):
        raw = c[0].value
        return ColumnRef(raw[1:-1]) 
    
    def function_call(self, args):
        name = args[0]
        params = args[1].children if len(args) > 1 else []
        return FunctionCall(name.value, params)
    
    def if_expr(self, args):
        return IfExpression(args[0], args[1], args[2])
    
    def iif_expr(self, args):
        return IfExpression(args[0], args[1], args[2])

    # Binary Ops
    def add(self, args): return BinaryOp(args[0], '+', args[1])
    def sub(self, args): return BinaryOp(args[0], '-', args[1])
    def concat(self, args): return BinaryOp(args[0], '+', args[1])
    def mul(self, args): return BinaryOp(args[0], '*', args[1])
    def div(self, args): return BinaryOp(args[0], '/', args[1])
    
    # Logic
    def eq(self, args): return BinaryOp(args[0], '=', args[1])
    def neq(self, args): return BinaryOp(args[0], '!=', args[1])
    def lt(self, args): return BinaryOp(args[0], '<', args[1])
    def gt(self, args): return BinaryOp(args[0], '>', args[1])
    def lte(self, args): return BinaryOp(args[0], '<=', args[1])
    def gte(self, args): return BinaryOp(args[0], '>=', args[1])
    def and_op(self, args): return BinaryOp(args[0], 'AND', args[1])
    def or_op(self, args): return BinaryOp(args[0], 'OR', args[1])

def get_parser():
    return Lark(grammar, start='start', parser='lalr')