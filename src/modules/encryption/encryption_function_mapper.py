"""
Encryption Function Mapper
"""

from typing import Any, Dict, List, Optional
from .encryption_types import is_encryption_function


class EncryptionFunctionMapper:
    """Maps encryption functions to MongoDB $function operations"""

    def __init__(self):
        self.function_map = {
            "MD5": {"type": "hash"},
            "SHA1": {"type": "hash"},
            "SHA2": {"type": "hash"},
            "AES_ENCRYPT": {"type": "encrypt"},
            "AES_DECRYPT": {"type": "decrypt"},
        }

    def map_function(
        self, function_name: str, args: List[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Map encryption function to MongoDB operations"""
        if not is_encryption_function(function_name):
            return None

        func_upper = function_name.upper()
        if func_upper == "MD5":
            return self._build_md5_expression(args or [])
        elif func_upper == "SHA1":
            return self._build_sha1_expression(args or [])
        elif func_upper == "SHA2":
            return self._build_sha2_expression(args or [])
        elif func_upper == "AES_ENCRYPT":
            return self._build_aes_encrypt_expression(args or [])
        elif func_upper == "AES_DECRYPT":
            return self._build_aes_decrypt_expression(args or [])
        else:
            raise ValueError(f"Unsupported encryption function: {function_name}")

    def _process_argument(self, arg: Any) -> Any:
        """Process function argument, converting field references to MongoDB syntax"""
        if isinstance(arg, dict) and "type" in arg:
            if arg["type"] == "literal":
                # It's a quoted string literal, return the value as-is
                return arg["value"]
            elif arg["type"] == "field_reference":
                # It's an unquoted field reference, convert to MongoDB field syntax
                return f"${arg['value']}"

        # For backward compatibility and other types (numbers, None, etc.)
        return arg

    def _build_md5_expression(self, args: List[Any]) -> Dict[str, Any]:
        """Build MD5 hash using client-side processing (MongoDB's JS doesn't have crypto)"""
        if len(args) != 1:
            raise ValueError("MD5 requires 1 argument")

        processed_arg = self._process_argument(args[0])
        # Return a special marker for client-side processing
        return {"_client_side_function": {"type": "MD5", "args": [processed_arg]}}

    def _build_sha1_expression(self, args: List[Any]) -> Dict[str, Any]:
        """Build SHA1 hash using client-side processing"""
        if len(args) != 1:
            raise ValueError("SHA1 requires 1 argument")

        processed_arg = self._process_argument(args[0])
        return {"_client_side_function": {"type": "SHA1", "args": [processed_arg]}}

    def _build_sha2_expression(self, args: List[Any]) -> Dict[str, Any]:
        """Build SHA2 hash using client-side processing"""
        if len(args) != 2:
            raise ValueError("SHA2 requires 2 arguments")

        processed_input = self._process_argument(args[0])
        processed_bits = self._process_argument(args[1])
        return {
            "_client_side_function": {
                "type": "SHA2",
                "args": [processed_input, processed_bits],
            }
        }

    def _build_aes_encrypt_expression(self, args: List[Any]) -> Dict[str, Any]:
        """Build AES encrypt using client-side processing"""
        if len(args) != 2:
            raise ValueError("AES_ENCRYPT requires 2 arguments")

        processed_data = self._process_argument(args[0])
        processed_key = self._process_argument(args[1])
        return {
            "_client_side_function": {
                "type": "AES_ENCRYPT",
                "args": [processed_data, processed_key],
            }
        }

    def _build_aes_decrypt_expression(self, args: List[Any]) -> Dict[str, Any]:
        """Build AES decrypt using client-side processing"""
        if len(args) != 2:
            raise ValueError("AES_DECRYPT requires 2 arguments")

        processed_encrypted = self._process_argument(args[0])
        processed_key = self._process_argument(args[1])
        return {
            "_client_side_function": {
                "type": "AES_DECRYPT",
                "args": [processed_encrypted, processed_key],
            }
        }

    def get_supported_functions(self) -> List[str]:
        """Return list of supported encryption functions"""
        return list(self.function_map.keys())

    def is_function_supported(self, function_name: str) -> bool:
        """Check if encryption function is supported"""
        return function_name.upper() in self.function_map
