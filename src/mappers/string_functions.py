"""
String function mapper for SQL to MongoDB string operations
Handles: CONCAT, SUBSTRING, UPPER, LOWER, LENGTH, TRIM, etc.
"""
from typing import Dict, List, Any, Optional

class StringFunctionMapper:
    """Maps SQL string functions to MongoDB string operators"""
    
    def __init__(self):
        self.function_map = self._build_string_map()
    
    def _build_string_map(self) -> Dict[str, Dict[str, Any]]:
        """Build the string function mapping dictionary"""
        return {
            # Basic String Functions
            'CONCAT': {
                'mongodb': '$concat',
                'type': 'expression',
                'description': 'Concatenates strings',
                'args': 'multiple'
            },
            'SUBSTRING': {
                'mongodb': '$substr',
                'type': 'expression',
                'description': 'Extracts substring',
                'args': 'position_length'
            },
            'SUBSTR': {
                'mongodb': '$substr',
                'type': 'expression',
                'description': 'Extracts substring (alias for SUBSTRING)',
                'args': 'position_length'
            },
            'LENGTH': {
                'mongodb': '$strLenCP',
                'type': 'expression',
                'description': 'Returns string length in code points'
            },
            'CHAR_LENGTH': {
                'mongodb': '$strLenCP',
                'type': 'expression',
                'description': 'Returns character length (alias for LENGTH)'
            },
            'CHARACTER_LENGTH': {
                'mongodb': '$strLenCP',
                'type': 'expression',
                'description': 'Returns character length (alias for LENGTH)'
            },
            
            # Case Conversion
            'UPPER': {
                'mongodb': '$toUpper',
                'type': 'expression',
                'description': 'Converts to uppercase'
            },
            'LOWER': {
                'mongodb': '$toLower',
                'type': 'expression',
                'description': 'Converts to lowercase'
            },
            'UCASE': {
                'mongodb': '$toUpper',
                'type': 'expression',
                'description': 'Converts to uppercase (alias for UPPER)'
            },
            'LCASE': {
                'mongodb': '$toLower',
                'type': 'expression',
                'description': 'Converts to lowercase (alias for LOWER)'
            },
            
            # String Manipulation
            'REVERSE': {
                'mongodb': None,  # No direct MongoDB equivalent
                'type': 'custom',
                'description': 'Reverses a string',
                'implementation': 'python_reverse'
            },
            
            # String Trimming
            'TRIM': {
                'mongodb': '$trim',
                'type': 'expression',
                'description': 'Removes leading and trailing whitespace',
                'args': 'optional_chars'
            },
            'LTRIM': {
                'mongodb': '$ltrim',
                'type': 'expression',
                'description': 'Removes leading whitespace',
                'args': 'optional_chars'
            },
            'RTRIM': {
                'mongodb': '$rtrim',
                'type': 'expression',
                'description': 'Removes trailing whitespace',
                'args': 'optional_chars'
            },
            
            # String Search and Replace
            'REPLACE': {
                'mongodb': '$replaceAll',
                'type': 'expression',
                'description': 'Replaces all occurrences of substring',
                'args': 'find_replace'
            },
            'REGEXP_REPLACE': {
                'mongodb': '$replaceAll',
                'type': 'expression',
                'description': 'Replaces using regular expression',
                'args': 'regex_replace'
            },
            
            # String Position Functions
            'INSTR': {
                'mongodb': '$indexOfCP',
                'type': 'expression',
                'description': 'Returns position of substring',
                'transform': 'add_one'  # MongoDB is 0-based, SQL is 1-based
            },
            'LOCATE': {
                'mongodb': '$indexOfCP',
                'type': 'expression', 
                'description': 'Returns position of substring',
                'transform': 'add_one'
            },
            'POSITION': {
                'mongodb': '$indexOfCP',
                'type': 'expression',
                'description': 'Returns position of substring',
                'transform': 'add_one'
            },
            
            # String Extraction
            'LEFT': {
                'mongodb': '$substr',
                'type': 'expression',
                'description': 'Returns leftmost characters',
                'args': 'length_from_start'
            },
            'RIGHT': {
                'mongodb': '$substr',
                'type': 'expression',
                'description': 'Returns rightmost characters',
                'args': 'length_from_end'
            },
            'MID': {
                'mongodb': '$substr',
                'type': 'expression',
                'description': 'Extracts substring from middle',
                'args': 'position_length'
            },
            
            # String Padding
            'LPAD': {
                'mongodb': '$concat',
                'type': 'expression',
                'description': 'Left-pads string to specified length',
                'complex': True  # Requires complex expression building
            },
            'RPAD': {
                'mongodb': '$concat',
                'type': 'expression',
                'description': 'Right-pads string to specified length',
                'complex': True
            },
            
            # String Comparison
            'STRCMP': {
                'mongodb': '$cmp',
                'type': 'expression',
                'description': 'Compares two strings'
            },
            
            # String Utilities
            'REVERSE': {
                'mongodb': None,  # No direct MongoDB equivalent
                'type': 'custom',
                'description': 'Reverses a string',
                'implementation': 'custom_reverse'
            },
            'REPEAT': {
                'mongodb': None,
                'type': 'custom',
                'description': 'Repeats string N times',
                'implementation': 'custom_repeat'
            },
            'SPACE': {
                'mongodb': None,
                'type': 'custom',
                'description': 'Returns string of N spaces',
                'implementation': 'custom_space'
            }
        }
    
    def map_function(self, function_name: str, args: List[Any] = None) -> Dict[str, Any]:
        """Map SQL string function to MongoDB expression"""
        func_upper = function_name.upper()
        
        if func_upper not in self.function_map:
            raise ValueError(f"Unsupported string function: {function_name}")
        
        mapping = self.function_map[func_upper]
        
        if mapping.get('complex'):
            return self._build_complex_expression(func_upper, args, mapping)
        elif mapping.get('type') == 'custom':
            return self._build_custom_expression(func_upper, args, mapping)
        else:
            return self._build_simple_expression(func_upper, args, mapping)
    
    def _build_simple_expression(self, function_name: str, args: List[Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Build simple MongoDB expression"""
        if not args:
            raise ValueError(f"Function {function_name} requires arguments")
        
        mongodb_op = mapping['mongodb']
        
        # Handle special argument patterns
        if function_name in ['SUBSTRING', 'SUBSTR', 'MID']:
            # SUBSTRING(string, start, length)
            if len(args) >= 2:
                return {
                    mongodb_op: [args[0], args[1] - 1, args[2] if len(args) > 2 else None]
                }
        elif function_name == 'LEFT':
            # LEFT(string, length) -> SUBSTR(string, 0, length)
            return {
                '$substr': [args[0], 0, args[1]]
            }
        elif function_name == 'RIGHT':
            # RIGHT(string, length) -> complex expression
            return self._build_right_expression(args)
        elif function_name in ['INSTR', 'LOCATE', 'POSITION']:
            # These need +1 for 1-based indexing
            base_expr = {mongodb_op: args}
            return {
                '$add': [base_expr, 1]
            }
        
        # Default simple mapping
        return {mongodb_op: args[0] if len(args) == 1 else args}
    
    def _build_complex_expression(self, function_name: str, args: List[Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Build complex MongoDB expressions for functions like LPAD, RPAD"""
        # Implementation for complex string functions
        # This would contain the logic for LPAD, RPAD, etc.
        raise NotImplementedError(f"Complex function {function_name} not yet implemented")
    
    def _build_custom_expression(self, function_name: str, args: List[Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Build custom expressions for functions without direct MongoDB equivalents"""
        if function_name == 'REVERSE':
            if not args or len(args) != 1:
                raise ValueError("REVERSE function requires exactly 1 argument")
            # Return a custom marker for reverse function
            return {'$reverse': args[0]}
        
        # Implementation for other custom functions like REPEAT, SPACE
        raise NotImplementedError(f"Custom function {function_name} not yet implemented")
    
    def _build_right_expression(self, args: List[Any]) -> Dict[str, Any]:
        """Build RIGHT() function using MongoDB expressions"""
        if len(args) != 2:
            raise ValueError("RIGHT function requires exactly 2 arguments")
        
        string_expr, length = args
        return {
            '$substr': [
                string_expr,
                {'$max': [0, {'$subtract': [{'$strLenCP': string_expr}, length]}]},
                length
            ]
        }
    
    def is_string_function(self, function_name: str) -> bool:
        """Check if function is a string function"""
        return function_name.upper() in self.function_map
    
    def get_supported_functions(self) -> List[str]:
        """Get list of supported string functions"""
        return list(self.function_map.keys())
