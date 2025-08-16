"""
JSON Function Types

Data structures for JSON function operations and MongoDB translation.
"""

from typing import Dict, List, Any, Union, Optional
from dataclasses import dataclass
from enum import Enum


class JSONOperationType(Enum):
    """Types of JSON operations"""
    EXTRACT = "extract"
    OBJECT = "object"
    ARRAY = "array"
    UNQUOTE = "unquote"
    KEYS = "keys"
    LENGTH = "length"
    SET = "set"
    REPLACE = "replace"
    MERGE = "merge"
    SEARCH = "search"


@dataclass
class JSONPath:
    """Represents a JSON path expression"""
    path: str
    is_array_index: bool = False
    array_index: Optional[int] = None
    is_wildcard: bool = False
    
    def to_mongodb_path(self) -> str:
        """Convert JSON path to MongoDB field path"""
        # Remove leading $ and convert dots to MongoDB field notation
        path = self.path.lstrip('$')
        if path.startswith('.'):
            path = path[1:]
        
        # Handle array notation [index] -> .index using string parsing
        result = ""
        i = 0
        while i < len(path):
            if path[i] == '[':
                # Find the closing bracket
                j = i + 1
                while j < len(path) and path[j] != ']':
                    j += 1
                if j < len(path):
                    # Extract the index and convert [index] to .index
                    index = path[i+1:j]
                    if index.isdigit():
                        result += '.' + index
                    i = j + 1
                else:
                    result += path[i]
                    i += 1
            else:
                result += path[i]
                i += 1
        
        return result


@dataclass
class JSONValue:
    """Represents a JSON value with type information"""
    value: Any
    json_type: str  # 'object', 'array', 'string', 'number', 'boolean', 'null'
    
    @classmethod
    def from_python(cls, value: Any) -> 'JSONValue':
        """Create JSONValue from Python value"""
        if isinstance(value, dict):
            return cls(value, 'object')
        elif isinstance(value, list):
            return cls(value, 'array')
        elif isinstance(value, str):
            return cls(value, 'string')
        elif isinstance(value, (int, float)):
            return cls(value, 'number')
        elif isinstance(value, bool):
            return cls(value, 'boolean')
        elif value is None:
            return cls(value, 'null')
        else:
            return cls(str(value), 'string')


@dataclass
class JSONOperation:
    """Represents a JSON function operation"""
    operation_type: JSONOperationType
    function_name: str
    arguments: List[Any]
    json_path: Optional[JSONPath] = None
    target_field: Optional[str] = None
    mongodb_expression: Optional[Dict[str, Any]] = None
    
    def to_mongodb_pipeline_stage(self) -> Dict[str, Any]:
        """Convert to MongoDB aggregation pipeline stage"""
        if self.mongodb_expression:
            return {"$addFields": {self.target_field or "result": self.mongodb_expression}}
        
        # Default implementation for simple operations
        return {"$project": {self.target_field or "result": {"$literal": "Not implemented"}}}


@dataclass
class JSONFunctionMapping:
    """Maps SQL JSON function to MongoDB operations"""
    sql_function: str
    mongodb_operators: List[str]
    operation_type: JSONOperationType
    supports_path: bool = True
    supports_array_index: bool = False
    description: str = ""
    
    def validate_arguments(self, args: List[Any]) -> bool:
        """Validate function arguments"""
        if self.sql_function == 'JSON_EXTRACT':
            return len(args) >= 2
        elif self.sql_function == 'JSON_OBJECT':
            return len(args) % 2 == 0  # Must have even number of args (key-value pairs)
        elif self.sql_function == 'JSON_ARRAY':
            return len(args) >= 1
        elif self.sql_function in ['JSON_UNQUOTE', 'JSON_KEYS', 'JSON_LENGTH']:
            return len(args) >= 1
        return True


# JSON Function Registry
JSON_FUNCTION_MAPPINGS = {
    'JSON_EXTRACT': JSONFunctionMapping(
        sql_function='JSON_EXTRACT',
        mongodb_operators=['$getField', '$arrayElemAt'],
        operation_type=JSONOperationType.EXTRACT,
        supports_path=True,
        supports_array_index=True,
        description='Extract data from JSON document using path'
    ),
    'JSON_OBJECT': JSONFunctionMapping(
        sql_function='JSON_OBJECT',
        mongodb_operators=['$mergeObjects'],
        operation_type=JSONOperationType.OBJECT,
        supports_path=False,
        description='Create JSON object from key-value pairs'
    ),
    'JSON_ARRAY': JSONFunctionMapping(
        sql_function='JSON_ARRAY',
        mongodb_operators=['$concatArrays'],
        operation_type=JSONOperationType.ARRAY,
        supports_path=False,
        description='Create JSON array from values'
    ),
    'JSON_UNQUOTE': JSONFunctionMapping(
        sql_function='JSON_UNQUOTE',
        mongodb_operators=['$toString'],
        operation_type=JSONOperationType.UNQUOTE,
        supports_path=False,
        description='Remove quotes from JSON string'
    ),
    'JSON_KEYS': JSONFunctionMapping(
        sql_function='JSON_KEYS',
        mongodb_operators=['$objectToArray'],
        operation_type=JSONOperationType.KEYS,
        supports_path=True,
        description='Extract keys from JSON object'
    ),
    'JSON_LENGTH': JSONFunctionMapping(
        sql_function='JSON_LENGTH',
        mongodb_operators=['$size', '$strLenCP'],
        operation_type=JSONOperationType.LENGTH,
        supports_path=True,
        description='Get length of JSON array or object'
    ),
    'JSON_SET': JSONFunctionMapping(
        sql_function='JSON_SET',
        mongodb_operators=['$mergeObjects'],
        operation_type=JSONOperationType.SET,
        supports_path=True,
        description='Set values in JSON document'
    ),
    'JSON_REPLACE': JSONFunctionMapping(
        sql_function='JSON_REPLACE',
        mongodb_operators=['$mergeObjects'],
        operation_type=JSONOperationType.REPLACE,
        supports_path=True,
        description='Replace values in JSON document'
    ),
    'JSON_MERGE': JSONFunctionMapping(
        sql_function='JSON_MERGE',
        mongodb_operators=['$mergeObjects'],
        operation_type=JSONOperationType.MERGE,
        supports_path=False,
        description='Merge multiple JSON documents'
    ),
    'JSON_SEARCH': JSONFunctionMapping(
        sql_function='JSON_SEARCH',
        mongodb_operators=['$indexOfArray', '$regexMatch'],
        operation_type=JSONOperationType.SEARCH,
        supports_path=True,
        description='Search for values in JSON document'
    )
}
