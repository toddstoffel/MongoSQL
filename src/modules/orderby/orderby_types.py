"""
ORDER BY types and data structures
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

class SortDirection(Enum):
    """Sort direction enumeration"""
    ASC = "ASC"
    DESC = "DESC"

@dataclass
class OrderField:
    """Represents a single field in ORDER BY clause"""
    field: str
    direction: SortDirection = SortDirection.ASC
    
    def to_mongodb_sort(self) -> Dict[str, int]:
        """Convert to MongoDB sort specification"""
        return {self.field: 1 if self.direction == SortDirection.ASC else -1}

@dataclass 
class OrderByClause:
    """Represents a complete ORDER BY clause"""
    fields: List[OrderField]
    
    def to_mongodb_sort(self) -> Dict[str, int]:
        """Convert to MongoDB $sort stage"""
        sort_spec = {}
        for field in self.fields:
            sort_spec.update(field.to_mongodb_sort())
        return sort_spec
    
    def is_empty(self) -> bool:
        """Check if ORDER BY clause is empty"""
        return len(self.fields) == 0
