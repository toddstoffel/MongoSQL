"""
FULLTEXT function mapper for MongoDB translation
"""

from typing import Dict, Any, List, Optional


class FulltextFunctionMapper:
    """Maps FULLTEXT functions to MongoDB operations"""

    def __init__(self):
        self.function_map = {
            "MATCH": self._handle_match_function,
        }

    def map_function(
        self, function_name: str, args: List[str], context: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Map FULLTEXT function to MongoDB operation

        Args:
            function_name: Name of the FULLTEXT function
            args: Function arguments
            context: Additional context for translation

        Returns:
            MongoDB operation or None if not supported
        """
        func_name_upper = function_name.upper()

        if func_name_upper in self.function_map:
            return self.function_map[func_name_upper](args, context)

        return None

    def _handle_match_function(
        self, args: List[str], context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Handle MATCH() function for FULLTEXT search"""
        # MATCH function is always paired with AGAINST
        # This is handled at the WHERE clause level, not as a standalone function

        return {
            "_fulltext_match": {
                "type": "MATCH",
                "columns": args,
                "requires_against": True,
            }
        }

    def get_supported_functions(self) -> List[str]:
        """Get list of supported FULLTEXT functions"""
        return list(self.function_map.keys())

    def is_fulltext_function(self, function_name: str) -> bool:
        """Check if function is a FULLTEXT function"""
        return function_name.upper() in self.function_map


# Create singleton instance
fulltext_mapper = FulltextFunctionMapper()
