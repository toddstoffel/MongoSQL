"""
JSON Function Mapper

Main interface for JSON function support in the MongoSQL translator.
Integrates JSON parsing and translation with the core function mapping system.
"""

from typing import Dict, List, Any, Optional
import sqlparse
from sqlparse.sql import Function

from .json_parser import JSONParser
from .json_translator import JSONTranslator
from .json_types import JSONOperation, JSON_FUNCTION_MAPPINGS


class JSONFunctionMapper:
    """Maps SQL JSON functions to MongoDB aggregation expressions"""
    
    def __init__(self):
        self.parser = JSONParser()
        self.translator = JSONTranslator()
        self.supported_functions = set(JSON_FUNCTION_MAPPINGS.keys())
    
    def is_json_function(self, function_name: str) -> bool:
        """Check if function is a supported JSON function"""
        return function_name.upper() in self.supported_functions
    
    def map_json_function(self, function_name: str, args: List[Any] = None, 
                         function_token: Function = None) -> Dict[str, Any]:
        """
        Map JSON function to MongoDB aggregation expression
        
        Args:
            function_name: Name of the JSON function
            args: Function arguments (optional if function_token provided)
            function_token: Parsed function token (preferred method)
        
        Returns:
            MongoDB aggregation expression
        """
        function_name = function_name.upper()
        
        if not self.is_json_function(function_name):
            return {"$literal": f"Unsupported function: {function_name}"}
        
        try:
            # Parse the function
            if function_token:
                operation = self.parser.parse_json_function(function_token)
            else:
                # Create basic operation from args
                operation = self._create_operation_from_args(function_name, args or [])
            
            if not operation:
                return {"$literal": f"Failed to parse {function_name}"}
            
            # Translate to MongoDB expression
            mongodb_expr = self.translator.translate_json_operation(operation)
            
            return mongodb_expr
            
        except Exception as e:
            return {"$literal": f"Error processing {function_name}: {str(e)}"}
    
    def _create_operation_from_args(self, function_name: str, args: List[Any]) -> Optional[JSONOperation]:
        """Create JSONOperation from function name and arguments"""
        mapping = JSON_FUNCTION_MAPPINGS.get(function_name)
        if not mapping:
            return None
        
        # Validate arguments
        if not mapping.validate_arguments(args):
            return None
        
        # Create appropriate operation based on function type
        operation = JSONOperation(
            operation_type=mapping.operation_type,
            function_name=function_name,
            arguments=args
        )
        
        # Add JSON path for functions that support it
        if mapping.supports_path and len(args) >= 2:
            operation.json_path = self.parser._parse_json_path(args[1])
        
        return operation
    
    def get_function_info(self, function_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a JSON function"""
        mapping = JSON_FUNCTION_MAPPINGS.get(function_name.upper())
        if not mapping:
            return None
        
        return {
            'function_name': mapping.sql_function,
            'mongodb_operators': mapping.mongodb_operators,
            'operation_type': mapping.operation_type.value,
            'supports_path': mapping.supports_path,
            'supports_array_index': mapping.supports_array_index,
            'description': mapping.description
        }
    
    def get_supported_functions(self) -> List[str]:
        """Get list of supported JSON function names"""
        return list(self.supported_functions)
    
    def get_function_examples(self) -> Dict[str, List[str]]:
        """Get examples of JSON function usage"""
        return {
            'JSON_EXTRACT': [
                "JSON_EXTRACT(user_data, '$.name')",
                "JSON_EXTRACT(user_data, '$.skills[0]')",
                "JSON_EXTRACT(user_data, '$.address.city')"
            ],
            'JSON_OBJECT': [
                "JSON_OBJECT('name', 'John', 'age', 30)",
                "JSON_OBJECT('customer', customerName, 'credit', creditLimit)"
            ],
            'JSON_ARRAY': [
                "JSON_ARRAY(1, 2, 'three', 4.5)",
                "JSON_ARRAY(customerName, country)"
            ],
            'JSON_UNQUOTE': [
                "JSON_UNQUOTE('\"Hello World\"')",
                "JSON_UNQUOTE(JSON_EXTRACT(user_data, '$.name'))"
            ],
            'JSON_KEYS': [
                "JSON_KEYS(user_data)",
                "JSON_KEYS(user_data, '$.address')"
            ],
            'JSON_LENGTH': [
                "JSON_LENGTH(user_data)",
                "JSON_LENGTH(user_data, '$.skills')"
            ]
        }
    
    def validate_json_syntax(self, json_str: str) -> bool:
        """Validate JSON syntax"""
        try:
            import json
            json.loads(json_str)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
