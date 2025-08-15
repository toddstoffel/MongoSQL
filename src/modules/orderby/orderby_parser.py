"""
ORDER BY SQL parsing module
"""
import sqlparse
from typing import List, Optional
from .orderby_types import OrderByClause, OrderField, SortDirection

class OrderByParser:
    """Parser for ORDER BY clauses in SQL"""
    
    def __init__(self):
        pass  # No regex patterns needed anymore
    
    def parse_order_by(self, sql: str) -> Optional[OrderByClause]:
        """
        Parse ORDER BY clause from SQL string using token-based parsing
        
        Args:
            sql: SQL query string
            
        Returns:
            OrderByClause if found, None otherwise
        """
        # Use token-based parsing for all cases
        return self._parse_with_tokens(sql)
    
    def _parse_order_fields(self, order_clause: str) -> OrderByClause:
        """
        Parse individual fields from ORDER BY clause
        
        Args:
            order_clause: The ORDER BY clause content
            
        Returns:
            OrderByClause with parsed fields
        """
        fields = []
        
        # Split by comma but handle function calls
        field_parts = self._smart_split(order_clause)
        
        for part in field_parts:
            part = part.strip()
            if not part:
                continue
                
            # Check for explicit direction
            if part.upper().endswith(' DESC'):
                field_name = part[:-5].strip()
                direction = SortDirection.DESC
            elif part.upper().endswith(' ASC'):
                field_name = part[:-4].strip()
                direction = SortDirection.ASC
            else:
                field_name = part
                direction = SortDirection.ASC
            
            # Clean field name (remove quotes, table prefixes if needed)
            field_name = self._clean_field_name(field_name)
            
            fields.append(OrderField(field_name, direction))
        
        return OrderByClause(fields)
    
    def _smart_split(self, clause: str) -> List[str]:
        """
        Split ORDER BY clause by commas, respecting function parentheses
        
        Args:
            clause: ORDER BY clause content
            
        Returns:
            List of field specifications
        """
        parts = []
        current = ""
        paren_count = 0
        
        for char in clause:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                parts.append(current.strip())
                current = ""
                continue
            
            current += char
        
        if current.strip():
            parts.append(current.strip())
        
        return parts
    
    def _clean_field_name(self, field_name: str) -> str:
        """
        Clean field name by removing quotes and unnecessary table prefixes
        
        Args:
            field_name: Raw field name from SQL
            
        Returns:
            Cleaned field name
        """
        # Remove backticks and quotes
        field_name = field_name.strip('`"\'')
        
        # Remove table prefix if present (table.column -> column)
        if '.' in field_name and not field_name.startswith('('):
            # Only remove prefix if it's not a function call
            parts = field_name.split('.')
            if len(parts) == 2:
                field_name = parts[1]
        
        return field_name
    
    def _parse_with_tokens(self, sql: str) -> Optional[OrderByClause]:
        """
        Parse ORDER BY using sqlparse tokens
        
        Args:
            sql: SQL query string
            
        Returns:
            OrderByClause if found, None otherwise
        """
        try:
            parsed = sqlparse.parse(sql)[0]
            tokens = list(parsed.flatten())
            
            # Find ORDER BY keyword
            order_by_found = False
            order_fields = []
            current_field = ""
            
            for i, token in enumerate(tokens):
                token_str = str(token).strip()
                token_upper = token_str.upper()
                
                # Look for "ORDER BY" as a single token
                if token_upper == "ORDER BY":
                    order_by_found = True
                    continue
                elif order_by_found:
                    # Stop at next major clause
                    if token_upper in ["LIMIT", "GROUP BY", "HAVING", ";"]:
                        break
                    
                    # Skip whitespace tokens
                    if not token_str or token.ttype is sqlparse.tokens.Text.Whitespace:
                        continue
                    
                    # Collect ORDER BY content
                    current_field += token_str
            
            if current_field:
                return self._parse_order_fields(current_field)
                
        except Exception:
            pass
        
        return None
