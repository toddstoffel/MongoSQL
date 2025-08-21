"""
Window Function Types for MongoSQL

This module defines the data structures and enums used for window function processing.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


class WindowFunctionType(Enum):
    """Enumeration of supported window function types"""

    ROW_NUMBER = "ROW_NUMBER"
    RANK = "RANK"
    DENSE_RANK = "DENSE_RANK"
    NTILE = "NTILE"
    LAG = "LAG"
    LEAD = "LEAD"


@dataclass
class OrderByClause:
    """Represents an ORDER BY clause in a window specification"""

    field: str
    direction: str = "ASC"  # ASC or DESC

    def to_mongo_sort(self) -> Dict[str, int]:
        """Convert to MongoDB sort specification"""
        return {self.field: 1 if self.direction.upper() == "ASC" else -1}


@dataclass
class PartitionByClause:
    """Represents a PARTITION BY clause in a window specification"""

    fields: List[str]

    def to_mongo_partition(self) -> Dict[str, str]:
        """Convert to MongoDB partition specification"""
        if len(self.fields) == 1:
            return f"${self.fields[0]}"
        else:
            # Multiple fields - create compound partition key
            return {field: f"${field}" for field in self.fields}


@dataclass
class WindowFrame:
    """Represents a window frame specification (ROWS/RANGE BETWEEN...)"""

    frame_type: str = "ROWS"  # ROWS or RANGE
    start_bound: str = "UNBOUNDED PRECEDING"
    end_bound: str = "CURRENT ROW"


@dataclass
class WindowSpec:
    """Represents a complete window specification (OVER clause)"""

    partition_by: Optional[PartitionByClause] = None
    order_by: Optional[List[OrderByClause]] = None
    frame: Optional[WindowFrame] = None

    def get_mongo_sort(self) -> Dict[str, int]:
        """Get MongoDB sort specification from ORDER BY clause"""
        if not self.order_by:
            return {}

        sort_spec = {}
        for order_clause in self.order_by:
            sort_spec.update(order_clause.to_mongo_sort())
        return sort_spec


@dataclass
class WindowFunction:
    """Represents a complete window function call"""

    function_type: WindowFunctionType
    alias: Optional[str] = None
    arguments: Optional[List[Any]] = None
    window_spec: Optional[WindowSpec] = None

    def get_primary_argument(self) -> Optional[Any]:
        """Get the primary argument for functions that need it (like NTILE)"""
        if self.arguments and len(self.arguments) > 0:
            return self.arguments[0]
        return None


@dataclass
class WindowQuery:
    """Represents a complete SQL query with window functions"""

    select_fields: List[str]
    window_functions: List[WindowFunction]
    from_table: str
    where_conditions: Optional[Dict[str, Any]] = None
    final_order_by: Optional[List[OrderByClause]] = None
    limit: Optional[int] = None

    def has_window_functions(self) -> bool:
        """Check if this query has any window functions"""
        return len(self.window_functions) > 0
