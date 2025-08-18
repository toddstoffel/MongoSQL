"""
REGEXP Types and Data Structures

This module defines the data structures and enums used for REGEXP operations.
Handles infix REGEXP/RLIKE operators in SQL expressions.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


class RegexpOperationType(Enum):
    """Types of REGEXP operations"""
    REGEXP = "REGEXP"      # 'text' REGEXP 'pattern'
    RLIKE = "RLIKE"        # 'text' RLIKE 'pattern' (alias for REGEXP)
    NOT_REGEXP = "NOT_REGEXP"  # 'text' NOT REGEXP 'pattern'


@dataclass
class InfixRegexpExpression:
    """Represents an infix REGEXP expression like 'text' REGEXP 'pattern'"""
    left_operand: str      # The text expression to test
    operator: str          # REGEXP, RLIKE, or NOT REGEXP
    right_operand: str     # The regex pattern
    original_expression: str  # Original SQL expression
    
    def to_mongodb_expression(self) -> Dict[str, Any]:
        """Convert to MongoDB $regexMatch expression"""
        base_regex = {
            "$regexMatch": {
                "input": self._process_operand(self.left_operand),
                "regex": self._process_pattern(self.right_operand)
            }
        }
        
        if self.operator.upper() == "NOT REGEXP":
            return {"$not": base_regex}
        else:
            return base_regex
    
    def _process_operand(self, operand: str) -> Any:
        """Process the left operand (text to test)"""
        # Remove quotes from string literals
        if operand.startswith("'") and operand.endswith("'"):
            return operand[1:-1]
        elif operand.startswith('"') and operand.endswith('"'):
            return operand[1:-1]
        else:
            # Field reference - ensure it starts with $
            return f"${operand}" if not operand.startswith('$') else operand
    
    def _process_pattern(self, pattern: str) -> str:
        """Process the right operand (regex pattern)"""
        # Remove quotes from pattern
        if pattern.startswith("'") and pattern.endswith("'"):
            return pattern[1:-1]
        elif pattern.startswith('"') and pattern.endswith('"'):
            return pattern[1:-1]
        else:
            return pattern


@dataclass 
class RegexpOperation:
    """Represents a complete REGEXP operation"""
    operation_type: RegexpOperationType
    expression: InfixRegexpExpression
    context: str  # 'SELECT', 'WHERE', 'HAVING', 'CASE'
    alias: Optional[str] = None  # For SELECT expressions with AS alias
    
    def to_mongodb_projection(self) -> Dict[str, Any]:
        """Convert to MongoDB projection for SELECT expressions"""
        field_name = self.alias or self.expression.original_expression
        
        # For SELECT expressions, REGEXP should return 1/0 like MariaDB
        mongo_expr = self.expression.to_mongodb_expression()
        
        return {
            field_name: {
                "$cond": [mongo_expr, 1, 0]
            }
        }


# Supported REGEXP operators
SUPPORTED_REGEXP_OPERATORS = ['REGEXP', 'RLIKE', 'NOT REGEXP']


def is_regexp_expression(expression: str) -> bool:
    """Check if an expression contains REGEXP operators"""
    expr_upper = expression.upper()
    return any(op in expr_upper for op in SUPPORTED_REGEXP_OPERATORS)


def parse_regexp_expression(expression: str) -> Optional[InfixRegexpExpression]:
    """Parse a string expression to extract REGEXP components"""
    expr_upper = expression.upper()
    
    # Find the REGEXP operator
    operator = None
    operator_pos = -1
    
    for op in SUPPORTED_REGEXP_OPERATORS:
        pos = expr_upper.find(f' {op} ')
        if pos != -1:
            operator = op
            operator_pos = pos
            break
    
    if operator is None:
        return None
    
    # Split the expression
    left_part = expression[:operator_pos].strip()
    right_part = expression[operator_pos + len(operator) + 2:].strip()
    
    return InfixRegexpExpression(
        left_operand=left_part,
        operator=operator,
        right_operand=right_part,
        original_expression=expression
    )
