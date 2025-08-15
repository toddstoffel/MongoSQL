"""
Type definitions for WHERE clause operations
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class WhereOperator(Enum):
    """SQL WHERE operators"""
    EQUALS = "="
    NOT_EQUALS = "!="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LIKE = "LIKE"
    NOT_LIKE = "NOT LIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
    BETWEEN = "BETWEEN"
    NOT_BETWEEN = "NOT BETWEEN"


class LogicalOperator(Enum):
    """Logical operators for compound WHERE clauses"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


@dataclass
class WhereCondition:
    """Represents a single WHERE condition"""
    field: str
    operator: WhereOperator
    value: Any
    is_function: bool = False


@dataclass
class CompoundWhereCondition:
    """Represents a compound WHERE condition with logical operators"""
    operator: LogicalOperator
    conditions: List[Union['WhereCondition', 'CompoundWhereCondition']]


@dataclass
class WhereClause:
    """Represents a complete WHERE clause"""
    conditions: List[Union[WhereCondition, CompoundWhereCondition]]
    
    def is_empty(self) -> bool:
        """Check if the WHERE clause is empty"""
        return not self.conditions
