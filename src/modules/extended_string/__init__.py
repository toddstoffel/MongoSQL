"""
Extended String Functions Module

This module provides support for advanced string manipulation functions
that extend beyond the basic string operations.

Functions supported:
- CONCAT_WS: Concatenate with separator
- REGEXP_SUBSTR: Extract substring using regular expressions  
- FORMAT: Number formatting with locale support
- SOUNDEX: Phonetic algorithm for string matching
- HEX: Convert to hexadecimal representation
- UNHEX: Convert from hexadecimal to string
- BIN: Convert to binary representation
"""

from .extended_string_function_mapper import ExtendedStringFunctionMapper
from .extended_string_parser import ExtendedStringParser
from .extended_string_translator import ExtendedStringTranslator
from .extended_string_types import (
    ExtendedStringOperation,
    ExtendedStringOperationType,
    RegexPattern,
    FormatSpecification
)

__all__ = [
    'ExtendedStringFunctionMapper',
    'ExtendedStringParser', 
    'ExtendedStringTranslator',
    'ExtendedStringOperation',
    'ExtendedStringOperationType',
    'RegexPattern',
    'FormatSpecification'
]
