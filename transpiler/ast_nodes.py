from dataclasses import dataclass
from typing import List, Any, Optional

@dataclass
class Node: pass

@dataclass
class Expression(Node):
    body: Any

@dataclass
class NumberLiteral(Node):
    value: float

@dataclass
class StringLiteral(Node):
    value: str

@dataclass
class ColumnRef(Node):
    name: str

@dataclass
class FunctionCall(Node):
    name: str
    args: List[Any]

@dataclass
class BinaryOp(Node):
    left: Any
    op: str
    right: Any

@dataclass
class IfExpression(Node):
    condition: Any
    true_branch: Any
    false_branch: Any