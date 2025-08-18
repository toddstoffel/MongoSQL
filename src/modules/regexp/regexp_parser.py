"""
REGEXP Parser Module

This module parses SQL expressions containing REGEXP/RLIKE operators.
Handles infix expressions like 'text' REGEXP 'pattern'.
"""

import sqlparse
from sqlparse.sql import Token, IdentifierList, Identifier
from sqlparse.tokens import Keyword, Name, String, Punctuation
from typing import List, Optional, Tuple, Any

from .regexp_types import InfixRegexpExpression, RegexpOperation, RegexpOperationType, is_regexp_expression, parse_regexp_expression


class RegexpParser:
    """Parser for REGEXP expressions in SQL"""
    
    def __init__(self):
        self.regexp_operators = ['REGEXP', 'RLIKE', 'NOT REGEXP']
    
    def parse_select_list(self, tokens: List[Token]) -> List[RegexpOperation]:
        """Parse SELECT expressions for REGEXP operations"""
        regexp_operations = []
        
        # Find SELECT expressions
        select_expressions = self._extract_select_expressions(tokens)
        
        for expr, alias in select_expressions:
            if is_regexp_expression(expr):
                regexp_expr = parse_regexp_expression(expr)
                if regexp_expr:
                    operation = RegexpOperation(
                        operation_type=self._get_operation_type(regexp_expr.operator),
                        expression=regexp_expr,
                        context='SELECT',
                        alias=alias
                    )
                    regexp_operations.append(operation)
        
        return regexp_operations
    
    def parse_where_clause(self, tokens: List[Token]) -> List[RegexpOperation]:
        """Parse WHERE clause for REGEXP operations"""
        regexp_operations = []
        
        # Extract WHERE expressions
        where_expressions = self._extract_where_expressions(tokens)
        
        for expr in where_expressions:
            if is_regexp_expression(expr):
                regexp_expr = parse_regexp_expression(expr)
                if regexp_expr:
                    operation = RegexpOperation(
                        operation_type=self._get_operation_type(regexp_expr.operator),
                        expression=regexp_expr,
                        context='WHERE'
                    )
                    regexp_operations.append(operation)
        
        return regexp_operations
    
    def parse_having_clause(self, tokens: List[Token]) -> List[RegexpOperation]:
        """Parse HAVING clause for REGEXP operations"""
        regexp_operations = []
        
        # Extract HAVING expressions
        having_expressions = self._extract_having_expressions(tokens)
        
        for expr in having_expressions:
            if is_regexp_expression(expr):
                regexp_expr = parse_regexp_expression(expr)
                if regexp_expr:
                    operation = RegexpOperation(
                        operation_type=self._get_operation_type(regexp_expr.operator),
                        expression=regexp_expr,
                        context='HAVING'
                    )
                    regexp_operations.append(operation)
        
        return regexp_operations
    
    def _extract_select_expressions(self, tokens: List[Token]) -> List[Tuple[str, Optional[str]]]:
        """Extract expressions from SELECT clause"""
        expressions = []
        current_expr = ""
        alias = None
        in_select = False
        
        for i, token in enumerate(tokens):
            if token.ttype is Keyword and token.normalized == 'SELECT':
                in_select = True
                continue
            elif token.ttype is Keyword and token.normalized in ['FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING']:
                if current_expr.strip():
                    expressions.append((current_expr.strip(), alias))
                break
            elif in_select:
                if token.ttype is Punctuation and str(token) == ',':
                    if current_expr.strip():
                        expressions.append((current_expr.strip(), alias))
                    current_expr = ""
                    alias = None
                elif token.ttype is Keyword and token.normalized == 'AS':
                    # Next non-whitespace token is the alias
                    for j in range(i + 1, len(tokens)):
                        if tokens[j].ttype not in (None, sqlparse.tokens.Whitespace):
                            alias = str(tokens[j]).strip()
                            break
                else:
                    current_expr += str(token)
        
        if current_expr.strip():
            expressions.append((current_expr.strip(), alias))
        
        return expressions
    
    def _extract_where_expressions(self, tokens: List[Token]) -> List[str]:
        """Extract expressions from WHERE clause"""
        expressions = []
        current_expr = ""
        in_where = False
        
        for token in tokens:
            if token.ttype is Keyword and token.normalized == 'WHERE':
                in_where = True
                continue
            elif token.ttype is Keyword and token.normalized in ['GROUP', 'ORDER', 'HAVING', 'LIMIT']:
                break
            elif in_where:
                if token.ttype is Keyword and token.normalized in ['AND', 'OR']:
                    if current_expr.strip():
                        expressions.append(current_expr.strip())
                    current_expr = ""
                else:
                    current_expr += str(token)
        
        if current_expr.strip():
            expressions.append(current_expr.strip())
        
        return expressions
    
    def _extract_having_expressions(self, tokens: List[Token]) -> List[str]:
        """Extract expressions from HAVING clause"""
        expressions = []
        current_expr = ""
        in_having = False
        
        for token in tokens:
            if token.ttype is Keyword and token.normalized == 'HAVING':
                in_having = True
                continue
            elif token.ttype is Keyword and token.normalized in ['ORDER', 'LIMIT']:
                break
            elif in_having:
                if token.ttype is Keyword and token.normalized in ['AND', 'OR']:
                    if current_expr.strip():
                        expressions.append(current_expr.strip())
                    current_expr = ""
                else:
                    current_expr += str(token)
        
        if current_expr.strip():
            expressions.append(current_expr.strip())
        
        return expressions
    
    def _get_operation_type(self, operator: str) -> RegexpOperationType:
        """Convert operator string to RegexpOperationType"""
        op_upper = operator.upper()
        if op_upper == 'REGEXP':
            return RegexpOperationType.REGEXP
        elif op_upper == 'RLIKE':
            return RegexpOperationType.RLIKE
        elif op_upper == 'NOT REGEXP':
            return RegexpOperationType.NOT_REGEXP
        else:
            return RegexpOperationType.REGEXP  # Default
    
    def has_regexp_expressions(self, sql: str) -> bool:
        """Check if SQL contains REGEXP expressions"""
        return is_regexp_expression(sql)
    
    def parse_sql(self, sql: str) -> List[RegexpOperation]:
        """Parse complete SQL statement for all REGEXP operations"""
        parsed = sqlparse.parse(sql)[0]
        tokens = list(parsed.flatten())
        
        operations = []
        operations.extend(self.parse_select_list(tokens))
        operations.extend(self.parse_where_clause(tokens))
        operations.extend(self.parse_having_clause(tokens))
        
        return operations
