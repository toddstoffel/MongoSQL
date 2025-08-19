"""
Enhanced Aggregate Function Parser

This module parses SQL expressions to identify and extract enhanced aggregate functions
like GROUP_CONCAT, STDDEV, VAR, and bitwise aggregations.
"""

import re
from typing import List, Optional, Dict, Any
from sqlparse import parse, sql
import sqlparse.tokens as tokens

from .enhanced_aggregate_types import (
    EnhancedAggregateOperation,
    GroupConcatFunction,
    StatisticalFunction,
    BitwiseFunction,
    EnhancedAggregateFunctionType,
    is_enhanced_aggregate_function,
)


class EnhancedAggregateParser:
    """Parser for enhanced aggregate functions in SQL"""

    def __init__(self):
        self.supported_functions = [
            "GROUP_CONCAT",
            "STDDEV_POP",
            "STDDEV_SAMP",
            "VAR_POP",
            "VAR_SAMP",
            "BIT_AND",
            "BIT_OR",
            "BIT_XOR",
        ]

    def parse_sql(self, sql_query: str) -> List[EnhancedAggregateOperation]:
        """Parse SQL to find enhanced aggregate functions"""
        operations = []

        # Parse SQL
        parsed = parse(sql_query)[0]

        # Extract functions from different contexts
        operations.extend(self._extract_from_select(parsed))
        operations.extend(self._extract_from_having(parsed))

        return operations

    def _extract_from_select(self, parsed) -> List[EnhancedAggregateOperation]:
        """Extract enhanced aggregate functions from SELECT clause"""
        operations = []

        # Get all tokens as a list for easier processing
        all_tokens = [token for token in parsed.flatten()]

        # Find SELECT token and process from there
        select_index = -1
        for i, token in enumerate(all_tokens):
            if token.ttype is tokens.Keyword.DML and token.value.upper() == "SELECT":
                select_index = i
                break

        if select_index == -1:
            return operations

        # Look for function calls after SELECT until we hit FROM/WHERE/etc
        i = select_index + 1
        while i < len(all_tokens):
            token = all_tokens[i]

            # Stop at clause keywords
            if token.ttype is tokens.Keyword and token.value.upper() in [
                "FROM",
                "WHERE",
                "GROUP",
                "ORDER",
                "HAVING",
                "LIMIT",
            ]:
                break

            # Look for function names
            if (
                token.ttype is tokens.Name
                and token.value.upper() in self.supported_functions
                and i + 1 < len(all_tokens)
                and all_tokens[i + 1].value == "("
            ):

                # Found a function call - reconstruct it
                func_call = self._reconstruct_function_call(all_tokens, i)
                if func_call:
                    operation = self._parse_function_call(func_call, "SELECT")
                    if operation:
                        operations.append(operation)

            i += 1

        return operations

    def _reconstruct_function_call(
        self, all_tokens, func_start_index
    ) -> Optional[Dict[str, str]]:
        """Reconstruct a function call from tokens starting at func_start_index"""
        func_name = all_tokens[func_start_index].value.upper()

        # Start building the full call
        full_call_parts = [all_tokens[func_start_index].value]  # Function name

        # Add the opening parenthesis
        if (
            func_start_index + 1 < len(all_tokens)
            and all_tokens[func_start_index + 1].value == "("
        ):
            full_call_parts.append("(")

            # Count parentheses to find the matching closing one
            paren_count = 1
            i = func_start_index + 2

            while i < len(all_tokens) and paren_count > 0:
                token_value = all_tokens[i].value
                full_call_parts.append(token_value)

                if token_value == "(":
                    paren_count += 1
                elif token_value == ")":
                    paren_count -= 1

                i += 1

            if paren_count == 0:  # Found matching closing parenthesis
                full_call = "".join(full_call_parts)
                arguments = "".join(
                    full_call_parts[1:]
                )  # Everything after function name

                return {
                    "function_name": func_name,
                    "full_call": full_call,
                    "arguments": arguments,
                }

        return None

    def _extract_from_having(self, parsed) -> List[EnhancedAggregateOperation]:
        """Extract enhanced aggregate functions from HAVING clause"""
        operations = []

        # Find HAVING token
        having_found = False
        for token in parsed.flatten():
            if token.ttype is tokens.Keyword and token.value.upper() == "HAVING":
                having_found = True
                continue

            if (
                having_found
                and token.ttype is tokens.Keyword
                and token.value.upper() in ["ORDER", "LIMIT"]
            ):
                break

            if having_found and hasattr(token, "value"):
                # Look for function calls
                func_match = self._extract_function_from_token(token.value)
                if func_match:
                    operation = self._parse_function_call(func_match, "HAVING")
                    if operation:
                        operations.append(operation)

        return operations

    def _extract_function_from_token(
        self, token_value: str
    ) -> Optional[Dict[str, str]]:
        """Extract function call details from a token"""
        # Pattern to match function calls: FUNCTION_NAME(arguments)
        pattern = r"(\w+)\s*\("
        match = re.search(pattern, token_value, re.IGNORECASE)

        if match:
            func_name = match.group(1).upper()
            if func_name in self.supported_functions:
                # Extract the full function call
                start_pos = match.start()
                paren_count = 0
                end_pos = len(token_value)

                for i, char in enumerate(token_value[start_pos:], start_pos):
                    if char == "(":
                        paren_count += 1
                    elif char == ")":
                        paren_count -= 1
                        if paren_count == 0:
                            end_pos = i + 1
                            break

                full_call = token_value[start_pos:end_pos]
                return {
                    "function_name": func_name,
                    "full_call": full_call,
                    "arguments": full_call[len(func_name) :].strip(),
                }

        return None

    def _parse_function_call(
        self, func_info: Dict[str, str], context: str
    ) -> Optional[EnhancedAggregateOperation]:
        """Parse a specific function call into an operation"""
        func_name = func_info["function_name"]
        full_call = func_info["full_call"]
        arguments = func_info["arguments"]

        if func_name == "GROUP_CONCAT":
            return self._parse_group_concat(arguments, full_call, context)
        elif func_name in ["STDDEV_POP", "STDDEV_SAMP", "VAR_POP", "VAR_SAMP"]:
            return self._parse_statistical_function(
                func_name, arguments, full_call, context
            )
        elif func_name in ["BIT_AND", "BIT_OR", "BIT_XOR"]:
            return self._parse_bitwise_function(
                func_name, arguments, full_call, context
            )

        return None

    def _parse_group_concat(
        self, arguments: str, full_call: str, context: str
    ) -> Optional[EnhancedAggregateOperation]:
        """Parse GROUP_CONCAT function with all its options"""
        # Remove outer parentheses
        args_content = (
            arguments.strip()[1:-1]
            if arguments.startswith("(") and arguments.endswith(")")
            else arguments
        )

        # Initialize defaults
        field = ""
        separator = ","
        distinct = False
        order_by = None

        # Check for DISTINCT
        if "DISTINCT" in args_content.upper():
            distinct = True
            args_content = re.sub(
                r"\bDISTINCT\b", "", args_content, flags=re.IGNORECASE
            ).strip()

        # Check for SEPARATOR clause
        separator_match = re.search(
            r'\bSEPARATOR\s+[\'"]([^\'"]*)[\'"]', args_content, re.IGNORECASE
        )
        if separator_match:
            separator = separator_match.group(1)
            args_content = re.sub(
                r'\bSEPARATOR\s+[\'"][^\'"]*[\'"]',
                "",
                args_content,
                flags=re.IGNORECASE,
            ).strip()

        # Check for ORDER BY clause
        order_match = re.search(
            r"\bORDER\s+BY\s+(.+?)(?:\s+SEPARATOR|$)", args_content, re.IGNORECASE
        )
        if order_match:
            order_clause = order_match.group(1).strip()
            order_by = self._parse_order_by_clause(order_clause)
            args_content = re.sub(
                r"\bORDER\s+BY\s+.+?(?:\s+SEPARATOR|$)",
                "",
                args_content,
                flags=re.IGNORECASE,
            ).strip()

        # What's left should be the field name
        field = args_content.strip().rstrip(",").strip()

        if not field:
            return None

        group_concat_func = GroupConcatFunction(
            field=field,
            separator=separator,
            distinct=distinct,
            order_by=order_by,
            original_expression=full_call,
        )

        return EnhancedAggregateOperation(function=group_concat_func, context=context)

    def _parse_statistical_function(
        self, func_name: str, arguments: str, full_call: str, context: str
    ) -> Optional[EnhancedAggregateOperation]:
        """Parse statistical functions like STDDEV, VAR"""
        # Remove outer parentheses and extract field name
        args_content = (
            arguments.strip()[1:-1]
            if arguments.startswith("(") and arguments.endswith(")")
            else arguments
        )
        field = args_content.strip()

        if not field:
            return None

        func_type = EnhancedAggregateFunctionType(func_name)
        statistical_func = StatisticalFunction(
            function_type=func_type, field=field, original_expression=full_call
        )

        return EnhancedAggregateOperation(function=statistical_func, context=context)

    def _parse_bitwise_function(
        self, func_name: str, arguments: str, full_call: str, context: str
    ) -> Optional[EnhancedAggregateOperation]:
        """Parse bitwise functions like BIT_AND, BIT_OR, BIT_XOR"""
        # Remove outer parentheses and extract field name
        args_content = (
            arguments.strip()[1:-1]
            if arguments.startswith("(") and arguments.endswith(")")
            else arguments
        )
        field = args_content.strip()

        if not field:
            return None

        func_type = EnhancedAggregateFunctionType(func_name)
        bitwise_func = BitwiseFunction(
            function_type=func_type, field=field, original_expression=full_call
        )

        return EnhancedAggregateOperation(function=bitwise_func, context=context)

    def _parse_order_by_clause(self, order_clause: str) -> List[Dict[str, str]]:
        """Parse ORDER BY clause for GROUP_CONCAT"""
        order_items = []

        # Split by comma for multiple fields
        fields = [f.strip() for f in order_clause.split(",")]

        for field in fields:
            direction = "ASC"
            field_name = field

            # Check for ASC/DESC
            if field.upper().endswith(" DESC"):
                direction = "DESC"
                field_name = field[:-5].strip()
            elif field.upper().endswith(" ASC"):
                direction = "ASC"
                field_name = field[:-4].strip()

            order_items.append({"field": field_name, "direction": direction})

        return order_items

    def has_enhanced_aggregate_functions(self, sql_query: str) -> bool:
        """Check if SQL contains enhanced aggregate functions"""
        sql_upper = sql_query.upper()
        return any(func in sql_upper for func in self.supported_functions)
