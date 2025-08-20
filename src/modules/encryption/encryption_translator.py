"""
Encryption Translator

Translates encryption function operations to MongoDB expressions.
"""

from typing import Any, Dict, List, Optional
from .encryption_function_mapper import EncryptionFunctionMapper


class EncryptionTranslator:
    """Translates encryption functions to MongoDB expressions"""

    def __init__(self):
        self.function_mapper = EncryptionFunctionMapper()

    def translate_function(
        self, function_name: str, args: List[Any]
    ) -> Optional[Dict[str, Any]]:
        """Translate an encryption function to MongoDB expression"""
        return self.function_mapper.map_function(function_name, args)

    def translate_encryption_operation(
        self, operation: dict
    ) -> Optional[Dict[str, Any]]:
        """Translate a parsed encryption operation to MongoDB expression"""
        if not operation or "function_name" not in operation:
            return None

        function_name = operation["function_name"]
        args = operation.get("args", [])

        return self.translate_function(function_name, args)
