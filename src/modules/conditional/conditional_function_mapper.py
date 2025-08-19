"""
Conditional function mapper for SQL to MongoDB conditional operations
Handles: IF, CASE WHEN, COALESCE, NULLIF
"""

from typing import Dict, List, Any, Optional
from . import ConditionalParser, ConditionalTranslator


class ConditionalFunctionMapper:
    """Maps SQL conditional functions to MongoDB aggregation operators"""

    def __init__(self):
        self.function_map = self._build_conditional_map()
        self.parser = ConditionalParser()
        self.translator = ConditionalTranslator()

    def _build_conditional_map(self) -> Dict[str, Dict[str, Any]]:
        """Build the conditional function mapping dictionary"""
        return {
            "IF": {
                "mongodb": "$cond",
                "type": "conditional",
                "description": "IF(condition, value_if_true, value_if_false)",
                "args": 3,
            },
            "CASE": {
                "mongodb": "$switch",
                "type": "conditional",
                "description": "CASE WHEN condition THEN result ... ELSE default END",
                "args": "variable",
            },
            "COALESCE": {
                "mongodb": "$ifNull",
                "type": "conditional",
                "description": "COALESCE(value1, value2, ...) - returns first non-null value",
                "args": "multiple",
            },
            "NULLIF": {
                "mongodb": "$cond",
                "type": "conditional",
                "description": "NULLIF(expr1, expr2) - returns null if expr1=expr2, else expr1",
                "args": 2,
            },
        }

    def map_function(
        self, function_name: str, args: List[Any] = None
    ) -> Dict[str, Any]:
        """Map SQL conditional function to MongoDB aggregation expression"""
        func_upper = function_name.upper()

        if func_upper not in self.function_map:
            raise ValueError(f"Unsupported conditional function: {function_name}")

        if not args:
            raise ValueError(f"Conditional function {function_name} requires arguments")

        # Use the mapper's translation methods based on function type
        if func_upper == "IF":
            return self._map_if_function(args)
        elif func_upper == "CASE":
            return self._map_case_function(args)
        elif func_upper == "COALESCE":
            return self._map_coalesce_function(args)
        elif func_upper == "NULLIF":
            return self._map_nullif_function(args)
        else:
            raise ValueError(f"Unknown conditional function: {function_name}")

    def _map_if_function(self, args: List[Any]) -> Dict[str, Any]:
        """Map IF(condition, value_if_true, value_if_false) to MongoDB $cond"""
        if len(args) != 3:
            raise ValueError("IF function requires exactly 3 arguments")

        condition, if_true, if_false = args

        return {
            "$cond": {
                "if": self._translate_condition(condition),
                "then": self._translate_value(if_true),
                "else": self._translate_value(if_false),
            }
        }

    def _map_case_function(self, args: List[Any]) -> Dict[str, Any]:
        """Map CASE WHEN expression to MongoDB $switch"""
        # CASE function args come as a single string with WHEN/THEN/ELSE clauses
        if len(args) != 1:
            raise ValueError("CASE function should have one args_str argument")

        case_expression = args[0]

        # Handle new argument format with type information
        if isinstance(case_expression, dict) and "value" in case_expression:
            case_expression = case_expression["value"]

        # Parse the CASE expression using conditional parser
        try:
            parsed_case = self.parser.parse_case_when(case_expression)
            # Use the main translate_conditional method
            return self.translator.translate_conditional(parsed_case)
        except Exception as e:
            raise ValueError(f"Error parsing CASE expression: {str(e)}")

    def _map_coalesce_function(self, args: List[Any]) -> Dict[str, Any]:
        """Map COALESCE(...) to MongoDB $ifNull chain"""
        if len(args) < 2:
            raise ValueError("COALESCE function requires at least 2 arguments")

        # Build nested $ifNull operations
        result = self._translate_value(args[-1])  # Start with the last argument

        for arg in reversed(args[:-1]):
            result = {"$ifNull": [self._translate_value(arg), result]}

        return result

    def _map_nullif_function(self, args: List[Any]) -> Dict[str, Any]:
        """Map NULLIF(expr1, expr2) to MongoDB $cond"""
        if len(args) != 2:
            raise ValueError("NULLIF function requires exactly 2 arguments")

        expr1, expr2 = args

        return {
            "$cond": {
                "if": {
                    "$eq": [self._translate_value(expr1), self._translate_value(expr2)]
                },
                "then": None,
                "else": self._translate_value(expr1),
            }
        }

    def _translate_condition(self, condition: Any) -> Dict[str, Any]:
        """Translate a condition to MongoDB boolean expression"""
        # Handle new argument format first
        if isinstance(condition, dict) and "type" in condition and "value" in condition:
            # Extract the actual condition string from the argument structure
            condition = condition["value"]

        if isinstance(condition, str):
            condition = condition.strip()

            # Handle simple comparison operators
            for op in [">=", "<=", "!=", "<>", ">", "<", "="]:
                if op in condition:
                    parts = condition.split(op)
                    if len(parts) == 2:
                        left = self._translate_value(parts[0].strip())
                        right = self._translate_value(parts[1].strip())

                        # Map SQL operators to MongoDB operators
                        mongo_op_map = {
                            "=": "$eq",
                            "!=": "$ne",
                            "<>": "$ne",
                            "<": "$lt",
                            "<=": "$lte",
                            ">": "$gt",
                            ">=": "$gte",
                        }

                        mongo_op = mongo_op_map.get(op, "$eq")
                        return {mongo_op: [left, right]}

            # Handle IS NULL / IS NOT NULL
            if condition.upper().endswith(" IS NULL"):
                field = condition[:-8].strip()
                return {"$eq": [self._translate_value(field), None]}
            elif condition.upper().endswith(" IS NOT NULL"):
                field = condition[:-12].strip()
                return {"$ne": [self._translate_value(field), None]}

            # Default: treat as field reference
            return self._translate_value(condition)

        else:
            # Already a MongoDB expression or other type
            return (
                condition
                if isinstance(condition, dict)
                else self._translate_value(condition)
            )

    def _translate_value(self, value: Any) -> Any:
        """Translate a value to MongoDB format"""
        if value is None:
            return None

        elif isinstance(value, (int, float, bool)):
            return value

        elif isinstance(value, dict):
            # Handle new argument format with type information
            if "type" in value and "value" in value:
                if value["type"] == "literal":
                    # This is a literal string value
                    return value["value"]
                elif value["type"] == "field_reference":
                    # This is a field reference
                    return f"${value['value']}"
                else:
                    # Unknown type, use value as-is
                    return value["value"]
            else:
                # Already a MongoDB expression
                return value

        elif isinstance(value, str):
            value = value.strip()

            # Handle NULL literal
            if value.upper() == "NULL":
                return None

            # Check if it's a string literal (quoted)
            if (value.startswith("'") and value.endswith("'")) or (
                value.startswith('"') and value.endswith('"')
            ):
                return value[1:-1]  # Remove quotes

            # Check if it's a numeric literal
            try:
                if "." in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                pass

            # Check if it looks like a field reference (alphanumeric with optional dots/underscores)
            # vs a literal string value
            if self._is_likely_field_reference(value):
                return f"${value}"
            else:
                # Treat as literal string value
                return value

        else:
            # Convert to string and treat as field reference
            return f"${str(value)}"

    def _is_likely_field_reference(self, value: str) -> bool:
        """Determine if a string value is likely a field reference vs a literal"""
        # If the value contains comparison operators, it's likely a condition expression
        if any(op in value for op in [">", "<", "=", "!=", "<>", ">=", "<="]):
            return False

        # If it contains spaces and doesn't look like a simple field name, treat as literal
        if " " in value:
            return False

        # If it's a short string (3 chars or less), it could be either but lean towards literal
        if len(value) <= 3:
            return False

        # Simple heuristic: field names are usually:
        # - lowercase with underscores (user_id, created_at)
        # - camelCase (userId, createdAt)
        # - contain dots for nested fields (address.city)

        # Check for common field patterns
        has_underscore = "_" in value
        has_dot = "." in value
        is_camelcase = (
            value[0].islower()
            and any(c.isupper() for c in value[1:])
            and value.replace("_", "").replace(".", "").isalnum()
        )
        is_lowercase_with_underscores = (
            value.islower() and value.replace("_", "").replace(".", "").isalnum()
        )

        return (
            has_underscore or has_dot or is_camelcase or is_lowercase_with_underscores
        )

    def get_supported_functions(self) -> List[str]:
        """Get list of supported conditional function names"""
        return list(self.function_map.keys())

    def is_conditional_function(self, function_name: str) -> bool:
        """Check if function is a conditional function"""
        return function_name.upper() in self.function_map

    def get_function_info(self, function_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a conditional function"""
        return self.function_map.get(function_name.upper())
