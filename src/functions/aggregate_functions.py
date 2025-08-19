"""
Aggregate function mapper for SQL to MongoDB aggregation pipeline
Handles: COUNT, SUM, AVG, MIN, MAX, GROUP_CONCAT, etc.
"""

from typing import Dict, List, Any, Optional


class AggregateFunctionMapper:
    """Maps SQL aggregate functions to MongoDB aggregation pipeline operators"""

    def __init__(self):
        self.function_map = self._build_aggregate_map()

    def _build_aggregate_map(self) -> Dict[str, Dict[str, Any]]:
        """Build the aggregate function mapping dictionary"""
        return {
            "COUNT": {
                "mongodb": "$sum",
                "stage": "$group",
                "type": "aggregate",
                "description": "Count documents or non-null values",
                "default_value": 1,  # For COUNT(*) we sum 1 for each document
            },
            "SUM": {
                "mongodb": "$sum",
                "stage": "$group",
                "type": "aggregate",
                "description": "Sum numeric values",
            },
            "AVG": {
                "mongodb": "$avg",
                "stage": "$group",
                "type": "aggregate",
                "description": "Calculate average of numeric values",
            },
            "MIN": {
                "mongodb": "$min",
                "stage": "$group",
                "type": "aggregate",
                "description": "Find minimum value",
            },
            "MAX": {
                "mongodb": "$max",
                "stage": "$group",
                "type": "aggregate",
                "description": "Find maximum value",
            },
            "FIRST": {
                "mongodb": "$first",
                "stage": "$group",
                "type": "aggregate",
                "description": "Get first value in group",
            },
            "LAST": {
                "mongodb": "$last",
                "stage": "$group",
                "type": "aggregate",
                "description": "Get last value in group",
            },
            "STDDEV": {
                "mongodb": "$stdDevPop",
                "stage": "$group",
                "type": "aggregate",
                "description": "Calculate standard deviation",
            },
            "STDDEV_POP": {
                "mongodb": "$stdDevPop",
                "stage": "$group",
                "type": "aggregate",
                "description": "Calculate population standard deviation",
            },
            "STDDEV_SAMP": {
                "mongodb": "$stdDevSamp",
                "stage": "$group",
                "type": "aggregate",
                "description": "Calculate sample standard deviation",
            },
            "VAR_POP": {
                "mongodb": "$stdDevPop",  # Placeholder - actual logic in core translator
                "stage": "$group",
                "type": "aggregate",
                "description": "Calculate population variance",
            },
            "VAR_SAMP": {
                "mongodb": "$stdDevSamp",  # Placeholder - actual logic in core translator
                "stage": "$group",
                "type": "aggregate",
                "description": "Calculate sample variance",
            },
            "GROUP_CONCAT": {
                "mongodb": "$push",
                "stage": "$group",
                "type": "aggregate",
                "description": "Concatenate values from multiple rows",
                "post_process": "join_array",
            },
            "BIT_AND": {
                "mongodb": "$bitAnd",
                "stage": "$group",
                "type": "aggregate",
                "description": "Bitwise AND operation on all values",
            },
            "BIT_OR": {
                "mongodb": "$bitOr",
                "stage": "$group",
                "type": "aggregate",
                "description": "Bitwise OR operation on all values",
            },
            "BIT_XOR": {
                "mongodb": "$bitXor",
                "stage": "$group",
                "type": "aggregate",
                "description": "Bitwise XOR operation on all values",
            },
            "VARIANCE": {
                "mongodb": "$stdDevPop",
                "stage": "$group",
                "type": "aggregate",
                "description": "Calculate variance (using stddev squared)",
                "transform": "square",  # Special handling needed
            },
        }

    def map_function(
        self, function_name: str, field: str = None, args: List[Any] = None
    ) -> Dict[str, Any]:
        """Map SQL aggregate function to MongoDB aggregation operator"""
        func_upper = function_name.upper()

        if func_upper not in self.function_map:
            raise ValueError(f"Unsupported aggregate function: {function_name}")

        # VAR_POP and VAR_SAMP are handled by core translator's _translate_statistical_aggregate
        if func_upper in ["VAR_POP", "VAR_SAMP"]:
            raise ValueError(
                f"Statistical aggregate function {function_name} handled by core translator"
            )

        mapping = self.function_map[func_upper]

        # Handle COUNT special cases
        if func_upper == "COUNT":
            if field == "*" or field is None:
                # COUNT(*) - count all documents
                return {
                    "operator": mapping["mongodb"],
                    "value": mapping.get("default_value", 1),
                    "stage": mapping["stage"],
                }
            else:
                # COUNT(field) - count non-null values
                return {
                    "operator": "$sum",
                    "value": {"$cond": [{"$ne": [f"${field}", None]}, 1, 0]},
                    "stage": mapping["stage"],
                }

        # Handle GROUP_CONCAT special case
        if func_upper == "GROUP_CONCAT":
            if field:
                return {
                    "operator": mapping["mongodb"],
                    "value": f"${field}",
                    "stage": mapping["stage"],
                    "post_process": mapping.get("post_process"),
                    "separator": ",",  # Default separator
                }

        # Handle STDDEV functions with simple operators
        if func_upper in ["STDDEV_POP", "STDDEV_SAMP", "STDDEV"]:
            if field:
                return {
                    "operator": mapping["mongodb"],  # Simple $stdDevPop or $stdDevSamp
                    "value": f"${field}",
                    "stage": mapping["stage"],
                    "precision": 6,  # Mark for rounding to 6 decimal places
                }

        # Handle other aggregate functions
        if field:
            return {
                "operator": mapping["mongodb"],
                "value": f"${field}",
                "stage": mapping["stage"],
            }

        raise ValueError(f"Field required for aggregate function: {function_name}")

    def is_aggregate_function(self, function_name: str) -> bool:
        """Check if function is an aggregate function"""
        return function_name.upper() in self.function_map

    def get_supported_functions(self) -> List[str]:
        """Get list of supported aggregate functions"""
        return list(self.function_map.keys())
