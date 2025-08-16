"""
Subqueries module for SQL to MongoDB subquery operations
Handles: WHERE subqueries, IN subqueries, EXISTS subqueries, scalar subqueries
"""

from .subquery_types import SubqueryType, SubqueryOperation
from .subquery_parser import SubqueryParser
from .subquery_translator import SubqueryTranslator

__all__ = [
    'SubqueryType',
    'SubqueryOperation', 
    'SubqueryParser',
    'SubqueryTranslator'
]
