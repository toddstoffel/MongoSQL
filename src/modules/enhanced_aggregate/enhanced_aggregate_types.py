"""
Enhanced Aggregate Types and Data Structures

This module defines the data structures and enums used for enhanced aggregate operations.
Handles GROUP_CONCAT, statistical functions (STDDEV, VAR), and bitwise aggregations.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


class EnhancedAggregateFunctionType(Enum):
    """Types of enhanced aggregate functions"""
    GROUP_CONCAT = "GROUP_CONCAT"
    STDDEV_POP = "STDDEV_POP"
    STDDEV_SAMP = "STDDEV_SAMP" 
    VAR_POP = "VAR_POP"
    VAR_SAMP = "VAR_SAMP"
    BIT_AND = "BIT_AND"
    BIT_OR = "BIT_OR"
    BIT_XOR = "BIT_XOR"


@dataclass
class GroupConcatFunction:
    """Represents a GROUP_CONCAT function with all its options"""
    field: str                          # Field to concatenate
    separator: str = ","                # Separator between values
    distinct: bool = False              # Whether to use DISTINCT
    order_by: Optional[List[Dict]] = None  # ORDER BY clauses
    original_expression: str = ""       # Original SQL expression
    
    def to_mongodb_aggregation(self) -> Dict[str, Any]:
        """Convert to MongoDB aggregation pipeline stages"""
        pipeline_stages = []
        
        # Build the aggregation expression
        if self.distinct:
            # For DISTINCT, we need to use $addToSet first, then format
            group_expr = {"$addToSet": f"${self.field}"}
        else:
            # Regular concatenation
            group_expr = {"$push": f"${self.field}"}
        
        # Add sorting if specified
        if self.order_by:
            # Add $sort stage before grouping
            sort_spec = {}
            for order_item in self.order_by:
                direction = 1 if order_item.get('direction', 'ASC') == 'ASC' else -1
                sort_spec[order_item['field']] = direction
            pipeline_stages.append({"$sort": sort_spec})
        
        # Group and collect values
        group_stage = {
            "$group": {
                "_id": None,  # Group all documents together
                "values": group_expr
            }
        }
        pipeline_stages.append(group_stage)
        
        # Convert array to string with separator
        if self.distinct:
            # For DISTINCT, sort the array first (since $addToSet doesn't preserve order)
            project_stage = {
                "$project": {
                    "result": {
                        "$reduce": {
                            "input": {"$sortArray": {"input": "$values", "sortBy": 1}},
                            "initialValue": "",
                            "in": {
                                "$cond": {
                                    "if": {"$eq": ["$$value", ""]},
                                    "then": "$$this",
                                    "else": {"$concat": ["$$value", self.separator, "$$this"]}
                                }
                            }
                        }
                    }
                }
            }
        else:
            # Regular concatenation
            project_stage = {
                "$project": {
                    "result": {
                        "$reduce": {
                            "input": "$values",
                            "initialValue": "",
                            "in": {
                                "$cond": {
                                    "if": {"$eq": ["$$value", ""]},
                                    "then": "$$this",
                                    "else": {"$concat": ["$$value", self.separator, "$$this"]}
                                }
                            }
                        }
                    }
                }
            }
        
        pipeline_stages.append(project_stage)
        return pipeline_stages


@dataclass
class StatisticalFunction:
    """Represents statistical functions like STDDEV, VAR"""
    function_type: EnhancedAggregateFunctionType
    field: str
    original_expression: str = ""
    
    def to_mongodb_aggregation(self) -> Dict[str, Any]:
        """Convert to MongoDB aggregation expression with MariaDB precision"""
        if self.function_type == EnhancedAggregateFunctionType.STDDEV_POP:
            return {"$round": [{"$stdDevPop": f"${self.field}"}, 6]}
        elif self.function_type == EnhancedAggregateFunctionType.STDDEV_SAMP:
            return {"$round": [{"$stdDevSamp": f"${self.field}"}, 6]}
        elif self.function_type == EnhancedAggregateFunctionType.VAR_POP:
            # MongoDB doesn't have VAR_POP, calculate as (STDDEV_POP)^2 with rounding
            return {"$round": [
                {"$pow": [
                    {"$stdDevPop": f"${self.field}"},
                    2
                ]}, 6
            ]}
        elif self.function_type == EnhancedAggregateFunctionType.VAR_SAMP:
            # MongoDB doesn't have VAR_SAMP, calculate as (STDDEV_SAMP)^2 with rounding
            return {"$round": [
                {"$pow": [
                    {"$stdDevSamp": f"${self.field}"},
                    2
                ]}, 6
            ]}
        else:
            raise ValueError(f"Unsupported statistical function: {self.function_type}")


@dataclass 
class BitwiseFunction:
    """Represents bitwise aggregate functions"""
    function_type: EnhancedAggregateFunctionType
    field: str
    original_expression: str = ""
    
    def to_mongodb_aggregation(self) -> Dict[str, Any]:
        """Convert to MongoDB aggregation expression"""
        # MongoDB has native bitwise aggregation operators
        if self.function_type == EnhancedAggregateFunctionType.BIT_AND:
            return {"$bitAnd": f"${self.field}"}
        elif self.function_type == EnhancedAggregateFunctionType.BIT_OR:
            return {"$bitOr": f"${self.field}"}
        elif self.function_type == EnhancedAggregateFunctionType.BIT_XOR:
            return {"$bitXor": f"${self.field}"}
        else:
            raise ValueError(f"Unsupported bitwise function: {self.function_type}")


@dataclass
class EnhancedAggregateOperation:
    """Represents a complete enhanced aggregate operation"""
    function: Union[GroupConcatFunction, StatisticalFunction, BitwiseFunction]
    alias: Optional[str] = None
    context: str = "SELECT"  # SELECT, HAVING, etc.
    
    def to_mongodb_expression(self) -> Dict[str, Any]:
        """Convert to MongoDB expression based on function type"""
        if isinstance(self.function, GroupConcatFunction):
            # GROUP_CONCAT requires special pipeline handling
            return {"type": "group_concat", "pipeline": self.function.to_mongodb_aggregation()}
        else:
            # Statistical and bitwise functions use direct aggregation
            return self.function.to_mongodb_aggregation()


# Helper function for function detection
def is_enhanced_aggregate_function(function_name: str) -> bool:
    """Check if a function name is an enhanced aggregate function"""
    function_name_upper = function_name.upper()
    enhanced_functions = [
        'GROUP_CONCAT', 'STDDEV_POP', 'STDDEV_SAMP', 'VAR_POP', 'VAR_SAMP',
        'BIT_AND', 'BIT_OR', 'BIT_XOR'
    ]
    return function_name_upper in enhanced_functions


# Supported enhanced aggregate functions list
SUPPORTED_ENHANCED_AGGREGATE_FUNCTIONS = [
    'GROUP_CONCAT', 'STDDEV_POP', 'STDDEV_SAMP', 'VAR_POP', 'VAR_SAMP',
    'BIT_AND', 'BIT_OR', 'BIT_XOR'
]
