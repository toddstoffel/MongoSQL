"""
Extended String Function Parser

This module parses SQL extended string function calls into structured operations.
Uses token-based parsing only (NO REGEX) following project guidelines.
"""

import sqlparse
from typing import Any, List, Optional, Dict
from .extended_string_types import (
    ExtendedStringOperation,
    ExtendedStringOperationType, 
    RegexPattern,
    FormatSpecification,
    get_extended_string_function_info
)


class ExtendedStringParser:
    """Parser for extended string functions using token-based parsing"""
    
    def __init__(self):
        self.function_map = {
            'CONCAT_WS': self._parse_concat_ws,
            'REGEXP_SUBSTR': self._parse_regexp_substr,
            'FORMAT': self._parse_format,
            'SOUNDEX': self._parse_soundex,
            'HEX': self._parse_hex,
            'UNHEX': self._parse_unhex,
            'BIN': self._parse_bin
        }
    
    def parse_extended_string_function(self, function_name: str, args: List[Any], 
                                     function_mapping: Dict[str, Any]) -> Optional[ExtendedStringOperation]:
        """Parse extended string function into operation object"""
        function_name_upper = function_name.upper()
        
        if function_name_upper not in self.function_map:
            return None
        
        # Validate argument count
        func_info = get_extended_string_function_info(function_name_upper)
        if func_info:
            min_args = func_info.get('min_args', 0)
            max_args = func_info.get('max_args')
            
            if len(args) < min_args:
                raise ValueError(f"{function_name} requires at least {min_args} arguments")
            if max_args is not None and len(args) > max_args:
                raise ValueError(f"{function_name} accepts at most {max_args} arguments")
        
        # Parse using specific function parser
        return self.function_map[function_name_upper](function_name, args, function_mapping)
    
    def _parse_concat_ws(self, function_name: str, args: List[Any], 
                        mapping: Dict[str, Any]) -> ExtendedStringOperation:
        """Parse CONCAT_WS function"""
        if len(args) < 2:
            raise ValueError("CONCAT_WS requires at least 2 arguments (separator + strings)")
        
        separator = self._parse_argument_value(args[0])
        string_args = [self._parse_argument_value(arg) for arg in args[1:]]
        
        return ExtendedStringOperation(
            operation_type=ExtendedStringOperationType.CONCAT_WS,
            function_name=function_name,
            arguments=string_args,
            separator=separator
        )
    
    def _parse_regexp_substr(self, function_name: str, args: List[Any],
                           mapping: Dict[str, Any]) -> ExtendedStringOperation:
        """Parse REGEXP_SUBSTR function"""
        if len(args) < 2:
            raise ValueError("REGEXP_SUBSTR requires at least 2 arguments (string, pattern)")
        
        target_string = self._parse_argument_value(args[0])
        pattern_str = self._parse_argument_value(args[1])
        
        # Optional position and occurrence parameters
        position = 1
        occurrence = 1
        
        if len(args) > 2:
            position = self._parse_argument_value(args[2])
        if len(args) > 3:
            occurrence = self._parse_argument_value(args[3])
        
        # Create regex pattern object
        regex_pattern = RegexPattern(pattern=pattern_str)
        
        return ExtendedStringOperation(
            operation_type=ExtendedStringOperationType.REGEXP_SUBSTR,
            function_name=function_name,
            arguments=[target_string, position, occurrence],
            regex_pattern=regex_pattern
        )
    
    def _parse_format(self, function_name: str, args: List[Any],
                     mapping: Dict[str, Any]) -> ExtendedStringOperation:
        """Parse FORMAT function"""
        if len(args) < 2:
            raise ValueError("FORMAT requires at least 2 arguments (number, decimal_places)")
        
        number = self._parse_argument_value(args[0])
        decimal_places = self._parse_argument_value(args[1])
        
        # Optional locale parameter
        locale = None
        if len(args) > 2:
            locale = self._parse_argument_value(args[2])
        
        format_spec = FormatSpecification(
            decimal_places=decimal_places,
            locale=locale,
            use_thousands_separator=True
        )
        
        return ExtendedStringOperation(
            operation_type=ExtendedStringOperationType.FORMAT,
            function_name=function_name,
            arguments=[number],
            format_spec=format_spec
        )
    
    def _parse_soundex(self, function_name: str, args: List[Any],
                      mapping: Dict[str, Any]) -> ExtendedStringOperation:
        """Parse SOUNDEX function"""
        if len(args) != 1:
            raise ValueError("SOUNDEX requires exactly 1 argument")
        
        target_string = self._parse_argument_value(args[0])
        
        return ExtendedStringOperation(
            operation_type=ExtendedStringOperationType.SOUNDEX,
            function_name=function_name,
            arguments=[target_string]
        )
    
    def _parse_hex(self, function_name: str, args: List[Any],
                  mapping: Dict[str, Any]) -> ExtendedStringOperation:
        """Parse HEX function"""
        if len(args) != 1:
            raise ValueError("HEX requires exactly 1 argument")
        
        target_string = self._parse_argument_value(args[0])
        
        return ExtendedStringOperation(
            operation_type=ExtendedStringOperationType.HEX,
            function_name=function_name,
            arguments=[target_string]
        )
    
    def _parse_unhex(self, function_name: str, args: List[Any],
                    mapping: Dict[str, Any]) -> ExtendedStringOperation:
        """Parse UNHEX function"""
        if len(args) != 1:
            raise ValueError("UNHEX requires exactly 1 argument")
        
        hex_string = self._parse_argument_value(args[0])
        
        return ExtendedStringOperation(
            operation_type=ExtendedStringOperationType.UNHEX,
            function_name=function_name,
            arguments=[hex_string]
        )
    
    def _parse_bin(self, function_name: str, args: List[Any],
                  mapping: Dict[str, Any]) -> ExtendedStringOperation:
        """Parse BIN function"""
        if len(args) != 1:
            raise ValueError("BIN requires exactly 1 argument")
        
        number = self._parse_argument_value(args[0])
        
        return ExtendedStringOperation(
            operation_type=ExtendedStringOperationType.BIN,
            function_name=function_name,
            arguments=[number]
        )
    
    def _parse_argument_value(self, arg: str) -> Any:
        """Parse individual argument value using token-based parsing"""
        if not isinstance(arg, str):
            return arg
        
        # Check if this is a quoted string that needs quote removal
        # Only strip whitespace if the string has quotes (raw SQL parsing)
        if (arg.strip().startswith("'") and arg.strip().endswith("'")) or (arg.strip().startswith('"') and arg.strip().endswith('"')):
            arg = arg.strip()  # Only strip if we're removing quotes
            return arg[1:-1]  # Remove quotes
        
        # For non-quoted strings, don't strip as they may already be processed
        # Handle numbers
        try:
            if '.' in arg:
                return float(arg)
            else:
                return int(arg)
        except ValueError:
            pass
        
        # Handle boolean and null
        if arg.lower() == 'true':
            return True
        elif arg.lower() == 'false':
            return False
        elif arg.lower() == 'null':
            return None
        
        # Field reference or literal (unquoted identifier)
        return arg
    
    def get_supported_functions(self) -> List[str]:
        """Get list of supported extended string function names"""
        return list(self.function_map.keys())
