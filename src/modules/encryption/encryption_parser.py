"""
Encryption Parser

Parses encryption and hash function calls from SQL tokens.
"""

from typing import Any, List, Optional
import sqlparse
from sqlparse.tokens import Keyword, Name, Punctuation
from .encryption_types import is_encryption_function, get_encryption_function_type


class EncryptionParser:
    """Parses encryption and hash functions from SQL tokens"""

    def __init__(self):
        pass

    def parse_function_call(self, tokens: List[sqlparse.sql.Token]) -> Optional[dict]:
        """Parse an encryption function call from tokens"""
        if not tokens:
            return None

        # Find function name
        function_name = None
        args = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Look for function name followed by parentheses
            if token.ttype is Name and i + 1 < len(tokens):
                next_token = tokens[i + 1]
                if next_token.ttype is Punctuation and str(next_token) == "(":
                    potential_func = str(token).upper()
                    if is_encryption_function(potential_func):
                        function_name = potential_func
                        # Parse arguments between parentheses
                        args = self._parse_function_args(tokens[i + 2 :])
                        break
            i += 1

        if function_name:
            return {
                "function_name": function_name,
                "function_type": get_encryption_function_type(function_name),
                "args": args,
            }

        return None

    def _parse_function_args(self, tokens: List[sqlparse.sql.Token]) -> List[str]:
        """Parse function arguments from tokens"""
        args = []
        current_arg = ""
        paren_count = 0

        for token in tokens:
            if str(token) == ")" and paren_count == 0:
                if current_arg.strip():
                    args.append(current_arg.strip())
                break
            elif str(token) == "(":
                paren_count += 1
                current_arg += str(token)
            elif str(token) == ")":
                paren_count -= 1
                current_arg += str(token)
            elif str(token) == "," and paren_count == 0:
                if current_arg.strip():
                    args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += str(token)

        return args
