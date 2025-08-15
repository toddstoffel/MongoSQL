"""
Mathematical function mapper for SQL to MongoDB mathematical operations
Handles: ABS, ROUND, CEIL, FLOOR, SIN, COS, TAN, LOG, EXP, etc.
"""
from typing import Dict, List, Any, Optional
import math

class MathFunctionMapper:
    """Maps SQL mathematical functions to MongoDB math operators"""
    
    def __init__(self):
        self.function_map = self._build_math_map()
    
    def _build_math_map(self) -> Dict[str, Dict[str, Any]]:
        """Build the mathematical function mapping dictionary"""
        return {
            # Basic Mathematical Functions
            'ABS': {
                'mongodb': '$abs',
                'type': 'expression',
                'description': 'Absolute value'
            },
            'ROUND': {
                'mongodb': '$round',
                'type': 'expression',
                'description': 'Round to specified decimal places',
                'args': 'value_precision'
            },
            'CEIL': {
                'mongodb': '$ceil',
                'type': 'expression',
                'description': 'Ceiling (round up)'
            },
            'CEILING': {
                'mongodb': '$ceil',
                'type': 'expression',
                'description': 'Ceiling (alias for CEIL)'
            },
            'FLOOR': {
                'mongodb': '$floor',
                'type': 'expression',
                'description': 'Floor (round down)'
            },
            'TRUNCATE': {
                'mongodb': '$trunc',
                'type': 'expression',
                'description': 'Truncate to specified decimal places',
                'args': 'value_precision'
            },
            'TRUNC': {
                'mongodb': '$trunc',
                'type': 'expression',
                'description': 'Truncate (alias for TRUNCATE)',
                'args': 'value_precision'
            },
            
            # Trigonometric Functions
            'SIN': {
                'mongodb': '$sin',
                'type': 'expression',
                'description': 'Sine function'
            },
            'COS': {
                'mongodb': '$cos',
                'type': 'expression',
                'description': 'Cosine function'
            },
            'TAN': {
                'mongodb': '$tan',
                'type': 'expression',
                'description': 'Tangent function'
            },
            'ASIN': {
                'mongodb': '$asin',
                'type': 'expression',
                'description': 'Arc sine'
            },
            'ACOS': {
                'mongodb': '$acos',
                'type': 'expression',
                'description': 'Arc cosine'
            },
            'ATAN': {
                'mongodb': '$atan',
                'type': 'expression',
                'description': 'Arc tangent'
            },
            'ATAN2': {
                'mongodb': '$atan2',
                'type': 'expression',
                'description': 'Arc tangent of y/x'
            },
            'COT': {
                'mongodb': None,
                'type': 'custom',
                'description': 'Cotangent (1/tan)',
                'implementation': 'cotangent'
            },
            
            # Logarithmic and Exponential Functions
            'LOG': {
                'mongodb': '$log',
                'type': 'expression',
                'description': 'Natural logarithm or log with base',
                'args': 'value_or_base_value'
            },
            'LN': {
                'mongodb': '$ln',
                'type': 'expression',
                'description': 'Natural logarithm'
            },
            'LOG10': {
                'mongodb': '$log10',
                'type': 'expression',
                'description': 'Base-10 logarithm'
            },
            'EXP': {
                'mongodb': '$exp',
                'type': 'expression',
                'description': 'e raised to the power'
            },
            'POWER': {
                'mongodb': '$pow',
                'type': 'expression',
                'description': 'Raise to power',
                'args': 'base_exponent'
            },
            'POW': {
                'mongodb': '$pow',
                'type': 'expression',
                'description': 'Raise to power (alias for POWER)',
                'args': 'base_exponent'
            },
            'SQRT': {
                'mongodb': '$sqrt',
                'type': 'expression',
                'description': 'Square root'
            },
            
            # Angle Conversion
            'DEGREES': {
                'mongodb': '$radiansToDegrees',
                'type': 'expression',
                'description': 'Convert radians to degrees'
            },
            'RADIANS': {
                'mongodb': '$degreesToRadians',
                'type': 'expression',
                'description': 'Convert degrees to radians'
            },
            
            # Comparison Functions
            'GREATEST': {
                'mongodb': '$max',
                'type': 'expression',
                'description': 'Return the largest value',
                'args': 'multiple'
            },
            'LEAST': {
                'mongodb': '$min',
                'type': 'expression',
                'description': 'Return the smallest value',
                'args': 'multiple'
            },
            
            # Sign and Modulo
            'SIGN': {
                'mongodb': None,
                'type': 'custom',
                'description': 'Sign of number (-1, 0, 1)',
                'implementation': 'sign_function'
            },
            'MOD': {
                'mongodb': '$mod',
                'type': 'expression',
                'description': 'Modulo operation',
                'args': 'dividend_divisor'
            },
            
            # Random
            'RAND': {
                'mongodb': '$rand',
                'type': 'expression',
                'description': 'Random number between 0 and 1'
            },
            'RANDOM': {
                'mongodb': '$rand',
                'type': 'expression',
                'description': 'Random number (alias for RAND)'
            },
            
            # Constants (handled specially)
            'PI': {
                'mongodb': None,
                'type': 'constant',
                'description': 'Pi constant',
                'value': math.pi
            }
        }
    
    def map_function(self, function_name: str, args: List[Any] = None) -> Dict[str, Any]:
        """Map SQL mathematical function to MongoDB expression"""
        func_upper = function_name.upper()
        
        if func_upper not in self.function_map:
            raise ValueError(f"Unsupported mathematical function: {function_name}")
        
        mapping = self.function_map[func_upper]
        
        if mapping.get('type') == 'constant':
            return {'$literal': mapping['value']}
        elif mapping.get('type') == 'custom':
            return self._build_custom_expression(func_upper, args, mapping)
        else:
            return self._build_simple_expression(func_upper, args, mapping)
    
    def _build_simple_expression(self, function_name: str, args: List[Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Build simple MongoDB mathematical expression"""
        mongodb_op = mapping['mongodb']
        
        if not args and function_name not in ['RAND', 'RANDOM']:
            raise ValueError(f"Function {function_name} requires arguments")
        
        # Handle special argument patterns
        if function_name in ['ROUND', 'TRUNCATE', 'TRUNC']:
            # ROUND(value, precision) - precision is optional
            if len(args) == 1:
                return {mongodb_op: [args[0], 0]}  # Default precision
            else:
                return {mongodb_op: args}
        elif function_name in ['POWER', 'POW', 'MOD', 'ATAN2']:
            # Two-argument functions
            if len(args) != 2:
                raise ValueError(f"Function {function_name} requires exactly 2 arguments")
            return {mongodb_op: args}
        elif function_name == 'LOG':
            # LOG can be LOG(value) or LOG(base, value)
            if len(args) == 1:
                return {'$ln': args[0]}  # Natural log
            elif len(args) == 2:
                return {mongodb_op: args}  # Log with base
            else:
                raise ValueError("LOG function requires 1 or 2 arguments")
        elif function_name in ['GREATEST', 'LEAST']:
            # Multiple argument functions
            if len(args) < 2:
                raise ValueError(f"Function {function_name} requires at least 2 arguments")
            return {mongodb_op: args}
        elif function_name in ['RAND', 'RANDOM']:
            # No arguments
            return {mongodb_op: {}}
        
        # Default single-argument functions
        return {mongodb_op: args[0] if args else None}
    
    def _build_custom_expression(self, function_name: str, args: List[Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Build custom expressions for functions without direct MongoDB equivalents"""
        if function_name == 'COT':
            # COT(x) = 1/TAN(x) = COS(x)/SIN(x)
            if not args or len(args) != 1:
                raise ValueError("COT function requires exactly 1 argument")
            return {
                '$divide': [
                    {'$cos': args[0]},
                    {'$sin': args[0]}
                ]
            }
        elif function_name == 'SIGN':
            # SIGN(x) = -1 if x < 0, 0 if x = 0, 1 if x > 0
            if not args or len(args) != 1:
                raise ValueError("SIGN function requires exactly 1 argument")
            return {
                '$cond': [
                    {'$gt': [args[0], 0]},
                    1,
                    {
                        '$cond': [
                            {'$lt': [args[0], 0]},
                            -1,
                            0
                        ]
                    }
                ]
            }
        
        raise NotImplementedError(f"Custom function {function_name} not yet implemented")
    
    def is_math_function(self, function_name: str) -> bool:
        """Check if function is a mathematical function"""
        return function_name.upper() in self.function_map
    
    def get_supported_functions(self) -> List[str]:
        """Get list of supported mathematical functions"""
        return list(self.function_map.keys())
