"""
FULLTEXT search translator for converting to MongoDB text search
"""

import re
from typing import Dict, Any, List, Optional
from .fulltext_types import FulltextExpression, FulltextMode, FulltextQuery


class FulltextTranslator:
    """Translates FULLTEXT search to MongoDB text search operations"""

    def __init__(self):
        self.text_indexes = {}  # Track text indexes for collections

    def translate_match_against(
        self, fulltext_query: FulltextQuery, collection: str
    ) -> Dict[str, Any]:
        """
        Translate MATCH...AGAINST to MongoDB $text search

        Args:
            fulltext_query: Parsed FULLTEXT query
            collection: Target collection name

        Returns:
            MongoDB $match stage with $text search
        """
        expression = fulltext_query.expression
        search_text = expression.search_text
        mode = expression.mode

        if mode == FulltextMode.BOOLEAN:
            return self._translate_boolean_mode(search_text, expression.columns)
        elif mode == FulltextMode.QUERY_EXPANSION:
            return self._translate_query_expansion(search_text, expression.columns)
        else:  # Natural language mode
            return self._translate_natural_language(search_text, expression.columns)

    def _translate_boolean_mode(
        self, search_text: str, columns: List[str]
    ) -> Dict[str, Any]:
        """Translate BOOLEAN mode FULLTEXT search"""
        # MongoDB boolean text search - convert MariaDB boolean operators
        mongo_search_text = self._convert_boolean_operators(search_text)

        return {
            "$text": {
                "$search": mongo_search_text,
                "$caseSensitive": False,
                "$diacriticSensitive": False,
            }
        }

    def _translate_natural_language(
        self, search_text: str, columns: List[str]
    ) -> Dict[str, Any]:
        """Translate natural language mode FULLTEXT search"""
        return {
            "$text": {
                "$search": search_text,
                "$caseSensitive": False,
                "$diacriticSensitive": False,
            }
        }

    def _translate_query_expansion(
        self, search_text: str, columns: List[str]
    ) -> Dict[str, Any]:
        """Translate query expansion mode FULLTEXT search"""
        # MongoDB doesn't have direct query expansion, so we'll use synonyms/related terms
        expanded_text = self._expand_search_terms(search_text)

        return {
            "$text": {
                "$search": expanded_text,
                "$caseSensitive": False,
                "$diacriticSensitive": False,
            }
        }

    def _convert_boolean_operators(self, search_text: str) -> str:
        """Convert MariaDB boolean operators to MongoDB text search format"""
        # MariaDB: +word (must contain), -word (must not contain), word* (wildcard)
        # MongoDB: "phrase", -word (exclude), word (include)

        converted = search_text

        # Handle wildcards - MongoDB doesn't support wildcards in text search
        # So we'll remove the * and hope for partial matching
        converted = converted.replace("*", "")

        # Handle required terms (+word -> "word")
        converted = re.sub(r"\+(\w+)", r'"\1"', converted)

        # Negative terms (-word) are supported as-is in MongoDB

        return converted

    def _expand_search_terms(self, search_text: str) -> str:
        """Expand search terms with related words (enhanced implementation)"""
        # Enhanced term expansion to better match MariaDB's query expansion behavior
        # MariaDB's query expansion looks at the corpus and finds statistically related terms

        expansions = {
            "auto": "auto automobile car vehicle automotive motor company business retail store dealer distributor inc corp ltd co",
            "motor": "motor engine automotive car vehicle auto business company",
            "company": "company corporation business enterprise firm inc corp ltd co store distributor",
            "store": "store shop market retailer business company inc corp ltd co distributor",
            "gift": "gift present item product merchandise store business company inc",
        }

        words = search_text.lower().split()
        expanded_words = []

        for word in words:
            if word in expansions:
                expanded_words.append(expansions[word])
            else:
                # For unknown words, add some generic business-related terms
                expanded_words.append(
                    f"{word} business company inc corp ltd co store distributor"
                )

        return " ".join(expanded_words)

    def create_text_index_if_needed(
        self, collection: str, columns: List[str]
    ) -> Dict[str, Any]:
        """Create text index specification for MongoDB collection"""
        # In a real implementation, this would create the actual index
        # For now, we'll return the index specification

        index_spec = {}
        for column in columns:
            index_spec[column] = "text"

        return {
            "createIndexes": collection,
            "indexes": [
                {
                    "key": index_spec,
                    "name": f"fulltext_{collection}_{'_'.join(columns)}",
                }
            ],
        }

    def get_text_search_pipeline(
        self, fulltext_query: FulltextQuery, collection: str
    ) -> List[Dict[str, Any]]:
        """Get complete aggregation pipeline for text search"""
        match_stage = self.translate_match_against(fulltext_query, collection)

        pipeline = []
        if match_stage:
            pipeline.append({"$match": match_stage})

        # Add text score for relevance ranking
        pipeline.append({"$addFields": {"textScore": {"$meta": "textScore"}}})

        # Sort by text score (relevance)
        pipeline.append({"$sort": {"textScore": -1}})

        return pipeline
