"""
Type definitions for conditional operations (IF, CASE WHEN, COALESCE, NULLIF)
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class ConditionalType(Enum):
    """Types of conditional expressions"""
    IF = "IF"
    CASE_WHEN = "CASE_WHEN"
    COALESCE = "COALESCE"
    NULLIF = "NULLIF"


@dataclass
class IfExpression:
    """Represents an IF(condition, value_if_true, value_if_false) expression"""
    condition: Any
    value_if_true: Any
    value_if_false: Any


@dataclass
class WhenClause:
    """Represents a WHEN condition THEN value clause"""
    condition: Any
    value: Any


@dataclass
class CaseExpression:
    """Represents a CASE WHEN ... THEN ... ELSE ... END expression"""
    when_clauses: List[WhenClause]
    else_value: Optional[Any] = None


@dataclass
class CoalesceExpression:
    """Represents a COALESCE(value1, value2, ...) expression"""
    values: List[Any]


@dataclass
class NullIfExpression:
    """Represents a NULLIF(expr1, expr2) expression"""
    expr1: Any
    expr2: Any


@dataclass
class ConditionalExpression:
    """Represents any conditional expression"""
    conditional_type: ConditionalType
    expression: Union[IfExpression, CaseExpression, CoalesceExpression, NullIfExpression]
