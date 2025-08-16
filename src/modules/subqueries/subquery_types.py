"""
Type definitions for subquery operations
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

class SubqueryType(Enum):
    """Types of subqueries supported"""
    SCALAR = "scalar"          # Single value: WHERE col = (SELECT ...)
    IN_LIST = "in_list"        # List comparison: WHERE col IN (SELECT ...)
    EXISTS = "exists"          # Existence check: WHERE EXISTS (SELECT ...)
    NOT_EXISTS = "not_exists"  # Non-existence: WHERE NOT EXISTS (SELECT ...)
    ROW = "row"                # Row/tuple comparison: WHERE (col1, col2) = (SELECT col1, col2 ...)
    DERIVED = "derived"        # Derived table: FROM (SELECT ...) alias

@dataclass
class SubqueryOperation:
    """Represents a parsed subquery operation"""
    subquery_type: SubqueryType
    outer_field: str              # Field being compared in outer query
    inner_query: str             # The subquery SQL
    inner_collection: str        # Collection name from subquery
    inner_field: Optional[str]   # Field from subquery (for scalar/IN)
    comparison_op: str           # Comparison operator (=, IN, EXISTS)
    correlation_fields: List[str] = None  # For correlated subqueries
    
    def __post_init__(self):
        if self.correlation_fields is None:
            self.correlation_fields = []

class SubqueryContext:
    """Context for subquery processing"""
    
    def __init__(self):
        self.outer_collection: str = ""
        self.outer_alias: str = ""
        self.correlation_map: Dict[str, str] = {}  # Maps outer.field -> inner.field
        
    def add_correlation(self, outer_field: str, inner_field: str):
        """Add field correlation between outer and inner queries"""
        self.correlation_map[outer_field] = inner_field
        
    def is_correlated(self) -> bool:
        """Check if subquery has correlations"""
        return len(self.correlation_map) > 0
