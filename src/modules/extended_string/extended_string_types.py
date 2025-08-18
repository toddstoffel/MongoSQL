"""
Extended String Function Types and Data Structures

This module defines the data structures and enums used for extended string operations.
All parsing is done using token-based methods (NO REGEX in parsing logic).
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


class ExtendedStringOperationType(Enum):
    """Types of extended string operations"""
    CONCAT_WS = "CONCAT_WS"
    REGEXP_SUBSTR = "REGEXP_SUBSTR" 
    FORMAT = "FORMAT"
    SOUNDEX = "SOUNDEX"
    HEX = "HEX"
    UNHEX = "UNHEX"
    BIN = "BIN"


@dataclass
class RegexPattern:
    """Represents a regular expression pattern for REGEXP functions"""
    pattern: str
    flags: Optional[str] = None
    
    def to_mongodb_regex(self) -> Dict[str, Any]:
        """Convert to MongoDB regex expression"""
        regex_expr = {"$regex": self.pattern}
        if self.flags:
            regex_expr["$options"] = self.flags
        return regex_expr


@dataclass
class FormatSpecification:
    """Represents number formatting specification"""
    decimal_places: int
    locale: Optional[str] = None
    use_thousands_separator: bool = True
    
    def to_mongodb_format(self) -> Dict[str, Any]:
        """Convert to MongoDB number formatting expression"""
        # MongoDB doesn't have direct FORMAT equivalent
        # We'll need to build this using string operations
        return {
            "decimal_places": self.decimal_places,
            "locale": self.locale,
            "thousands_separator": self.use_thousands_separator
        }


@dataclass 
class ExtendedStringOperation:
    """Represents an extended string function operation"""
    operation_type: ExtendedStringOperationType
    function_name: str
    arguments: List[Any]
    separator: Optional[str] = None  # For CONCAT_WS
    regex_pattern: Optional[RegexPattern] = None  # For REGEXP functions
    format_spec: Optional[FormatSpecification] = None  # For FORMAT function
    
    def __post_init__(self):
        """Validate operation after initialization"""
        if self.operation_type == ExtendedStringOperationType.CONCAT_WS and not self.separator:
            raise ValueError("CONCAT_WS operation requires separator")
        if self.operation_type == ExtendedStringOperationType.REGEXP_SUBSTR and not self.regex_pattern:
            raise ValueError("REGEXP_SUBSTR operation requires regex pattern")
        if self.operation_type == ExtendedStringOperationType.FORMAT and not self.format_spec:
            raise ValueError("FORMAT operation requires format specification")


# Function mappings for MongoDB operations
EXTENDED_STRING_FUNCTION_MAPPINGS = {
    'CONCAT_WS': {
        'mongodb_operator': '$concat',
        'description': 'Concatenate strings with separator',
        'min_args': 2,  # separator + at least one string
        'max_args': None,  # unlimited strings
        'example': "CONCAT_WS('-', 'a', 'b', 'c') -> 'a-b-c'"
    },
    'REGEXP_SUBSTR': {
        'mongodb_operator': '$regexFind', 
        'description': 'Extract substring matching regex pattern',
        'min_args': 2,  # string and pattern
        'max_args': 4,  # string, pattern, position, occurrence
        'example': "REGEXP_SUBSTR('Hello123', '[0-9]+') -> '123'"
    },
    'FORMAT': {
        'mongodb_operator': ['$toString', '$round'],
        'description': 'Format number with decimal places and thousands separators',
        'min_args': 2,  # number and decimal places
        'max_args': 3,  # number, decimal places, locale
        'example': "FORMAT(1234567.89, 2) -> '1,234,567.89'"
    },
    'SOUNDEX': {
        'mongodb_operator': '$function',  # Custom JavaScript function
        'description': 'Generate soundex phonetic code',
        'min_args': 1,  # string to encode
        'max_args': 1,
        'example': "SOUNDEX('Smith') -> 'S530'"
    },
    'HEX': {
        'mongodb_operator': '$function',  # Custom JavaScript function  
        'description': 'Convert string to hexadecimal representation',
        'min_args': 1,  # string to convert
        'max_args': 1,
        'example': "HEX('Hello') -> '48656C6C6F'"
    },
    'UNHEX': {
        'mongodb_operator': '$function',  # Custom JavaScript function
        'description': 'Convert hexadecimal to string',
        'min_args': 1,  # hex string to convert
        'max_args': 1, 
        'example': "UNHEX('48656C6C6F') -> 'Hello'"
    },
        'BIN': {
        'mongodb_operator': '$function',  # Custom JavaScript function
        'description': 'Convert number to binary representation',
        'min_args': 1,  # number to convert
        'max_args': 1,
        'example': "BIN(42) -> '101010'"
    }
}
def get_extended_string_function_info(function_name: str) -> Optional[Dict[str, Any]]:
    """Get information about an extended string function"""
    return EXTENDED_STRING_FUNCTION_MAPPINGS.get(function_name.upper())


def is_extended_string_function(function_name: str) -> bool:
    """Check if a function is an extended string function"""
    return function_name.upper() in EXTENDED_STRING_FUNCTION_MAPPINGS
