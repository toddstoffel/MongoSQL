"""Reserved Word Handler

This module provides utilities for handling SQL reserved words and keywords
in the MongoSQL translator to ensure proper parsing and identifier handling for MariaDB.
"""

from typing import Set, Optional, Union
from .mariadb_reserved_words import (
    MARIADB_RESERVED_WORDS, 
    MARIADB_KEYWORDS, 
    MARIADB_ORACLE_MODE_RESERVED,
    MARIADB_FUNCTION_NAMES,
    MARIADB_EXCEPTIONS,
    ALL_MARIADB_WORDS
)


class ReservedWordHandler:
    """Handles reserved words and keywords for SQL parsing and identifier management.
    
    This class provides utilities to:
    - Check if a word is reserved
    - Escape identifiers when necessary
    - Handle MariaDB-specific reserved word variations
    """
    
    def __init__(self, oracle_mode: bool = False, ignore_space_mode: bool = False):
        """Initialize the reserved word handler for MariaDB.
        
        Args:
            oracle_mode: Whether Oracle compatibility mode is enabled (MariaDB only)
            ignore_space_mode: Whether IGNORE_SPACE SQL_MODE is set
        """
        self.oracle_mode = oracle_mode
        self.ignore_space_mode = ignore_space_mode
        
        # Set up reserved words for MariaDB
        self.reserved_words = MARIADB_RESERVED_WORDS.copy()
        self.keywords = MARIADB_KEYWORDS.copy()
        self.all_words = ALL_MARIADB_WORDS.copy()
        
        # Add Oracle mode reserved words if enabled
        if self.oracle_mode:
            self.reserved_words.update(MARIADB_ORACLE_MODE_RESERVED)
            self.all_words.update(MARIADB_ORACLE_MODE_RESERVED)
            
        # Add function names as reserved if IGNORE_SPACE mode is enabled
        if self.ignore_space_mode:
            self.reserved_words.update(MARIADB_FUNCTION_NAMES)
            self.all_words.update(MARIADB_FUNCTION_NAMES)
    
    def is_reserved_word(self, word: str) -> bool:
        """Check if a word is a reserved word that requires quoting.
        
        Args:
            word: The word to check
            
        Returns:
            True if the word is reserved and requires quoting
        """
        if not word:
            return False
            
        word_upper = word.upper()
        
        # Check if it's a reserved word
        if word_upper in self.reserved_words:
            # Handle MariaDB exceptions (historical reasons)
            if word_upper in MARIADB_EXCEPTIONS:
                return False
            return True
            
        return False
    
    def is_keyword(self, word: str) -> bool:
        """Check if a word is any kind of SQL keyword (reserved or non-reserved).
        
        Args:
            word: The word to check
            
        Returns:
            True if the word is a keyword
        """
        if not word:
            return False
            
        return word.upper() in self.all_words
    
    def escape_identifier(self, identifier: str) -> str:
        """Escape an identifier with backticks if it's a reserved word.
        
        Args:
            identifier: The identifier to potentially escape
            
        Returns:
            The identifier, escaped with backticks if necessary
        """
        if not identifier:
            return identifier
            
        if self.is_reserved_word(identifier):
            return f"`{identifier}`"
        
        return identifier
    
    def escape_if_needed(self, identifier: str, force_check: bool = False) -> str:
        """Escape an identifier only if absolutely necessary.
        
        This is a more conservative approach that only escapes when the
        identifier would definitely cause a SQL syntax error.
        
        Args:
            identifier: The identifier to check
            force_check: If True, always check and escape reserved words
            
        Returns:
            The identifier, escaped only if necessary
        """
        if not identifier:
            return identifier
            
        # Always escape if forced or if it's a reserved word
        if force_check or self.is_reserved_word(identifier):
            return self.escape_identifier(identifier)
            
        return identifier
    
    def get_reserved_words(self) -> Set[str]:
        """Get the set of reserved words for the current configuration.
        
        Returns:
            Set of reserved words
        """
        return self.reserved_words.copy()
    
    def get_keywords(self) -> Set[str]:
        """Get the set of all keywords (reserved and non-reserved).
        
        Returns:
            Set of all keywords
        """
        return self.all_words.copy()
    
    def check_identifier_conflicts(self, identifier: str) -> dict:
        """Check for potential conflicts with an identifier.
        
        Args:
            identifier: The identifier to check
            
        Returns:
            Dictionary with conflict information:
            - is_reserved: bool
            - is_keyword: bool  
            - needs_escaping: bool
            - suggested_name: str (escaped version)
        """
        if not identifier:
            return {
                'is_reserved': False,
                'is_keyword': False,
                'needs_escaping': False,
                'suggested_name': identifier
            }
            
        is_reserved = self.is_reserved_word(identifier)
        is_keyword = self.is_keyword(identifier)
        needs_escaping = is_reserved
        
        return {
            'is_reserved': is_reserved,
            'is_keyword': is_keyword,
            'needs_escaping': needs_escaping,
            'suggested_name': self.escape_identifier(identifier) if needs_escaping else identifier
        }
    
    def validate_identifier(self, identifier: str, context: str = '') -> tuple[bool, str]:
        """Validate an identifier and return status with message.
        
        Args:
            identifier: The identifier to validate
            context: Context description (e.g., 'column name', 'table name')
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not identifier:
            return False, f"Empty {context or 'identifier'} is not allowed"
            
        conflicts = self.check_identifier_conflicts(identifier)
        
        if conflicts['is_reserved']:
            return False, (
                f"'{identifier}' is a reserved word and cannot be used as {context or 'an identifier'} "
                f"without backtick quoting. Use `{identifier}` instead."
            )
        
        if conflicts['is_keyword']:
            return True, (
                f"'{identifier}' is a keyword but can be used as {context or 'an identifier'}. "
                f"Consider using `{identifier}` to avoid potential issues."
            )
            
        return True, f"'{identifier}' is a valid {context or 'identifier'}"


# Convenience functions for common operations
def is_reserved_word(word: str) -> bool:
    """Quick check if a word is reserved (convenience function).
    
    Args:
        word: Word to check
        
    Returns:
        True if reserved
    """
    handler = ReservedWordHandler()
    return handler.is_reserved_word(word)


def escape_identifier(identifier: str) -> str:
    """Quick escape of an identifier (convenience function).
    
    Args:
        identifier: Identifier to escape
        
    Returns:
        Escaped identifier
    """
    handler = ReservedWordHandler()
    return handler.escape_identifier(identifier)
