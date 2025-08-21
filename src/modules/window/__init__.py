"""
Window Functions Module for MongoSQL

This module provides SQL Window Function support, specifically for the
working window functions: NTILE, LAG, and LEAD.
"""

from .window_types import WindowFunctionType
from .window_function_mapper import WindowFunctionMapper

__all__ = [
    "WindowFunctionType",
    "WindowFunctionMapper",
]
