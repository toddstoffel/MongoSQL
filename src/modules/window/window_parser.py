"""
Window Function Parser for MongoSQL

This module handles parsing of SQL window function syntax with OVER clauses.
Window functions have the structure: FUNCTION() OVER (ORDER BY col [ASC|DESC])
"""

import sqlparse
from sqlparse import tokens
from sqlparse.sql import Statement, Function, Identifier, IdentifierList
from typing import List, Dict, Any, Optional, Tuple
from .window_types import WindowFunction, WindowFunctionType, WindowSpec, OrderByClause


class WindowParser:
    """Parses SQL queries containing window functions with OVER clauses"""

    def __init__(self):
        """Initialize the window function parser"""
        self.window_functions = [
            "ROW_NUMBER",
            "RANK",
            "DENSE_RANK",
            "NTILE",
            "LAG",
            "LEAD",
            "FIRST_VALUE",
            "LAST_VALUE",
            "NTH_VALUE",
        ]

    def parse_sql(self, sql: str) -> List[WindowFunction]:
        """
        Parse SQL statement and extract window functions

        Args:
            sql: SQL statement containing window functions

        Returns:
            List of WindowFunction objects found in the query
        """
        parsed = sqlparse.parse(sql)[0]
        window_functions = []

        # Convert to token list for easier processing
        tokens_list = list(parsed.flatten())

        i = 0
        while i < len(tokens_list):
            token = tokens_list[i]

            # Look for window function names
            if (
                token.ttype is tokens.Name
                and token.value.upper() in self.window_functions
            ):

                window_func = self._parse_window_function(tokens_list, i)
                if window_func:
                    window_functions.append(window_func)

            i += 1

        return window_functions

    def _parse_window_function(
        self, tokens_list: List, start_idx: int
    ) -> Optional[WindowFunction]:
        """
        Parse a window function starting from the function name token

        Args:
            tokens_list: List of all tokens
            start_idx: Index of the function name token

        Returns:
            WindowFunction object or None if parsing fails
        """
        if start_idx >= len(tokens_list):
            return None

        func_name_token = tokens_list[start_idx]
        function_name = func_name_token.value.upper()

        try:
            function_type = WindowFunctionType(function_name)
        except ValueError:
            return None

        # Look for function arguments (between parentheses after function name)
        arguments = []
        i = start_idx + 1

        # Skip whitespace
        while i < len(tokens_list) and tokens_list[i].ttype in (
            tokens.Whitespace,
            tokens.Newline,
        ):
            i += 1

        # Look for opening parenthesis
        if i < len(tokens_list) and tokens_list[i].value == "(":
            i += 1
            paren_depth = 1
            arg_tokens = []

            while i < len(tokens_list) and paren_depth > 0:
                token = tokens_list[i]
                if token.value == "(":
                    paren_depth += 1
                elif token.value == ")":
                    paren_depth -= 1

                if paren_depth > 0:
                    arg_tokens.append(token)
                i += 1

            # Parse arguments from collected tokens
            if arg_tokens:
                arguments = self._parse_function_arguments(arg_tokens)

        # Look for OVER clause
        window_spec = self._parse_over_clause(tokens_list, i)

        return WindowFunction(
            function_type=function_type, arguments=arguments, window_spec=window_spec
        )

    def _parse_function_arguments(self, arg_tokens: List) -> List[Any]:
        """Parse function arguments from token list"""
        arguments = []
        current_arg = []

        for token in arg_tokens:
            if token.value == "," and token.ttype is tokens.Punctuation:
                if current_arg:
                    arg_value = self._tokens_to_value(current_arg)
                    if arg_value is not None:
                        arguments.append(arg_value)
                    current_arg = []
            elif token.ttype not in (tokens.Whitespace, tokens.Newline):
                current_arg.append(token)

        # Add last argument
        if current_arg:
            arg_value = self._tokens_to_value(current_arg)
            if arg_value is not None:
                arguments.append(arg_value)

        return arguments

    def _tokens_to_value(self, token_list: List) -> Any:
        """Convert token list to a single value"""
        if not token_list:
            return None

        # Join all token values
        value_str = "".join(token.value for token in token_list).strip()

        # Try to convert to appropriate type
        if value_str.isdigit():
            return int(value_str)
        elif value_str.replace(".", "").isdigit():
            return float(value_str)
        else:
            return value_str

    def _parse_over_clause(
        self, tokens_list: List, start_idx: int
    ) -> Optional[WindowSpec]:
        """
        Parse the OVER clause starting from the given index

        Args:
            tokens_list: List of all tokens
            start_idx: Index to start looking for OVER clause

        Returns:
            WindowSpec object or None if no OVER clause found
        """
        i = start_idx

        # Skip whitespace
        while i < len(tokens_list) and tokens_list[i].ttype in (
            tokens.Whitespace,
            tokens.Newline,
        ):
            i += 1

        # Look for OVER keyword
        if i >= len(tokens_list) or tokens_list[i].value.upper() != "OVER":
            return None

        i += 1

        # Skip whitespace
        while i < len(tokens_list) and tokens_list[i].ttype in (
            tokens.Whitespace,
            tokens.Newline,
        ):
            i += 1

        # Look for opening parenthesis
        if i >= len(tokens_list) or tokens_list[i].value != "(":
            return None

        i += 1
        paren_depth = 1
        over_tokens = []

        while i < len(tokens_list) and paren_depth > 0:
            token = tokens_list[i]
            if token.value == "(":
                paren_depth += 1
            elif token.value == ")":
                paren_depth -= 1

            if paren_depth > 0:
                over_tokens.append(token)
            i += 1

        # Parse the contents of the OVER clause
        return self._parse_window_spec(over_tokens)

    def _parse_window_spec(self, over_tokens: List) -> WindowSpec:
        """Parse window specification from OVER clause tokens"""
        order_by_clauses = []

        # Look for ORDER BY clause
        i = 0
        while i < len(over_tokens):
            token = over_tokens[i]

            if token.ttype is tokens.Keyword and token.value.upper() == "ORDER":

                # Look for BY keyword
                i += 1
                while i < len(over_tokens) and over_tokens[i].ttype in (
                    tokens.Whitespace,
                    tokens.Newline,
                ):
                    i += 1

                if (
                    i < len(over_tokens)
                    and over_tokens[i].ttype is tokens.Keyword
                    and over_tokens[i].value.upper() == "BY"
                ):

                    i += 1
                    order_by_clauses = self._parse_order_by_list(over_tokens, i)
                    break

            i += 1

        return WindowSpec(order_by=order_by_clauses)

    def _parse_order_by_list(
        self, tokens_list: List, start_idx: int
    ) -> List[OrderByClause]:
        """Parse ORDER BY field list"""
        order_clauses = []
        i = start_idx
        current_field = []
        current_direction = "ASC"

        while i < len(tokens_list):
            token = tokens_list[i]

            if token.value == "," and token.ttype is tokens.Punctuation:
                # End of current field
                if current_field:
                    field_name = "".join(t.value for t in current_field).strip()
                    order_clauses.append(OrderByClause(field_name, current_direction))
                    current_field = []
                    current_direction = "ASC"

            elif token.ttype is tokens.Keyword and token.value.upper() in (
                "ASC",
                "DESC",
            ):
                current_direction = token.value.upper()

            elif token.ttype not in (tokens.Whitespace, tokens.Newline):
                current_field.append(token)

            i += 1

        # Add last field
        if current_field:
            field_name = "".join(t.value for t in current_field).strip()
            order_clauses.append(OrderByClause(field_name, current_direction))

        return order_clauses

    def has_window_functions(self, sql: str) -> bool:
        """Check if SQL contains any window functions"""
        window_functions = self.parse_sql(sql)
        return len(window_functions) > 0

    def extract_window_function_info(self, sql: str) -> Dict[str, Any]:
        """
        Extract comprehensive window function information from SQL

        Returns:
            Dictionary with window function details for translation
        """
        window_functions = self.parse_sql(sql)

        if not window_functions:
            return {}

        # For now, handle single window function
        # TODO: Support multiple window functions in one query
        window_func = window_functions[0]

        return {
            "function_name": window_func.function_type.value,
            "arguments": window_func.arguments,
            "order_by": (
                window_func.window_spec.order_by if window_func.window_spec else []
            ),
            "has_window_functions": True,
        }
