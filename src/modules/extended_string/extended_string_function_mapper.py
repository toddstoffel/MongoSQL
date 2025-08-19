"""
Extended String Function Mapper

This module provides the main interface for extended string function processing.
Coordinates between parsing and translation following the modular architecture.
"""

from typing import Any, Dict, List, Optional, Union
from .extended_string_parser import ExtendedStringParser
from .extended_string_translator import ExtendedStringTranslator
from .extended_string_types import (
    ExtendedStringOperation,
    ExtendedStringOperationType,
    is_extended_string_function,
    get_extended_string_function_info,
)
from ...utils.helpers import process_function_argument


class ExtendedStringFunctionMapper:
    """Main mapper for extended string functions"""

    def __init__(self):
        self.parser = ExtendedStringParser()
        self.translator = ExtendedStringTranslator()

        # Function name mappings (case-insensitive)
        self.function_mappings = {
            "CONCAT_WS": ExtendedStringOperationType.CONCAT_WS,
            "REGEXP_SUBSTR": ExtendedStringOperationType.REGEXP_SUBSTR,
            "FORMAT": ExtendedStringOperationType.FORMAT,
            "SOUNDEX": ExtendedStringOperationType.SOUNDEX,
            "HEX": ExtendedStringOperationType.HEX,
            "UNHEX": ExtendedStringOperationType.UNHEX,
            "BIN": ExtendedStringOperationType.BIN,
        }

    def map_extended_string_function(
        self, function_name: str, args: List[Any]
    ) -> Dict[str, Any]:
        """Main entry point for mapping extended string functions"""
        function_name_upper = function_name.upper()

        if not self.is_extended_string_function(function_name_upper):
            raise ValueError(f"Unsupported extended string function: {function_name}")

        try:
            # Process arguments to handle field references vs literals
            processed_args = [process_function_argument(arg) for arg in args]

            # Get function mapping info
            function_info = get_extended_string_function_info(function_name_upper)
            if not function_info:
                raise ValueError(f"No mapping found for function: {function_name}")

            # Parse the function call into operation object
            operation = self.parser.parse_extended_string_function(
                function_name, processed_args, function_info
            )

            if not operation:
                raise ValueError(f"Failed to parse function: {function_name}")

            # Translate operation to MongoDB expression
            mongodb_expression = self.translator.translate(operation)

            return mongodb_expression

        except Exception as e:
            # Return error expression that will be visible in output
            return {"$literal": f"Function {function_name} error: {str(e)}"}

    def is_extended_string_function(self, function_name: str) -> bool:
        """Check if function is an extended string function"""
        return is_extended_string_function(function_name)

    def get_supported_functions(self) -> List[str]:
        """Get list of supported extended string function names"""
        return list(self.function_mappings.keys())

    def get_function_info(self, function_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a function"""
        return get_extended_string_function_info(function_name)

    def validate_function_call(self, function_name: str, args: List[Any]) -> bool:
        """Validate that a function call has correct arguments"""
        function_info = self.get_function_info(function_name)
        if not function_info:
            return False

        min_args = function_info.get("min_args", 0)
        max_args = function_info.get("max_args")

        if len(args) < min_args:
            return False
        if max_args is not None and len(args) > max_args:
            return False

        return True

    def get_function_description(self, function_name: str) -> Optional[str]:
        """Get description of what a function does"""
        function_info = self.get_function_info(function_name)
        return function_info.get("description") if function_info else None

    def get_function_example(self, function_name: str) -> Optional[str]:
        """Get example usage of a function"""
        function_info = self.get_function_info(function_name)
        return function_info.get("example") if function_info else None
