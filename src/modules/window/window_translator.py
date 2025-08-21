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
        self,
        sql: str,
        base_collection: str,
        parsed_columns: List[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Translate SQL query with window functions to MongoDB aggregation pipeline

        Args:
            sql: SQL query containing window functions
            base_collection: The collection to query
            parsed_columns: Pre-parsed column information with window functions

        Returns:
            MongoDB aggregation pipeline with $setWindowFields stages
        """
        # If we have parsed columns, use those directly
        if parsed_columns:
            window_columns = [
                col
                for col in parsed_columns
                if isinstance(col, dict) and col.get("is_window_function")
            ]
            if window_columns:
                return self._build_window_stages_from_columns(window_columns)

        # Fallback to original parser method
        window_info = self.parser.extract_window_function_info(sql)

        if not window_info.get("has_window_functions", False):
            return []

        # Build $setWindowFields stage
        set_window_fields_stage = self._build_set_window_fields_stage(window_info)

        if not set_window_fields_stage:
            return []

        return [set_window_fields_stage]

    def _build_window_stages_from_columns(
        self, window_columns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build $setWindowFields stage from parsed window function columns

        Args:
            window_columns: List of parsed columns with window function information

        Returns:
            MongoDB aggregation pipeline with $setWindowFields stages
        """
        stage = {"$setWindowFields": {"output": {}}}
        sort_spec = {}

        for col in window_columns:
            function_name = col.get("function", "").upper()
            # Handle both 'arguments' (list) and 'args_str' (string) formats
            arguments = col.get("arguments", [])
            if not arguments and col.get("args_str"):
                # Parse args_str like "creditLimit, 1" into ["creditLimit", "1"]
                args_str = col.get("args_str", "").strip()
                if args_str:
                    arguments = [arg.strip() for arg in args_str.split(",")]
            window_spec = col.get("window_spec", "")
            alias = col.get("alias", self._get_output_field_name(function_name))

            # Extract ORDER BY from window specification
            if "ORDER BY" in window_spec:
                order_by_part = window_spec.split("ORDER BY")[1].strip()
                # Parse "creditLimit DESC" format
                parts = order_by_part.strip().split()
                if len(parts) >= 1:
                    field_name = parts[0]
                    direction = (
                        1 if len(parts) == 1 or parts[1].upper() == "ASC" else -1
                    )
                    sort_spec[field_name] = direction

                    # Note: Cannot add secondary sort fields for window functions
                    # because $documentNumber requires exactly one element in sortBy

            # Build the window function expression
            if function_name == "ROW_NUMBER":
                stage["$setWindowFields"]["output"][alias] = {"$documentNumber": {}}
            elif function_name == "RANK":
                stage["$setWindowFields"]["output"][alias] = {"$rank": {}}
            elif function_name == "DENSE_RANK":
                stage["$setWindowFields"]["output"][alias] = {"$denseRank": {}}
            elif function_name == "NTILE":
                # NTILE will be handled specially in pipeline generation
                # Just add a placeholder that will be processed later
                n_buckets = int(arguments[0]) if arguments else 4
                stage["$setWindowFields"]["output"][alias] = {"$documentNumber": {}}
            elif function_name == "LAG":
                if arguments:
                    field_name = arguments[0]
                    offset = arguments[1] if len(arguments) > 1 else 1
                    default_value = arguments[2] if len(arguments) > 2 else None

                    lag_expr = {
                        "$shift": {"output": f"${field_name}", "by": -int(offset)}
                    }
                    if default_value is not None:
                        lag_expr["$shift"]["default"] = default_value

                    stage["$setWindowFields"]["output"][alias] = lag_expr
            elif function_name == "LEAD":
                if arguments:
                    field_name = arguments[0]
                    offset = arguments[1] if len(arguments) > 1 else 1
                    default_value = arguments[2] if len(arguments) > 2 else None

                    lead_expr = {
                        "$shift": {"output": f"${field_name}", "by": int(offset)}
                    }
                    if default_value is not None:
                        lead_expr["$shift"]["default"] = default_value

                    stage["$setWindowFields"]["output"][alias] = lead_expr

        # Add sortBy if we have ORDER BY clause(s)
        if sort_spec:
            stage["$setWindowFields"]["sortBy"] = sort_spec

        # Build pipeline with explicit sort first, then window fields
        pipeline = []
        has_ntile = False
        ntile_buckets = 4
        ntile_field = ""

        # Check for NTILE in window columns to handle specially
        for col in window_columns:
            function_name = col.get("function", "").upper()
            if function_name == "NTILE":
                has_ntile = True
                arguments = col.get("arguments", [])
                if not arguments and col.get("args_str"):
                    args_str = col.get("args_str", "").strip()
                    if args_str:
                        arguments = [arg.strip() for arg in args_str.split(",")]
                ntile_buckets = int(arguments[0]) if arguments else 4
                ntile_field = col.get("alias", "quartile")
                break

        if sort_spec:
            # Add explicit $sort stage before $setWindowFields
            pipeline.append({"$sort": sort_spec})

        if stage["$setWindowFields"]["output"]:
            if has_ntile:
                # For NTILE, we need a different approach using facet to get total count
                pipeline.extend(
                    [
                        {
                            "$facet": {
                                "data": [
                                    {
                                        "$setWindowFields": {
                                            "output": {
                                                ntile_field: {"$documentNumber": {}}
                                            },
                                            "sortBy": (
                                                sort_spec if sort_spec else {"_id": 1}
                                            ),
                                        }
                                    }
                                ],
                                "total": [{"$count": "count"}],
                            }
                        },
                        {"$unwind": "$data"},
                        {"$unwind": "$total"},
                        {
                            "$addFields": {
                                f"data.{ntile_field}": {
                                    "$ceil": {
                                        "$divide": [
                                            {
                                                "$multiply": [
                                                    f"$data.{ntile_field}",
                                                    ntile_buckets,
                                                ]
                                            },
                                            "$total.count",
                                        ]
                                    }
                                }
                            }
                        },
                        {"$replaceRoot": {"newRoot": "$data"}},
                    ]
                )
            else:
                pipeline.append(stage)

        return pipeline

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
