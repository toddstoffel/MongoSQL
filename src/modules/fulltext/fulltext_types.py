"""
FULLTEXT search types and enums for MongoDB translation
"""

from enum import Enum
from typing import List, Optional
from dataclasses import dataclass


class FulltextMode(Enum):
    """FULLTEXT search modes"""

    NATURAL_LANGUAGE = "NATURAL_LANGUAGE"
    BOOLEAN = "BOOLEAN"
    QUERY_EXPANSION = "QUERY_EXPANSION"


class FulltextSearchType(Enum):
    """FULLTEXT search function types"""

    MATCH_AGAINST = "MATCH_AGAINST"


@dataclass
class FulltextExpression:
    """Represents a FULLTEXT MATCH...AGAINST expression"""

    columns: List[str]
    search_text: str
    mode: FulltextMode

    def __post_init__(self):
        """Validate the FULLTEXT expression"""
        if not self.columns:
            raise ValueError("FULLTEXT search requires at least one column")
        if not self.search_text:
            raise ValueError("FULLTEXT search requires search text")


@dataclass
class FulltextQuery:
    """Represents a complete FULLTEXT query"""

    expression: FulltextExpression
    table: Optional[str] = None
    alias: Optional[str] = None
