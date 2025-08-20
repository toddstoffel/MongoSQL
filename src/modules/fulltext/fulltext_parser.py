"""
FULLTEXT search parser for SQL MATCH...AGAINST expressions
"""

import re
from typing import Optional, List
from .fulltext_types import FulltextExpression, FulltextMode, FulltextQuery


class FulltextParser:
    """Parser for FULLTEXT MATCH...AGAINST expressions"""

    def __init__(self):
        self.match_patterns = [
            # MATCH(column) AGAINST('text' IN BOOLEAN MODE)
            r'MATCH\s*\(\s*([^)]+)\s*\)\s+AGAINST\s*\(\s*[\'"]([^\'\"]+)[\'"]\s+IN\s+BOOLEAN\s+MODE\s*\)',
            # MATCH(column) AGAINST('text' WITH QUERY EXPANSION)
            r'MATCH\s*\(\s*([^)]+)\s*\)\s+AGAINST\s*\(\s*[\'"]([^\'\"]+)[\'"]\s+WITH\s+QUERY\s+EXPANSION\s*\)',
            # MATCH(column) AGAINST('text') - natural language mode (default)
            r'MATCH\s*\(\s*([^)]+)\s*\)\s+AGAINST\s*\(\s*[\'"]([^\'\"]+)[\'"]\s*\)',
        ]

    def parse_match_against(self, where_clause: str) -> Optional[FulltextQuery]:
        """
        Parse MATCH...AGAINST expression from WHERE clause

        Args:
            where_clause: SQL WHERE clause string

        Returns:
            FulltextQuery object if MATCH...AGAINST found, None otherwise
        """
        if not where_clause or "MATCH" not in where_clause.upper():
            return None

        # Try each pattern
        for i, pattern in enumerate(self.match_patterns):
            match = re.search(pattern, where_clause, re.IGNORECASE)
            if match:
                columns_str = match.group(1).strip()
                search_text = match.group(2).strip()

                # Parse column list
                columns = [col.strip() for col in columns_str.split(",")]

                # Determine mode based on pattern index
                if i == 0:  # Boolean mode
                    mode = FulltextMode.BOOLEAN
                elif i == 1:  # Query expansion
                    mode = FulltextMode.QUERY_EXPANSION
                else:  # Natural language (default)
                    mode = FulltextMode.NATURAL_LANGUAGE

                expression = FulltextExpression(
                    columns=columns, search_text=search_text, mode=mode
                )

                return FulltextQuery(expression=expression)

        return None

    def extract_columns_from_match(self, match_expr: str) -> List[str]:
        """Extract column names from MATCH() expression"""
        # Remove MATCH( and ) to get column list
        columns_part = re.sub(r"MATCH\s*\(\s*", "", match_expr, flags=re.IGNORECASE)
        columns_part = re.sub(r"\s*\).*", "", columns_part)

        # Split by comma and clean up
        columns = [col.strip() for col in columns_part.split(",")]
        return columns

    def extract_search_text(self, against_expr: str) -> str:
        """Extract search text from AGAINST() expression"""
        # Find text within quotes
        match = re.search(r'[\'"]([^\'\"]+)[\'"]', against_expr)
        if match:
            return match.group(1)
        return ""

    def get_fulltext_mode(self, against_expr: str) -> FulltextMode:
        """Determine FULLTEXT mode from AGAINST expression"""
        against_upper = against_expr.upper()

        if "IN BOOLEAN MODE" in against_upper:
            return FulltextMode.BOOLEAN
        elif "WITH QUERY EXPANSION" in against_upper:
            return FulltextMode.QUERY_EXPANSION
        else:
            return FulltextMode.NATURAL_LANGUAGE
