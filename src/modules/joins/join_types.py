"""
JOIN type definitions and enumerations
"""
from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

class JoinType(Enum):
    """Enumeration of supported JOIN types"""
    INNER = "INNER"
    LEFT = "LEFT" 
    RIGHT = "RIGHT"
    FULL = "FULL"
    CROSS = "CROSS"

@dataclass
class JoinCondition:
    """Represents a JOIN condition"""
    left_table: str
    left_column: str
    right_table: str
    right_column: str
    operator: str = "="
    
    def __str__(self):
        return f"{self.left_table}.{self.left_column} {self.operator} {self.right_table}.{self.right_column}"

@dataclass
class JoinOperation:
    """Represents a complete JOIN operation"""
    join_type: JoinType
    left_table: str
    right_table: str
    conditions: List[JoinCondition]
    alias_left: Optional[str] = None
    alias_right: Optional[str] = None
    
    def __str__(self):
        conditions_str = " AND ".join(str(cond) for cond in self.conditions)
        return f"{self.join_type.value} JOIN {self.right_table} ON {conditions_str}"

class JoinTypeHandler:
    """Base class for handling different JOIN types"""
    
    def __init__(self, join_type: JoinType):
        self.join_type = join_type
    
    def create_lookup_stage(self, join_op: JoinOperation) -> Dict[str, Any]:
        """Create MongoDB $lookup stage for this JOIN type"""
        raise NotImplementedError("Subclasses must implement create_lookup_stage")
    
    def requires_unwind(self) -> bool:
        """Check if this JOIN type requires $unwind stage"""
        return True
    
    def create_match_stage(self, join_op: JoinOperation) -> Optional[Dict[str, Any]]:
        """Create optional $match stage for JOIN filtering"""
        return None

class InnerJoinHandler(JoinTypeHandler):
    """Handler for INNER JOIN operations"""
    
    def __init__(self):
        super().__init__(JoinType.INNER)
    
    def create_lookup_stage(self, join_op: JoinOperation) -> Dict[str, Any]:
        """Create $lookup stage for INNER JOIN"""
        condition = join_op.conditions[0]  # For now, handle single condition
        
        return {
            "$lookup": {
                "from": join_op.right_table,
                "localField": condition.left_column,
                "foreignField": condition.right_column,
                "as": f"{join_op.right_table}_joined"
            }
        }
    
    def create_match_stage(self, join_op: JoinOperation) -> Dict[str, Any]:
        """INNER JOIN requires non-empty joined array"""
        return {
            "$match": {
                f"{join_op.right_table}_joined": {"$ne": []}
            }
        }

class LeftJoinHandler(JoinTypeHandler):
    """Handler for LEFT JOIN operations"""
    
    def __init__(self):
        super().__init__(JoinType.LEFT)
    
    def create_lookup_stage(self, join_op: JoinOperation) -> Dict[str, Any]:
        """Create $lookup stage for LEFT JOIN"""
        condition = join_op.conditions[0]
        
        return {
            "$lookup": {
                "from": join_op.right_table,
                "localField": condition.left_column,
                "foreignField": condition.right_column,
                "as": f"{join_op.right_table}_joined"
            }
        }
    
    def requires_unwind(self) -> bool:
        """LEFT JOIN uses preserveNullAndEmptyArrays"""
        return True

class RightJoinHandler(JoinTypeHandler):
    """Handler for RIGHT JOIN operations"""
    
    def __init__(self):
        super().__init__(JoinType.RIGHT)
    
    def create_lookup_stage(self, join_op: JoinOperation) -> Dict[str, Any]:
        """Create $lookup stage for RIGHT JOIN"""
        # For RIGHT JOIN, we start from the right table and lookup the left table
        # Since we're now starting from the right table, we lookup the left table
        condition = join_op.conditions[0]  # For now, handle single condition
        return {
            "$lookup": {
                "from": join_op.left_table,  # Lookup the left table (customers)
                "localField": condition.right_column,  # Use right table column (customerNumber from orders)
                "foreignField": condition.left_column,  # Use left table column (customerNumber from customers)
                "as": f"{join_op.left_table}_joined"  # Store as customers_joined
            }
        }
    
    def requires_unwind(self) -> bool:
        """RIGHT JOIN preserves all right table records"""
        return True

class CrossJoinHandler(JoinTypeHandler):
    """Handler for CROSS JOIN operations"""
    
    def __init__(self):
        super().__init__(JoinType.CROSS)
    
    def create_lookup_stage(self, join_op: JoinOperation) -> Dict[str, Any]:
        """Create $lookup stage for CROSS JOIN (Cartesian product)"""
        return {
            "$lookup": {
                "from": join_op.right_table,
                "pipeline": [],  # Empty pipeline for all documents
                "as": f"{join_op.right_table}_joined"
            }
        }

# Factory for creating JOIN handlers
JOIN_HANDLERS = {
    JoinType.INNER: InnerJoinHandler,
    JoinType.LEFT: LeftJoinHandler,
    JoinType.RIGHT: RightJoinHandler,
    JoinType.CROSS: CrossJoinHandler,
    # FULL will be added later
}

def get_join_handler(join_type: JoinType) -> JoinTypeHandler:
    """Factory function to get appropriate JOIN handler"""
    handler_class = JOIN_HANDLERS.get(join_type)
    if not handler_class:
        raise ValueError(f"Unsupported JOIN type: {join_type}")
    return handler_class()
