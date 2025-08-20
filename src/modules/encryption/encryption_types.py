"""
Encryption and Hash Function Type Definitions

This module defines types and enums for encryption and hash operations
in SQL to MongoDB translation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


class EncryptionFunctionType(Enum):
    """Types of encryption and hash functions"""

    MD5 = "MD5"
    SHA1 = "SHA1"
    SHA2 = "SHA2"
    AES_ENCRYPT = "AES_ENCRYPT"
    AES_DECRYPT = "AES_DECRYPT"


@dataclass
class HashFunction:
    """Represents a hash function operation"""

    function_type: EncryptionFunctionType
    input_value: str
    algorithm: Optional[str] = None  # For SHA2 bit length


@dataclass
class EncryptionFunction:
    """Represents an encryption function operation"""

    function_type: EncryptionFunctionType
    data: str
    key: str
    algorithm: Optional[str] = None


@dataclass
class EncryptionOperation:
    """Represents any encryption or hash operation"""

    operation_type: EncryptionFunctionType
    args: List[str]
    mongodb_expression: Dict[str, Any]


# Supported encryption function names
SUPPORTED_ENCRYPTION_FUNCTIONS = {"MD5", "SHA1", "SHA2", "AES_ENCRYPT", "AES_DECRYPT"}


def is_encryption_function(function_name: str) -> bool:
    """Check if a function name is an encryption/hash function"""
    return function_name.upper() in SUPPORTED_ENCRYPTION_FUNCTIONS


def get_encryption_function_type(
    function_name: str,
) -> Optional[EncryptionFunctionType]:
    """Get encryption function type from function name"""
    name = function_name.upper()
    if name in SUPPORTED_ENCRYPTION_FUNCTIONS:
        return EncryptionFunctionType(name)
    return None
