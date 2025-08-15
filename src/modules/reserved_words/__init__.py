"""Reserved Words Module

This module handles SQL reserved words and keywords for MariaDB compatibility.
Provides utilities to identify, escape, and handle reserved words in SQL parsing.

Classes:
    ReservedWordHandler: Main class for reserved word processing
    
Functions:
    is_reserved_word: Check if a word is reserved
    escape_identifier: Add backticks around reserved word identifiers
    get_reserved_words: Get list of all reserved words
"""

from .reserved_word_handler import ReservedWordHandler, is_reserved_word, escape_identifier
from .mariadb_reserved_words import MARIADB_RESERVED_WORDS, MARIADB_KEYWORDS

__all__ = [
    'ReservedWordHandler',
    'is_reserved_word',
    'escape_identifier',
    'MARIADB_RESERVED_WORDS',
    'MARIADB_KEYWORDS'
]
