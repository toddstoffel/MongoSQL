"""
Window Function Translator for MongoSQL

This module translates SQL window functions to MongoDB $setWindowFields operations.
Window functions require special pipeline handling, not simple expression mapping.
"""

from typing import Dict, List, Any, Optional
from .window_types import WindowFunction, WindowFunctionType
from .window_parser import WindowParser
from .window_function_mapper import WindowFunctionMapper


class WindowTranslator:
    """Translates SQL window functions to MongoDB aggregation pipeline stages"""

    def __init__(self):
        """Initialize the window function translator"""
        self.parser = WindowParser()
        self.function_mapper = WindowFunctionMapper()

    def translate_window_query(
        self, sql: str, base_collection: str
    ) -> List[Dict[str, Any]]:
        """
        Translate SQL query with window functions to MongoDB aggregation pipeline

        Args:
            sql: SQL query containing window functions
            base_collection: The collection to query

        Returns:
            MongoDB aggregation pipeline with $setWindowFields stages
        """
        window_info = self.parser.extract_window_function_info(sql)

        if not window_info.get("has_window_functions", False):
            return []

        # Build $setWindowFields stage
        set_window_fields_stage = self._build_set_window_fields_stage(window_info)

        if not set_window_fields_stage:
            return []

        return [set_window_fields_stage]

    def _build_set_window_fields_stage(
        self, window_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Build $setWindowFields stage from window function information

        Args:
            window_info: Window function details from parser

        Returns:
            MongoDB $setWindowFields stage or None if translation fails
        """
        function_name = window_info.get("function_name", "")
        arguments = window_info.get("arguments", [])
        order_by = window_info.get("order_by", [])

        # Get the MongoDB expression for this window function
        mongo_expr = self.function_mapper.get_function_mapping(function_name, arguments)
        if not mongo_expr:
            return None

        # Build sort specification from ORDER BY
        sort_spec = {}
        for order_clause in order_by:
            sort_spec[order_clause.field] = 1 if order_clause.direction == "ASC" else -1

        # Build $setWindowFields stage
        stage = {"$setWindowFields": {"output": {}}}

        # Add sortBy if we have ORDER BY clause
        if sort_spec:
            stage["$setWindowFields"]["sortBy"] = sort_spec

        # Add the window function output
        output_field = self._get_output_field_name(function_name)

        # Handle different window function types
        if function_name == "ROW_NUMBER":
            stage["$setWindowFields"]["output"][output_field] = {"$documentNumber": {}}
        elif function_name == "RANK":
            stage["$setWindowFields"]["output"][output_field] = {"$rank": {}}
        elif function_name == "DENSE_RANK":
            stage["$setWindowFields"]["output"][output_field] = {"$denseRank": {}}
        elif function_name == "NTILE":
            n_buckets = arguments[0] if arguments else 4
            stage["$setWindowFields"]["output"][output_field] = {
                "$ntile": int(n_buckets)
            }
        elif function_name == "LAG":
            if arguments:
                field_name = arguments[0]
                offset = arguments[1] if len(arguments) > 1 else 1
                default_value = arguments[2] if len(arguments) > 2 else None

                lag_expr = {"$shift": {"output": f"${field_name}", "by": -int(offset)}}
                if default_value is not None:
                    lag_expr["$shift"]["default"] = default_value

                stage["$setWindowFields"]["output"][output_field] = lag_expr
        elif function_name == "LEAD":
            if arguments:
                field_name = arguments[0]
                offset = arguments[1] if len(arguments) > 1 else 1
                default_value = arguments[2] if len(arguments) > 2 else None

                lead_expr = {"$shift": {"output": f"${field_name}", "by": int(offset)}}
                if default_value is not None:
                    lead_expr["$shift"]["default"] = default_value

                stage["$setWindowFields"]["output"][output_field] = lead_expr

        return stage

    def _get_output_field_name(self, function_name: str) -> str:
        """Get the output field name for a window function"""
        # Map function names to sensible output field names
        field_map = {
            "ROW_NUMBER": "row_num",
            "RANK": "rank_num",
            "DENSE_RANK": "dense_rank",
            "NTILE": "quartile",
            "LAG": "prev_credit",
            "LEAD": "next_credit",
        }
        return field_map.get(function_name, function_name.lower())

    def is_window_query(self, sql: str) -> bool:
        """Check if SQL query contains window functions"""
        return self.parser.has_window_functions(sql)

    def get_window_function_names(self, sql: str) -> List[str]:
        """Get list of window function names used in the query"""
        window_functions = self.parser.parse_sql(sql)
        return [wf.function_type.value for wf in window_functions]
