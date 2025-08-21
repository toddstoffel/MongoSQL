"""
SQL Parser for parsing MariaDB/MySQL syntax using proper token-based parsing
"""

import sqlparse
from sqlparse.sql import (
    Statement,
    IdentifierList,
    Identifier,
    Function,
    Where,
    Comparison,
)
from typing import List, Dict, Any, Optional
from ..modules.where import WhereParser
from sqlparse.tokens import (
    Keyword,
    Name,
    Number,
    String,
    Operator,
    Punctuation,
    Literal,
)
from typing import Dict, List, Any, Optional, Union
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from ..modules.joins.join_parser import JoinParser
from ..modules.joins.join_types import JoinOperation, JoinCondition, JoinType
from ..modules.subqueries import SubqueryParser


class TokenBasedSQLParser:
    """Parser for SQL statements using proper token-based parsing"""

    def __init__(self):
        """Initialize the token-based SQL parser"""
        self.where_parser = WhereParser()
        self.subquery_parser = SubqueryParser()

    def parse(self, sql: str) -> Dict[str, Any]:
        """Parse SQL statement and return structured data"""
        # Parse SQL using sqlparse
        parsed = sqlparse.parse(sql)[0]

        # Get statement type
        statement_type = self._get_statement_type(parsed)

        if statement_type == "SELECT":
            return self._parse_select(parsed)
        elif statement_type == "INSERT":
            return self._parse_insert(parsed)
        elif statement_type == "UPDATE":
            return self._parse_update(parsed)
        elif statement_type == "DELETE":
            return self._parse_delete(parsed)
        elif statement_type == "SHOW":
            return self._parse_show(parsed)
        elif statement_type == "USE":
            return self._parse_use(parsed)
        else:
            raise Exception(f"Unsupported SQL type: {statement_type}")

    def _get_statement_type(self, tokens):
        """Determine the type of SQL statement"""
        for token in tokens:
            if (
                token.ttype is sqlparse.tokens.Keyword.DML
                or token.ttype is sqlparse.tokens.Keyword
            ):
                token_value = token.value.upper()
                if token_value == "SELECT":
                    return "SELECT"
                elif token_value == "INSERT":
                    return "INSERT"
                elif token_value == "UPDATE":
                    return "UPDATE"
                elif token_value == "DELETE":
                    return "DELETE"

        raise Exception(
            f"Could not determine statement type from tokens: {[(t.ttype, t.value) for t in tokens[:5]]}"
        )

    def _parse_select(self, parsed: Statement) -> Dict[str, Any]:
        """Parse SELECT statement using sqlparse tokens"""
        result = {
            "type": "SELECT",
            "columns": [],
            "from": None,
            "where": None,
            "group_by": [],
            "having": None,
            "order_by": [],
            "limit": None,
            "offset": None,
            "joins": [],
            "distinct": False,
            "subqueries": [],
            "original_sql": str(parsed),
        }

        tokens = list(parsed.flatten())

        # Parse subqueries FIRST before other clauses process them as literals
        original_sql = str(parsed)
        if self.subquery_parser.has_subqueries(original_sql):
            result["subqueries"] = self.subquery_parser.extract_subqueries(original_sql)

        i = 0

        while i < len(tokens):
            token = tokens[i]

            if (
                token.ttype in (Keyword, Keyword.DML)
                and token.value.upper() == "SELECT"
            ):
                i = self._parse_select_clause(tokens, i + 1, result)
            elif token.ttype is Keyword and token.value.upper() == "FROM":
                i = self._parse_from_clause(tokens, i + 1, result)
            elif token.ttype is Keyword and token.value.upper() == "WHERE":
                i = self._parse_where_clause(tokens, i + 1, result)
            elif token.ttype is Keyword and token.value.upper() == "GROUP BY":
                from ..modules.groupby.groupby_parser import GroupByParser

                groupby_parser = GroupByParser()
                fields, i = groupby_parser.parse_group_by_from_tokens(tokens, i + 1)
                result["group_by"] = fields
            elif token.ttype is Keyword and token.value.upper() == "HAVING":
                i = self._parse_having_clause(tokens, i + 1, result)
            elif token.ttype is Keyword and token.value.upper() in [
                "ORDER BY",
                "ORDER",
            ]:
                i = self._parse_order_clause(tokens, i, result)
            elif token.ttype is Keyword and token.value.upper() == "LIMIT":
                i = self._parse_limit_clause(tokens, i + 1, result)
            elif token.ttype is Keyword and "JOIN" in token.value.upper():
                i = self._parse_join_clause(tokens, i, result)
            else:
                i += 1

        return result

    def _parse_select_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse SELECT column list"""
        i = start_idx
        columns = []
        current_column_tokens = []
        paren_depth = 0

        while i < len(tokens):
            token = tokens[i]

            # Track parentheses depth
            if token.ttype is Punctuation and token.value == "(":
                paren_depth += 1
            elif token.ttype is Punctuation and token.value == ")":
                paren_depth -= 1

            # Stop at FROM keyword only if not inside parentheses
            if (
                token.ttype is Keyword
                and token.value.upper() == "FROM"
                and paren_depth == 0
            ):
                break

            # Handle DISTINCT only at top level (not inside function parentheses)
            if (
                token.ttype is Keyword
                and token.value.upper() == "DISTINCT"
                and paren_depth == 0
            ):
                result["distinct"] = True
                i += 1
                continue

            # Track parentheses depth
            if token.ttype is Punctuation and token.value == "(":
                paren_depth += 1
            elif token.ttype is Punctuation and token.value == ")":
                paren_depth -= 1

            # Handle column separators (commas) - only split at top level
            if token.ttype is Punctuation and token.value == "," and paren_depth == 0:
                if current_column_tokens:
                    # Join tokens with proper spacing
                    column_str = self._reconstruct_column_from_tokens(
                        current_column_tokens
                    )
                    columns.append(column_str)
                    current_column_tokens = []
                i += 1
                continue

            # Collect all non-whitespace tokens for the column
            if token.ttype is not sqlparse.tokens.Text.Whitespace:
                current_column_tokens.append(token)
            elif current_column_tokens:  # Only add space if we have content
                # Add a space token to preserve spacing
                current_column_tokens.append(token)

            i += 1

        # Add final column if exists
        if current_column_tokens:
            column_str = self._reconstruct_column_from_tokens(current_column_tokens)
            columns.append(column_str)

        result["columns"] = columns
        return i

    def _reconstruct_column_from_tokens(self, tokens: List) -> str:
        """Reconstruct column string from tokens with proper spacing"""
        if not tokens:
            return ""

        result_parts = []
        for i, token in enumerate(tokens):
            if token.ttype is sqlparse.tokens.Text.Whitespace:
                # Only add single space, not the actual whitespace content
                if result_parts and not result_parts[-1].endswith(" "):
                    result_parts.append(" ")
            else:
                result_parts.append(token.value)

        column_str = "".join(result_parts).strip()

        # Check if this is a CASE expression
        if column_str.upper().startswith("CASE ") and " END" in column_str.upper():
            return self._parse_case_expression(column_str)

        # Check if this is a function call and parse it
        if "(" in column_str and ")" in column_str:
            return self._parse_function_column(column_str)

        return column_str

    def _parse_function_column(self, column_str: str) -> Dict[str, Any]:
        """Parse a function call column using proper token-based parsing"""
        # Parse the column string using sqlparse to get proper tokens
        try:
            parsed = sqlparse.parse(column_str)[0]
            function_token = None

            # Look for Function tokens in the parsed result
            for token in parsed.flatten():
                if hasattr(token, "get_name") and hasattr(token, "get_parameters"):
                    function_token = token
                    break
                elif str(type(token).__name__) == "Function":
                    function_token = token
                    break

            if function_token:
                func_name = function_token.get_name().upper()
                parameters = function_token.get_parameters()
                args_str = str(parameters).strip() if parameters else ""

                # Remove extra parentheses if present
                if args_str.startswith("(") and args_str.endswith(")"):
                    args_str = args_str[1:-1].strip()

                column_info = {
                    "function": func_name,
                    "args_str": args_str,
                    "original_call": column_str,
                }
                return column_info

        except Exception:
            # Fall back to manual parsing if sqlparse fails
            pass

        # Manual parsing with proper parentheses handling
        func_match = None
        for i, char in enumerate(column_str):
            if char == "(" and column_str[:i].strip():
                func_name = column_str[:i].strip().upper()
                start_paren = i
                break
        else:
            return column_str  # Not a function call

        # Find matching closing parenthesis
        paren_count = 0
        end_paren = -1

        for i in range(start_paren, len(column_str)):
            if column_str[i] == "(":
                paren_count += 1
            elif column_str[i] == ")":
                paren_count -= 1
                if paren_count == 0:
                    end_paren = i
                    break

        if end_paren == -1:
            return column_str  # Malformed function call

        # Extract arguments between the parentheses
        args_str = column_str[start_paren + 1 : end_paren].strip()

        # Check for window function (OVER clause) after the function
        remaining = column_str[end_paren + 1 :].strip()
        window_spec = None
        alias = None

        if remaining.upper().startswith("OVER"):
            # This is a window function - parse the OVER clause
            over_start = remaining.upper().find("OVER")
            over_part = remaining[over_start:]

            # Find the OVER clause parentheses
            if "(" in over_part and ")" in over_part:
                paren_start = over_part.find("(")
                paren_count = 0
                paren_end = -1

                for i in range(paren_start, len(over_part)):
                    if over_part[i] == "(":
                        paren_count += 1
                    elif over_part[i] == ")":
                        paren_count -= 1
                        if paren_count == 0:
                            paren_end = i
                            break

                if paren_end != -1:
                    # Extract window specification
                    window_spec = over_part[paren_start + 1 : paren_end].strip()

                    # Check for alias after the OVER clause
                    after_over = over_part[paren_end + 1 :].strip()
                    if after_over.upper().startswith("AS "):
                        alias = after_over[3:].strip()
                    elif after_over and not after_over.upper().startswith("FROM"):
                        alias = after_over.strip()
        else:
            # Regular function - check for alias
            if remaining.upper().startswith("AS "):
                alias = remaining[3:].strip()
            elif " " in remaining and not remaining.upper().startswith("FROM"):
                alias = remaining.strip()

        column_info = {
            "function": func_name,
            "args_str": args_str,
            "original_call": column_str,
        }

        if window_spec is not None:
            column_info["window_spec"] = window_spec
            column_info["is_window_function"] = True

        if alias:
            column_info["alias"] = alias

        return column_info

    def _parse_case_expression(self, case_str: str) -> Dict[str, Any]:
        """Parse a CASE WHEN expression into structured format"""
        # Extract alias if present
        alias = None
        case_str = case_str.strip()

        # Find the position of END keyword (case-insensitive)
        case_upper = case_str.upper()
        end_pos = case_upper.find(" END")
        if end_pos != -1:
            # Check if there's content after END (like an alias)
            after_end = case_str[end_pos + 4 :].strip()
            if after_end.upper().startswith("AS "):
                alias = after_end[3:].strip()
            elif after_end and not after_end.upper().startswith("FROM"):
                alias = after_end.strip()

            # Extract just the CASE...END part
            case_expression = case_str[: end_pos + 4]
        else:
            case_expression = case_str

        # Remove CASE and END keywords from the expression part
        expr_content = case_expression.strip()
        if expr_content.upper().startswith("CASE"):
            expr_content = expr_content[4:].strip()
        if expr_content.upper().endswith("END"):
            expr_content = expr_content[:-3].strip()

        # Parse using sqlparse tokens for proper handling
        parsed = sqlparse.parse(f"CASE {expr_content} END")[0]
        tokens = list(parsed.flatten())

        when_clauses = []
        else_clause = None
        current_when = None
        current_then = None
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == "WHEN":
                # Start new WHEN clause
                if current_when is not None and current_then is not None:
                    when_clauses.append(
                        {
                            "condition": current_when.strip(),
                            "value": current_then.strip(),
                        }
                    )
                current_when = ""
                current_then = None
                i += 1
                continue

            elif (
                token.ttype is sqlparse.tokens.Keyword and token.value.upper() == "THEN"
            ):
                # Start collecting THEN value
                current_then = ""
                i += 1
                continue

            elif (
                token.ttype is sqlparse.tokens.Keyword and token.value.upper() == "ELSE"
            ):
                # Save current WHEN clause if exists
                if current_when is not None and current_then is not None:
                    when_clauses.append(
                        {
                            "condition": current_when.strip(),
                            "value": current_then.strip(),
                        }
                    )
                # Start collecting ELSE value
                else_clause = ""
                current_when = None
                current_then = None
                i += 1
                continue

            elif token.ttype is sqlparse.tokens.Keyword and token.value.upper() in [
                "CASE",
                "END",
            ]:
                # Skip CASE and END keywords
                i += 1
                continue

            elif token.ttype is not sqlparse.tokens.Text.Whitespace:
                # Collect content
                if else_clause is not None:
                    else_clause += token.value
                elif current_then is not None:
                    current_then += token.value
                elif current_when is not None:
                    current_when += token.value
            else:
                # Handle whitespace
                if else_clause is not None and else_clause:
                    else_clause += " "
                elif current_then is not None and current_then:
                    current_then += " "
                elif current_when is not None and current_when:
                    current_when += " "

            i += 1

        # Add final WHEN clause if exists
        if current_when is not None and current_then is not None:
            when_clauses.append(
                {"condition": current_when.strip(), "value": current_then.strip()}
            )

        # Convert CASE WHEN to function format for function mapper
        # Build args string that ConditionalFunctionMapper can understand
        args_parts = []
        for clause in when_clauses:
            args_parts.append(f"WHEN {clause['condition']} THEN {clause['value']}")

        if else_clause:
            args_parts.append(f"ELSE {else_clause.strip()}")

        args_str = " ".join(args_parts)

        result = {
            "function": "CASE",
            "args_str": args_str,
            "original_call": case_expression,
        }

        if alias:
            result["alias"] = alias

        return result

    def _parse_from_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse FROM table with optional alias"""
        i = start_idx
        table_parts = []

        while i < len(tokens):
            token = tokens[i]

            # Stop at keywords that end FROM clause
            if token.ttype is Keyword and (
                token.value.upper()
                in ["WHERE", "ORDER BY", "GROUP BY", "LIMIT", "HAVING"]
                or "JOIN" in token.value.upper()
            ):
                break

            # Skip whitespace
            if token.value.strip() == "":
                i += 1
                continue

            # Collect table name and potential alias
            if token.ttype is Name or token.ttype is None:
                table_parts.append(token.value.strip())

            i += 1

        if table_parts:
            result["from"] = table_parts[0]
            if len(table_parts) > 1:
                result["from_alias"] = table_parts[1]

        return i

    def _parse_join_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse JOIN clause"""
        i = start_idx

        # Get JOIN type from current token
        join_token = tokens[i]
        join_type = join_token.value.upper()

        # Move past JOIN keyword
        i += 1

        # Skip whitespace
        while i < len(tokens) and tokens[i].ttype is sqlparse.tokens.Text.Whitespace:
            i += 1

        # Get table name
        if i >= len(tokens):
            return i

        table_name = tokens[i].value
        i += 1

        # Skip whitespace
        while i < len(tokens) and tokens[i].ttype is sqlparse.tokens.Text.Whitespace:
            i += 1

        # Get table alias if present
        table_alias = None
        if (
            i < len(tokens)
            and tokens[i].ttype is sqlparse.tokens.Name
            and tokens[i].value.upper() != "ON"
        ):
            table_alias = tokens[i].value
            i += 1

        # Skip whitespace
        while i < len(tokens) and tokens[i].ttype is sqlparse.tokens.Text.Whitespace:
            i += 1

        # Expect ON keyword
        if (
            i < len(tokens)
            and tokens[i].ttype is Keyword
            and tokens[i].value.upper() == "ON"
        ):
            i += 1
            # Parse join condition
            condition_tokens = []
            while i < len(tokens):
                token = tokens[i]
                if token.ttype is Keyword and (
                    "JOIN" in token.value.upper()
                    or token.value.upper()
                    in ["WHERE", "ORDER", "ORDER BY", "LIMIT", "GROUP"]
                ):
                    break
                condition_tokens.append(token)
                i += 1

            # Build condition string
            condition = "".join(t.value for t in condition_tokens).strip()

            # Parse condition to create JoinCondition object
            join_condition = self._parse_join_condition(condition)

            # Map JOIN type string to enum
            join_type_map = {
                "INNER JOIN": JoinType.INNER,
                "LEFT JOIN": JoinType.LEFT,
                "RIGHT JOIN": JoinType.RIGHT,
                "FULL OUTER JOIN": JoinType.FULL,
                "CROSS JOIN": JoinType.CROSS,
            }

            join_type_enum = join_type_map.get(join_type, JoinType.INNER)

            # Create proper JoinOperation object
            join_operation = JoinOperation(
                join_type=join_type_enum,
                left_table=result.get("from", ""),  # Base table
                right_table=table_name,
                conditions=[join_condition] if join_condition else [],
                alias_left=result.get("from_alias"),
                alias_right=table_alias,
            )

            result["joins"].append(join_operation)

        return i

    def _parse_join_condition(self, condition_str: str) -> Optional[JoinCondition]:
        """Parse JOIN condition string into JoinCondition object"""
        if not condition_str or "=" not in condition_str:
            return None

        # Simple parsing for "table1.col1 = table2.col2" format
        parts = condition_str.split("=")
        if len(parts) != 2:
            return None

        left_part = parts[0].strip()
        right_part = parts[1].strip()

        # Parse left side
        if "." in left_part:
            left_table, left_column = left_part.split(".", 1)
        else:
            left_table, left_column = "", left_part

        # Parse right side
        if "." in right_part:
            right_table, right_column = right_part.split(".", 1)
        else:
            right_table, right_column = "", right_part

        return JoinCondition(
            left_table=left_table.strip(),
            left_column=left_column.strip(),
            right_table=right_table.strip(),
            right_column=right_column.strip(),
            operator="=",
        )

    def _parse_where_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse WHERE clause"""
        i = start_idx
        where_tokens = []

        while i < len(tokens):
            token = tokens[i]

            # Stop at keywords that end WHERE clause
            if token.ttype is Keyword and token.value.upper() in [
                "ORDER",
                "ORDER BY",
                "GROUP",
                "GROUP BY",
                "LIMIT",
                "HAVING",
            ]:
                break

            where_tokens.append(token)
            i += 1

        if where_tokens:
            where_str = "".join(t.value for t in where_tokens)
            result["where"] = self._parse_where_from_string(where_str.strip())

        return i

    def _parse_order_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse ORDER BY clause"""
        i = start_idx

        # Skip ORDER BY keyword (might be combined as "ORDER BY" or separate "ORDER" "BY")
        if tokens[i].value.upper() == "ORDER BY":
            # Combined token, move to next
            i += 1
        else:
            # Separate tokens, skip ORDER and BY
            while i < len(tokens) and tokens[i].value.upper() != "BY":
                i += 1
            i += 1  # Skip BY

        order_tokens = []
        while i < len(tokens):
            token = tokens[i]

            # Stop at LIMIT or other keywords
            if token.ttype is Keyword and token.value.upper() in [
                "LIMIT",
                "GROUP",
                "HAVING",
            ]:
                break

            order_tokens.append(token)
            i += 1

        if order_tokens:
            order_str = "".join(t.value for t in order_tokens)
            result["order_by"] = self._parse_order_by(order_str.strip())

        return i

    def _parse_limit_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse LIMIT clause"""
        i = start_idx

        # Skip whitespace
        while i < len(tokens) and tokens[i].ttype is sqlparse.tokens.Text.Whitespace:
            i += 1

        if (
            i < len(tokens)
            and tokens[i].ttype is sqlparse.tokens.Literal.Number.Integer
        ):
            limit_count = int(tokens[i].value)
            result["limit"] = {"count": limit_count}
            i += 1

        return i

    def _parse_where_from_string(self, where_str: str) -> Dict[str, Any]:
        """Parse WHERE clause from string using modular WHERE parser"""
        return self.where_parser.parse_where_string(where_str)

    def _parse_order_by(self, order_str: str) -> List[Dict[str, Any]]:
        """Parse ORDER BY clause - temporary until full token parsing"""
        # This is a simplified implementation
        # TODO: Replace with proper token-based parsing
        parts = order_str.split(",")
        order_list = []
        for part in parts:
            part = part.strip()
            if part.upper().endswith(" DESC"):
                field = part[:-5].strip()
                direction = "DESC"
            else:
                field = part.replace(" ASC", "").strip()
                direction = "ASC"
            order_list.append({"field": field, "direction": direction})
        return order_list

    def _parse_having_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse HAVING clause"""
        i = start_idx
        having_tokens = []

        # Collect all tokens until we hit another keyword or end
        while i < len(tokens):
            token = tokens[i]

            # Stop at other SQL keywords
            if token.ttype is Keyword and token.value.upper() in [
                "ORDER BY",
                "LIMIT",
                "UNION",
                "EXCEPT",
                "INTERSECT",
            ]:
                break

            having_tokens.append(token)
            i += 1

        # Parse the HAVING condition
        if having_tokens:
            having_str = "".join(t.value for t in having_tokens).strip()
            # For now, store as string - can be enhanced later with WHERE parser
            result["having"] = having_str

        return i

    # Placeholder methods for other statement types
    def _parse_insert(self, parsed: Statement) -> Dict[str, Any]:
        return {"type": "INSERT", "error": "Not implemented with token parsing yet"}

    def _parse_update(self, parsed: Statement) -> Dict[str, Any]:
        return {"type": "UPDATE", "error": "Not implemented with token parsing yet"}

    def _parse_delete(self, parsed: Statement) -> Dict[str, Any]:
        return {"type": "DELETE", "error": "Not implemented with token parsing yet"}

    def _parse_show(self, parsed: Statement) -> Dict[str, Any]:
        return {"type": "SHOW", "error": "Not implemented with token parsing yet"}

    def _parse_use(self, parsed: Statement) -> Dict[str, Any]:
        return {"type": "USE", "error": "Not implemented with token parsing yet"}

    # ========================================================================
    # ENHANCED PARSING METHODS - SAFE CORE EXTENSIONS (NON-BREAKING)
    # ========================================================================

    def parse_with_expressions(self, sql: str) -> Dict[str, Any]:
        """Enhanced parser that recognizes expression patterns like REGEXP

        This method extends existing parsing without modifying core logic.
        It first uses the standard parser, then enhances with expression recognition.
        """
        try:
            # First, use existing parser (no changes to existing logic)
            result = self.parse(sql)

            # Then, enhance with expression recognition
            if "columns" in result and isinstance(result["columns"], list):
                enhanced_columns = []
                has_regexp_expressions = False

                for col in result["columns"]:
                    if isinstance(col, str) and self._is_regexp_expression(col):
                        # Extract alias if present
                        alias = None
                        expression = col

                        # Check for AS alias
                        if " AS " in col.upper():
                            parts = col.rsplit(" AS ", 1)
                            if len(parts) == 2:
                                expression = parts[0].strip()
                                alias = parts[1].strip()

                        enhanced_columns.append(
                            {
                                "type": "regexp_expression",
                                "expression": expression,
                                "alias": alias,
                                "original": col,
                            }
                        )
                        has_regexp_expressions = True
                    else:
                        enhanced_columns.append(col)  # Keep original unchanged

                # Only add enhanced_columns if we found REGEXP expressions
                if has_regexp_expressions:
                    result["enhanced_columns"] = enhanced_columns
                    result["has_regexp_expressions"] = True

            return result

        except Exception:
            # If enhanced parsing fails, fallback to original parser
            return self.parse(sql)

    def _is_regexp_expression(self, expr: str) -> bool:
        """Check if expression contains REGEXP operators"""
        if not isinstance(expr, str):
            return False

        expr_upper = expr.upper()
        # Look for REGEXP operators with word boundaries
        regexp_patterns = [" REGEXP ", " RLIKE ", " NOT REGEXP "]
        return any(pattern in expr_upper for pattern in regexp_patterns)

    def has_enhanced_expressions(self, sql: str) -> bool:
        """Check if SQL contains expressions that benefit from enhancement"""
        return self._is_regexp_expression(sql)

    def get_enhanced_column_info(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract enhanced column information from parsed result"""
        return {
            "has_enhancements": parsed_result.get("has_regexp_expressions", False),
            "enhanced_columns": parsed_result.get("enhanced_columns", []),
            "original_columns": parsed_result.get("columns", []),
        }
