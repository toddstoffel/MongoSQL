"""
Standalone WHERE clause translator to avoid circular imports
"""

from typing import Dict, Any, List, Optional
import re


class WhereTranslator:
    """Translates WHERE clauses to MongoDB match filters"""

    def __init__(self):
        """Initialize WHERE translator with FULLTEXT support"""
        from ..fulltext.fulltext_parser import FulltextParser
        from ..fulltext.fulltext_translator import FulltextTranslator

        self.fulltext_parser = FulltextParser()
        self.fulltext_translator = FulltextTranslator()

    def translate_where(self, where_clause: Dict[str, Any]) -> Dict[str, Any]:
        """Translate WHERE clause to MongoDB match filter"""
        if not where_clause:
            return {}

        # Check for raw WHERE clause string (for FULLTEXT)
        if isinstance(where_clause, str):
            return self._translate_raw_where_string(where_clause)

        # Handle compound WHERE clauses (with AND/OR)
        if where_clause.get("type") == "compound":
            return self._translate_compound_where(where_clause)

        # Handle simple WHERE clauses
        field = where_clause.get("field", "")
        operator = where_clause.get("operator", "=")
        value = where_clause.get("value")

        if not field or value is None:
            return {}

        return self._create_mongo_condition(field, operator, value)

    def _translate_raw_where_string(self, where_string: str) -> Dict[str, Any]:
        """Translate raw WHERE string, checking for FULLTEXT expressions"""
        # Check for MATCH...AGAINST expressions
        fulltext_query = self.fulltext_parser.parse_match_against(where_string)
        if fulltext_query:
            return self.fulltext_translator.translate_match_against(fulltext_query, "")

        # If not FULLTEXT, return empty (not supported)
        print(f"WARNING: Raw WHERE clause not fully supported: {where_string}")
        return {}

    def _translate_compound_where(self, where_clause: Dict[str, Any]) -> Dict[str, Any]:
        """Translate compound WHERE clause with AND/OR operators"""
        conditions = where_clause.get("conditions", [])
        operators = where_clause.get("operators", [])

        if not conditions:
            return {}

        if len(conditions) == 1:
            # Single condition
            return self.translate_where(conditions[0])

        # Multiple conditions with operators
        mongo_conditions = []
        for condition in conditions:
            mongo_condition = self.translate_where(condition)
            if mongo_condition:
                mongo_conditions.append(mongo_condition)

        if not mongo_conditions:
            return {}

        if len(mongo_conditions) == 1:
            return mongo_conditions[0]

        # Determine if all operators are AND or if we have OR
        has_or = any(op.upper() == "OR" for op in operators)

        if has_or:
            # Use $or for OR operations
            return {"$or": mongo_conditions}
        else:
            # All AND operations - combine into single filter
            combined_filter = {}
            for condition in mongo_conditions:
                combined_filter.update(condition)
            return combined_filter

    def _create_mongo_condition(
        self, field: str, operator: str, value: Any
    ) -> Dict[str, Any]:
        """Create MongoDB condition from field, operator, and value"""
        operator = operator.upper()

        if operator == "=":
            return {field: value}
        elif operator == "!=":
            return {field: {"$ne": value}}
        elif operator == "<":
            return {field: {"$lt": value}}
        elif operator == "<=":
            return {field: {"$lte": value}}
        elif operator == ">":
            return {field: {"$gt": value}}
        elif operator == ">=":
            return {field: {"$gte": value}}
        elif operator == "LIKE":
            # Convert SQL LIKE pattern to MongoDB regex
            regex_pattern = self._like_to_regex(value)
            return {field: {"$regex": regex_pattern, "$options": "i"}}
        elif operator == "REGEXP" or operator == "REGEX" or operator == "RLIKE":
            # Direct regex pattern for REGEXP/REGEX/RLIKE operators
            return {field: {"$regex": value, "$options": "i"}}
        elif operator == "IN":
            return {field: {"$in": value if isinstance(value, list) else [value]}}
        elif operator == "NOT IN":
            return {field: {"$nin": value if isinstance(value, list) else [value]}}
        elif operator == "IS NULL":
            return {field: None}
        elif operator == "IS NOT NULL":
            return {field: {"$ne": None}}
        else:
            # Fallback to equality
            return {field: value}

    def _like_to_regex(self, like_pattern: str) -> str:
        """Convert SQL LIKE pattern to MongoDB regex"""
        # First convert SQL wildcards to temporary placeholders
        temp_pattern = like_pattern.replace("%", "<<<PCT>>>").replace(
            "_", "<<<UNDERSCORE>>>"
        )

        # Escape special regex characters
        escaped = re.escape(temp_pattern)

        # Convert placeholders to regex equivalents
        # % becomes .* (any characters)
        # _ becomes . (single character)
        regex_pattern = escaped.replace("<<<PCT>>>", ".*").replace(
            "<<<UNDERSCORE>>>", "."
        )

        return regex_pattern
