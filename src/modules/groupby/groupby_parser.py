"""
GROUP BY parser for SQL to MongoDB translation
Handles parsing of GROUP BY clauses from SQL tokens
"""

import sqlparse
from sqlparse import tokens
from sqlparse.tokens import Keyword, Name, Number, Operator, Punctuation
from typing import List, Dict, Any
from .groupby_types import GroupByStructure, GroupByField, AggregateFunction


class GroupByParser:
    """Parser for GROUP BY clauses"""

    def parse_group_by_from_tokens(
        self, tokens: List, start_idx: int
    ) -> tuple[List[str], int]:
        """
        Parse GROUP BY clause from SQL tokens
        Returns tuple of (field_list, next_index)
        """
        i = start_idx
        group_by_tokens = []

        # Collect all tokens until we hit another keyword or end
        while i < len(tokens):
            token = tokens[i]

            # Stop at other SQL keywords
            if token.ttype is Keyword and token.value.upper() in [
                "HAVING",
                "ORDER BY",
                "LIMIT",
                "UNION",
                "EXCEPT",
                "INTERSECT",
            ]:
                break

            group_by_tokens.append(token)
            i += 1

        # Parse the GROUP BY fields
        fields = []
        if group_by_tokens:
            group_by_str = "".join(
                t.value
                for t in group_by_tokens
                if t.ttype is not sqlparse.tokens.Text.Whitespace
            )
            # Split by comma and clean up field names
            fields = [
                field.strip().strip("`\"'")
                for field in group_by_str.split(",")
                if field.strip()
            ]

        return fields, i

    def parse_group_by_structure(self, parsed_sql: Dict[str, Any]) -> GroupByStructure:
        """
        Parse complete GROUP BY structure from parsed SQL
        """
        group_fields = []
        aggregate_functions = []
        regular_columns = []

        # Extract GROUP BY fields
        group_by_fields = parsed_sql.get("group_by", [])
        for field in group_by_fields:
            group_fields.append(GroupByField(field_name=field))

        # Extract columns and categorize them
        columns = parsed_sql.get("columns", [])
        for col in columns:
            if isinstance(col, dict) and "function" in col:
                # This is an aggregate function
                func_name = col.get("function")
                func_arg = col.get("arg") or col.get("args_str", "*")
                alias = col.get("alias")  # Only use explicit aliases
                original_call = col.get("original_call", f"{func_name}({func_arg})")

                # For GROUP_CONCAT, extract just the field name from complex arguments
                if func_name == "GROUP_CONCAT":
                    field_name = self._extract_group_concat_field_name(func_arg)
                else:
                    field_name = func_arg

                aggregate_functions.append(
                    AggregateFunction(
                        function_name=func_name,
                        field_name=field_name,
                        alias=alias,
                        original_call=original_call,
                    )
                )
            else:
                # Regular column
                if isinstance(col, str):
                    regular_columns.append(col)
                elif isinstance(col, dict) and "name" in col:
                    regular_columns.append(col["name"])

        # Extract HAVING conditions
        having_conditions = parsed_sql.get("having")
        parsed_having = (
            self._parse_having_conditions(having_conditions)
            if having_conditions
            else None
        )

        return GroupByStructure(
            group_fields=group_fields,
            aggregate_functions=aggregate_functions,
            regular_columns=regular_columns,
            having_conditions=parsed_having,
        )

    def _extract_group_concat_field_name(self, args_str: str) -> str:
        """Extract just the field name from GROUP_CONCAT arguments"""
        # Handle simple cases first
        if not args_str or args_str == "*":
            return args_str

        # Extract field name before any keywords like ORDER BY, DISTINCT, SEPARATOR
        field = args_str.strip()

        # Remove DISTINCT if present
        if field.upper().startswith("DISTINCT"):
            field = field[8:].strip()  # Remove 'DISTINCT' and leading space

        # Find the first occurrence of ORDER BY or SEPARATOR
        order_by_pos = field.upper().find("ORDER BY")
        separator_pos = field.upper().find("SEPARATOR")

        # Find the earliest position where we need to stop
        stop_pos = len(field)
        if order_by_pos != -1:
            stop_pos = min(stop_pos, order_by_pos)
        if separator_pos != -1:
            stop_pos = min(stop_pos, separator_pos)

        # Extract field name up to that position
        field_name = field[:stop_pos].strip()

        return field_name if field_name else args_str

    def _parse_having_conditions(self, having_str: str) -> Dict[str, Any]:
        """
        Parse HAVING condition string into MongoDB match expression using token-based parsing

        Examples:
        - "SUM(creditLimit) > 100000" -> {"SUM(creditLimit)": {"$gt": 100000}}
        - "COUNT(*) > 5" -> {"COUNT(*)": {"$gt": 5}}
        - "AVG(amount) >= 50.0" -> {"AVG(amount)": {"$gte": 50.0}}
        """
        import sqlparse
        from sqlparse.tokens import Operator, Number, Name, Punctuation, Keyword

        # Parse the HAVING condition using sqlparse
        parsed = sqlparse.parse(having_str)[0]
        tokens = [
            token
            for token in parsed.flatten()
            if token.ttype is not sqlparse.tokens.Text.Whitespace
        ]

        if len(tokens) < 3:
            # Fallback for complex conditions
            return {"$expr": {"$literal": having_str}}

        # Extract function call, operator, and value from tokens
        function_call = ""
        operator = ""
        value_str = ""

        # Find the function call (everything up to the operator)
        i = 0
        while i < len(tokens) and tokens[i].ttype not in [
            Operator.Comparison,
            Operator,
        ]:
            function_call += tokens[i].value
            i += 1

        # Get the operator
        if i < len(tokens) and tokens[i].ttype in [Operator.Comparison, Operator]:
            operator = tokens[i].value.strip()
            i += 1

        # Get the value
        if i < len(tokens) and tokens[i].ttype in [Number.Integer, Number.Float]:
            value_str = tokens[i].value

        if not function_call or not operator or not value_str:
            # Fallback for parsing failures
            return {"$expr": {"$literal": having_str}}

        # Convert value to appropriate type
        if "." in value_str:
            value = float(value_str)
        else:
            value = int(value_str)

        # Map SQL operators to MongoDB operators
        operator_map = {
            ">": "$gt",
            ">=": "$gte",
            "<": "$lt",
            "<=": "$lte",
            "=": "$eq",
            "==": "$eq",
            "!=": "$ne",
            "<>": "$ne",
        }

        mongo_operator = operator_map.get(operator, "$eq")

        return {function_call.strip(): {mongo_operator: value}}
