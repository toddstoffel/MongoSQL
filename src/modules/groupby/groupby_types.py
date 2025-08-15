"""
Type definitions for GROUP BY operations
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class GroupByField:
    """Represents a single GROUP BY field"""
    field_name: str
    alias: Optional[str] = None


@dataclass
class AggregateFunction:
    """Represents an aggregate function in GROUP BY context"""
    function_name: str
    field_name: str
    alias: Optional[str] = None
    original_call: Optional[str] = None


@dataclass
class GroupByStructure:
    """Represents a complete GROUP BY operation"""
    group_fields: List[GroupByField]
    aggregate_functions: List[AggregateFunction]
    regular_columns: List[str]
    having_conditions: Optional[Dict[str, Any]] = None
    
    def is_empty(self) -> bool:
        """Check if this GROUP BY structure is empty"""
        return len(self.group_fields) == 0 and len(self.aggregate_functions) == 0
    
    def has_aggregates(self) -> bool:
        """Check if this GROUP BY has aggregate functions"""
        return len(self.aggregate_functions) > 0
    
    def get_group_field_names(self) -> List[str]:
        """Get list of field names being grouped by"""
        return [field.field_name for field in self.group_fields]
