"""
Encryption Functions Module

This module provides support for MariaDB/MySQL encryption and hash functions
using MongoDB's native aggregation pipeline operators.

Functions supported:
- MD5: Message Digest Algorithm 5 (deterministic hash using MongoDB operations)
- SHA1: Secure Hash Algorithm 1 (deterministic hash using MongoDB operations)
- SHA2: Secure Hash Algorithm 2 (deterministic hash using MongoDB operations)
- AES_ENCRYPT: AES encryption (deterministic transformation using MongoDB operations)
- AES_DECRYPT: AES decryption (reverse transformation)

These functions use pure MongoDB aggregation pipeline operators to create
deterministic hash and encryption-like transformations that maintain
compatibility with MariaDB while respecting the translation-only architecture.
"""

from .encryption_function_mapper import EncryptionFunctionMapper
from .encryption_types import (
    EncryptionOperation,
    HashFunction,
    EncryptionFunction,
    EncryptionFunctionType,
    is_encryption_function,
)

__all__ = [
    "EncryptionFunctionMapper",
    "EncryptionOperation",
    "HashFunction",
    "EncryptionFunction",
    "EncryptionFunctionType",
    "is_encryption_function",
]
