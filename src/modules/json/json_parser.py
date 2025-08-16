"""
JSON Function Parser

Parses SQL JSON function calls and extracts components for MongoDB translation.
Uses token-based parsing following project architecture principles.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
import sqlparse
from sqlparse.sql import Function, Identifier, Token
from sqlparse.tokens import Literal

from .json_types import (
    JSONOperation, JSONPath, JSONValue, JSONOperationType, 
    JSON_FUNCTION_MAPPINGS
)


class JSONParser:
    """Parses SQL JSON function calls into structured operations"""
    
    def __init__(self):
        self.supported_functions = set(JSON_FUNCTION_MAPPINGS.keys())
    
    def is_json_function(self, function_name: str) -> bool:
        """Check if function is a supported JSON function"""
        return function_name.upper() in self.supported_functions
    
    def parse_json_function(self, function_token: Function) -> Optional[JSONOperation]:
        """Parse JSON function token into JSONOperation"""
        if not isinstance(function_token, Function):
            return None
            
        function_name = function_token.get_name().upper()
        if not self.is_json_function(function_name):
            return None
            
        # Get function mapping
        mapping = JSON_FUNCTION_MAPPINGS[function_name]
        
        # Extract arguments
        args = self._extract_function_arguments(function_token)
        
        # Validate arguments
        if not mapping.validate_arguments(args):
            return None
            
        # Parse based on function type
        if function_name == 'JSON_EXTRACT':
            return self._parse_json_extract(function_name, args, mapping)
        elif function_name == 'JSON_OBJECT':
            return self._parse_json_object(function_name, args, mapping)
        elif function_name == 'JSON_ARRAY':
            return self._parse_json_array(function_name, args, mapping)
        elif function_name == 'JSON_UNQUOTE':
            return self._parse_json_unquote(function_name, args, mapping)
        elif function_name == 'JSON_KEYS':
            return self._parse_json_keys(function_name, args, mapping)
        elif function_name == 'JSON_LENGTH':
            return self._parse_json_length(function_name, args, mapping)
        else:
            # Generic parsing for other functions
            return JSONOperation(
                operation_type=mapping.operation_type,
                function_name=function_name,
                arguments=args
            )
    
    def _extract_function_arguments(self, function_token: Function) -> List[Any]:
        """Extract arguments from function token"""
        args = []
        
        # Get the parenthesis content
        for token in function_token.tokens:
            if token.ttype is None and str(token).strip().startswith('('):
                # Parse the content inside parentheses
                content = str(token).strip()[1:-1]  # Remove parentheses
                if content:
                    # Split by comma, handling nested structures
                    arg_tokens = self._split_function_arguments(content)
                    for arg in arg_tokens:
                        args.append(self._parse_argument_value(arg.strip()))
                break
                
        return args
    
    def _split_function_arguments(self, content: str) -> List[str]:
        """Split function arguments, handling nested parentheses and quotes"""
        args = []
        current_arg = ""
        paren_level = 0
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(content):
            char = content[i]
            
            if char in ['"', "'"] and not in_quotes:
                in_quotes = True
                quote_char = char
                current_arg += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                current_arg += char
            elif not in_quotes:
                if char == '(':
                    paren_level += 1
                    current_arg += char
                elif char == ')':
                    paren_level -= 1
                    current_arg += char
                elif char == ',' and paren_level == 0:
                    args.append(current_arg)
                    current_arg = ""
                else:
                    current_arg += char
            else:
                current_arg += char
            
            i += 1
        
        if current_arg:
            args.append(current_arg)
            
        return args
    
    def _parse_argument_value(self, arg: str) -> Any:
        """Parse individual argument value"""
        arg = arg.strip()
        
        # Handle string literals
        if (arg.startswith("'") and arg.endswith("'")) or (arg.startswith('"') and arg.endswith('"')):
            return arg[1:-1]  # Remove quotes
        
        # Handle JSON path expressions (start with $)
        if arg.startswith('$'):
            return arg
        
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
            
        # Handle field references (no quotes)
        return arg
    
    def _parse_json_extract(self, function_name: str, args: List[Any], mapping) -> JSONOperation:
        """Parse JSON_EXTRACT function"""
        if len(args) < 2:
            return None
            
        json_field = args[0]
        json_path_str = args[1]
        
        # Parse JSON path
        json_path = self._parse_json_path(json_path_str)
        
        return JSONOperation(
            operation_type=JSONOperationType.EXTRACT,
            function_name=function_name,
            arguments=args,
            json_path=json_path,
            target_field=json_field if isinstance(json_field, str) else None
        )
    
    def _parse_json_object(self, function_name: str, args: List[Any], mapping) -> JSONOperation:
        """Parse JSON_OBJECT function"""
        if len(args) % 2 != 0:
            return None
            
        # Keep arguments as flat list - translator will handle pairing
        return JSONOperation(
            operation_type=JSONOperationType.OBJECT,
            function_name=function_name,
            arguments=args  # Keep as flat list
        )
    
    def _parse_json_array(self, function_name: str, args: List[Any], mapping) -> JSONOperation:
        """Parse JSON_ARRAY function"""
        return JSONOperation(
            operation_type=JSONOperationType.ARRAY,
            function_name=function_name,
            arguments=args
        )
    
    def _parse_json_unquote(self, function_name: str, args: List[Any], mapping) -> JSONOperation:
        """Parse JSON_UNQUOTE function"""
        return JSONOperation(
            operation_type=JSONOperationType.UNQUOTE,
            function_name=function_name,
            arguments=args
        )
    
    def _parse_json_keys(self, function_name: str, args: List[Any], mapping) -> JSONOperation:
        """Parse JSON_KEYS function"""
        json_field = args[0]
        json_path = None
        
        if len(args) > 1:
            json_path = self._parse_json_path(args[1])
        
        return JSONOperation(
            operation_type=JSONOperationType.KEYS,
            function_name=function_name,
            arguments=args,
            json_path=json_path,
            target_field=json_field if isinstance(json_field, str) else None
        )
    
    def _parse_json_length(self, function_name: str, args: List[Any], mapping) -> JSONOperation:
        """Parse JSON_LENGTH function"""
        json_field = args[0]
        json_path = None
        
        if len(args) > 1:
            json_path = self._parse_json_path(args[1])
        
        return JSONOperation(
            operation_type=JSONOperationType.LENGTH,
            function_name=function_name,
            arguments=args,
            json_path=json_path,
            target_field=json_field if isinstance(json_field, str) else None
        )
    
    def _parse_json_path(self, path_str: str) -> JSONPath:
        """Parse JSON path string into JSONPath object"""
        if not isinstance(path_str, str):
            return JSONPath(str(path_str))
        
        # Check for array index pattern like $[0] or $.key[0] using string parsing
        is_array_index = False
        array_index = None
        
        # Find array bracket notation
        bracket_start = path_str.find('[')
        if bracket_start != -1:
            bracket_end = path_str.find(']', bracket_start)
            if bracket_end != -1:
                index_str = path_str[bracket_start+1:bracket_end]
                if index_str.isdigit():
                    is_array_index = True
                    array_index = int(index_str)
        
        # Check for wildcard
        is_wildcard = '*' in path_str or '[*]' in path_str
        
        return JSONPath(
            path=path_str,
            is_array_index=is_array_index,
            array_index=array_index,
            is_wildcard=is_wildcard
        )
    
    def get_supported_functions(self) -> List[str]:
        """Get list of supported JSON function names"""
        return list(self.supported_functions)
