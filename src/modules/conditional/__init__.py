"""
Conditional module for SQL conditional functions (IF, CASE WHEN, COALESCE, NULLIF)
"""

from .conditional_types import (
    ConditionalType,
    ConditionalExpression,
    IfExpression,
    WhenClause,
    CaseExpression,
    CoalesceExpression,
    NullIfExpression
)

from .conditional_parser import ConditionalParser
from .conditional_translator import ConditionalTranslator
from .conditional_function_mapper import ConditionalFunctionMapper

__all__ = [
    'ConditionalType',
    'ConditionalExpression',
    'IfExpression',
    'WhenClause', 
    'CaseExpression',
    'CoalesceExpression',
    'NullIfExpression',
    'ConditionalParser',
    'ConditionalTranslator',
    'ConditionalFunctionMapper'
]
