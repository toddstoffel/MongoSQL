"""
Enhanced Aggregate Functions Module

This module provides advanced aggregation functions beyond the basic COUNT, SUM, AVG, MIN, MAX.
Handles GROUP_CONCAT, statistical functions, and bitwise aggregations.
"""

from .enhanced_aggregate_types import (
    EnhancedAggregateOperation,
    GroupConcatFunction,
    StatisticalFunction,
    BitwiseFunction,
    EnhancedAggregateFunctionType,
    is_enhanced_aggregate_function,
)

from .enhanced_aggregate_parser import EnhancedAggregateParser
from .enhanced_aggregate_translator import EnhancedAggregateTranslator
from .enhanced_aggregate_function_mapper import EnhancedAggregateFunctionMapper

__all__ = [
    "EnhancedAggregateOperation",
    "GroupConcatFunction",
    "StatisticalFunction",
    "BitwiseFunction",
    "EnhancedAggregateFunctionType",
    "is_enhanced_aggregate_function",
    "EnhancedAggregateParser",
    "EnhancedAggregateTranslator",
    "EnhancedAggregateFunctionMapper",
]
