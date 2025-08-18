"""
REGEXP Module

This module handles REGEXP/RLIKE infix operators in various SQL contexts:
- SELECT expressions: 'test123' REGEXP '[0-9]+'  
- WHERE clauses: WHERE column REGEXP pattern (already handled by core)
- HAVING clauses: HAVING expression REGEXP pattern
- CASE statements: CASE WHEN value REGEXP pattern THEN result

Key difference from extended_string module:
- extended_string handles function-style: REGEXP_SUBSTR('text', 'pattern')
- regexp module handles infix-style: 'text' REGEXP 'pattern'
"""

from .regexp_types import (
    RegexpOperation,
    RegexpOperationType,
    InfixRegexpExpression,
    is_regexp_expression,
    SUPPORTED_REGEXP_OPERATORS
)

from .regexp_parser import RegexpParser
from .regexp_translator import RegexpTranslator
from .regexp_function_mapper import RegexpFunctionMapper

__all__ = [
    'RegexpOperation',
    'RegexpOperationType', 
    'InfixRegexpExpression',
    'RegexpParser',
    'RegexpTranslator',
    'RegexpFunctionMapper',
    'is_regexp_expression',
    'SUPPORTED_REGEXP_OPERATORS'
]
