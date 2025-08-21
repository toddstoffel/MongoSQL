"""
Window Function Mapper for MongoSQL

This module provides MongoDB expression mappings for window functions
that were previously working: NTILE, LAG, and LEAD.

Focus on maintaining compatibility with existing implementations
and fixing ordering issues.
"""

from typing import Dict, Any, Optional, List
from .window_types import WindowFunctionType


class WindowFunctionMapper:
    """Maps SQL window function names to MongoDB aggregation expressions"""

    def __init__(self):
        """Initialize window function mapper with working functions"""
        self.function_map = {
            "ROW_NUMBER": self._map_row_number,
            "RANK": self._map_rank,
            "DENSE_RANK": self._map_dense_rank,
            "NTILE": self._map_ntile,
            "LAG": self._map_lag,
            "LEAD": self._map_lead,
        }

    def get_function_mapping(
        self, function_name: str, args: Optional[List] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get MongoDB expression for a window function

        Args:
            function_name: SQL function name (e.g., 'NTILE', 'LAG', 'LEAD')
            args: Function arguments if any

        Returns:
            MongoDB aggregation expression or None if function not supported
        """
        function_name_upper = function_name.upper()

        if function_name_upper in self.function_map:
            mapper_func = self.function_map[function_name_upper]
            return mapper_func(args)

        return None

    def is_window_function(self, function_name: str) -> bool:
        """Check if a function name is a supported window function"""
        return function_name.upper() in self.function_map

    def get_supported_functions(self) -> List[str]:
        """Get list of all supported window function names"""
        return list(self.function_map.keys())

    # Individual function mappers for working functions

    def _map_row_number(self, args: Optional[List] = None) -> Dict[str, Any]:
        """Map ROW_NUMBER() to MongoDB expression using $documentNumber"""
        # ROW_NUMBER() takes no arguments
        return {"$documentNumber": {}}

    def _map_rank(self, args: Optional[List] = None) -> Dict[str, Any]:
        """Map RANK() to MongoDB expression using $rank"""
        # RANK() takes no arguments
        return {"$rank": {}}

    def _map_dense_rank(self, args: Optional[List] = None) -> Dict[str, Any]:
        """Map DENSE_RANK() to MongoDB expression using $denseRank"""
        # DENSE_RANK() takes no arguments
        return {"$denseRank": {}}

    def _map_ntile(self, args: Optional[List] = None) -> Dict[str, Any]:
        """
        Map NTILE(n) to MongoDB expression using $bucketAuto

        This was one of the working functions - use $bucketAuto approach
        as specified for NTILE window functions
        """
        if args and len(args) > 0:
            n_buckets = args[0]
            # Ensure it's a positive integer
            try:
                n_buckets = int(n_buckets)
                if n_buckets > 0:
                    # Use $bucketAuto for NTILE as specified
                    return {
                        "$bucketAuto": {
                            "groupBy": "$_id",  # Will be replaced with proper grouping field
                            "buckets": n_buckets,
                        }
                    }
            except (ValueError, TypeError):
                pass

        # Default to quartiles if no valid argument
        return {"$bucketAuto": {"groupBy": "$_id", "buckets": 4}}

    def _map_lag(self, args: Optional[List] = None) -> Dict[str, Any]:
        """
        Map LAG(field, offset, default) to MongoDB expression using $shift

        This was one of the working functions - preserve its behavior
        """
        if not args or len(args) == 0:
            return {"$literal": None}

        field_name = args[0]
        offset = args[1] if len(args) > 1 else 1
        default_value = args[2] if len(args) > 2 else None

        # Build LAG expression using $shift with negative offset
        lag_expr = {
            "$shift": {
                "output": f"${field_name}",
                "by": -int(offset) if isinstance(offset, (int, str)) else -1,
            }
        }

        # Add default value if provided
        if default_value is not None:
            lag_expr["$shift"]["default"] = default_value

        return lag_expr

    def _map_lead(self, args: Optional[List] = None) -> Dict[str, Any]:
        """
        Map LEAD(field, offset, default) to MongoDB expression using $shift

        This was one of the working functions - preserve its behavior
        """
        if not args or len(args) == 0:
            return {"$literal": None}

        field_name = args[0]
        offset = args[1] if len(args) > 1 else 1
        default_value = args[2] if len(args) > 2 else None

        # Build LEAD expression using $shift with positive offset
        lead_expr = {
            "$shift": {
                "output": f"${field_name}",
                "by": int(offset) if isinstance(offset, (int, str)) else 1,
            }
        }

        # Add default value if provided
        if default_value is not None:
            lead_expr["$shift"]["default"] = default_value

        return lead_expr

    def validate_function_call(
        self, function_name: str, args: Optional[List] = None
    ) -> bool:
        """
        Validate that a window function call has correct arguments

        Args:
            function_name: SQL function name
            args: Function arguments

        Returns:
            True if function call is valid, False otherwise
        """
        function_name_upper = function_name.upper()

        if function_name_upper in ["ROW_NUMBER", "RANK", "DENSE_RANK"]:
            # These functions take no arguments
            return args is None or len(args) == 0

        elif function_name_upper == "NTILE":
            # NTILE(n) requires exactly one positive integer argument
            if args and len(args) == 1:
                try:
                    n = int(args[0])
                    return n > 0
                except (ValueError, TypeError):
                    return False
            return False

        elif function_name_upper in ["LAG", "LEAD"]:
            # LAG/LEAD require at least one argument (field name)
            return args is not None and len(args) >= 1

        return False
