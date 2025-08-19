"""
WHERE clause parser - handles complex WHERE conditions with AND/OR operators
"""
from typing import List, Dict, Any, Optional
import sqlparse
from sqlparse import tokens as T

class WhereCondition:
    """Represents a single WHERE condition"""
    def __init__(self, field: str, operator: str, value: Any):
        self.field = field
        self.operator = operator
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'field': self.field,
            'operator': self.operator,
            'value': self.value
        }

class CompoundWhereClause:
    """Represents a compound WHERE clause with AND/OR operators"""
    def __init__(self):
        self.conditions: List[WhereCondition] = []
        self.operators: List[str] = []  # AND/OR between conditions
    
    def add_condition(self, condition: WhereCondition, logical_op: Optional[str] = None):
        """Add a condition with optional logical operator"""
        self.conditions.append(condition)
        if logical_op and len(self.conditions) > 1:
            self.operators.append(logical_op)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for translation"""
        if len(self.conditions) == 1:
            # Single condition
            return self.conditions[0].to_dict()
        else:
            # Multiple conditions with operators
            return {
                'type': 'compound',
                'conditions': [cond.to_dict() for cond in self.conditions],
                'operators': self.operators
            }

class WhereParser:
    """Token-based WHERE clause parser"""
    
    def parse_where_string(self, where_str: str) -> Dict[str, Any]:
        """Parse WHERE clause string using tokens"""
        try:
            # Parse the WHERE string as SQL
            parsed = sqlparse.parse(f"SELECT * FROM table WHERE {where_str}")[0]
            
            # Find the WHERE clause
            where_clause = None
            for token in parsed.tokens:
                if isinstance(token, sqlparse.sql.Where):
                    where_clause = token
                    break
            
            if not where_clause:
                return {'_raw': where_str}
            
            # Parse the WHERE condition tokens
            result = self._parse_where_tokens(where_clause.tokens[1:])  # Skip 'WHERE' keyword
            
            # If no conditions were parsed, fall back
            if (isinstance(result, dict) and 
                (result.get('type') == 'compound' and not result.get('conditions')) or
                (not result.get('field') and not result.get('type'))):
                return self._parse_simple_where(where_str)
            
            return result
            
        except Exception:
            # Fallback to simple parsing
            return self._parse_simple_where(where_str)
    
    def _parse_where_tokens(self, tokens: List) -> Dict[str, Any]:
        """Parse WHERE clause tokens"""
        compound_clause = CompoundWhereClause()
        logical_operator = None
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Skip whitespace
            if token.ttype is T.Whitespace:
                i += 1
                continue
            
            # Handle logical operators (AND/OR)
            if token.ttype is T.Keyword and token.value.upper() in ['AND', 'OR']:
                logical_operator = token.value.upper()
                i += 1
                continue
            
            # Handle comparison tokens (this is the key fix)
            if isinstance(token, sqlparse.sql.Comparison):
                condition = self._parse_comparison(token)
                if condition:
                    compound_clause.add_condition(condition, logical_operator)
                    logical_operator = None
                i += 1
                continue
            
            i += 1
        
        return compound_clause.to_dict()
    
    def _parse_comparison(self, comparison_token) -> Optional[WhereCondition]:
        """Parse a comparison token"""
        try:
            # Get the direct tokens from the comparison, not flattened
            tokens = comparison_token.tokens
            field = None
            operator = None
            value = None
            
            for token in tokens:
                # Skip whitespace
                if token.ttype in [T.Whitespace]:
                    continue
                
                # Field name - should be first identifier without quotes
                if not field:
                    if isinstance(token, sqlparse.sql.Identifier):
                        token_str = str(token).strip()
                        # If it has quotes, it's likely a value, not a field
                        if not (token_str.startswith('"') or token_str.startswith("'")):
                            field = token_str
                        else:
                            # This is a quoted value
                            value = token_str[1:-1]  # Remove quotes
                    elif token.ttype is None and '.' in str(token):
                        field = str(token).strip()
                    elif token.ttype in [T.Name]:
                        field = str(token).strip()
                
                # Operator
                elif token.ttype in [T.Operator.Comparison] or str(token).strip().upper() in ['LIKE', 'IN', 'BETWEEN', 'REGEXP', 'REGEX', 'RLIKE']:
                    operator = str(token).strip().upper()
                
                # Value (string literal, number, etc.)
                elif token.ttype in [T.Literal.String.Single, 
                                   T.Literal.String.Symbol,
                                   T.Literal.Number.Integer,
                                   T.Literal.Number.Float]:
                    value = self._extract_value(token)
                
                # Handle quoted identifiers as values (when we already have field and operator)
                elif field and operator and isinstance(token, sqlparse.sql.Identifier):
                    token_str = str(token).strip()
                    if token_str.startswith('"') or token_str.startswith("'"):
                        value = token_str[1:-1]  # Remove quotes
            
            if field and operator and value is not None:
                return WhereCondition(field, operator, value)
            
        except Exception:
            pass
        
        return None
    
    def _extract_value(self, token) -> Any:
        """Extract value from token"""
        value_str = str(token.value).strip()
        
        # Remove quotes if present
        if value_str.startswith("'") and value_str.endswith("'"):
            return value_str[1:-1]
        elif value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        
        # Try to convert to number
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            return value_str
    
    def _parse_simple_where(self, where_str: str) -> Dict[str, Any]:
        """Fallback simple parsing for basic cases"""
        where_upper = where_str.upper()
        
        # Handle IS NOT NULL
        if ' IS NOT NULL' in where_upper:
            field = where_str[:where_upper.index(' IS NOT NULL')].strip()
            return {
                'field': field,
                'operator': 'IS NOT NULL',
                'value': None
            }
        
        # Handle IS NULL
        elif ' IS NULL' in where_upper:
            field = where_str[:where_upper.index(' IS NULL')].strip()
            return {
                'field': field,
                'operator': 'IS NULL',
                'value': None
            }
        
        # Handle IN operator
        elif ' IN (' in where_upper:
            parts = where_str.split(' IN ')
            if len(parts) == 2:
                field = parts[0].strip()
                values_part = parts[1].strip()
                if values_part.startswith('(') and values_part.endswith(')'):
                    values_str = values_part[1:-1]  # Remove parentheses
                    values = [v.strip().strip("'\"") for v in values_str.split(',')]
                    return {
                        'field': field,
                        'operator': 'IN',
                        'value': values
                    }
        
        # Handle LIKE operator
        elif ' LIKE ' in where_upper:
            parts = where_str.split(' LIKE ')
            if len(parts) == 2:
                field = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                return {
                    'field': field,
                    'operator': 'LIKE',
                    'value': value
                }
        
        # Handle comparison operators (order matters - check multi-char first)
        elif '>=' in where_str:
            parts = where_str.split('>=')
            if len(parts) == 2:
                field = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                return {
                    'field': field,
                    'operator': '>=',
                    'value': value
                }
        
        elif '<=' in where_str:
            parts = where_str.split('<=')
            if len(parts) == 2:
                field = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                return {
                    'field': field,
                    'operator': '<=',
                    'value': value
                }
        
        elif '!=' in where_str:
            parts = where_str.split('!=')
            if len(parts) == 2:
                field = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                return {
                    'field': field,
                    'operator': '!=',
                    'value': value
                }
        
        elif '<>' in where_str:
            parts = where_str.split('<>')
            if len(parts) == 2:
                field = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                return {
                    'field': field,
                    'operator': '!=',  # Normalize <> to !=
                    'value': value
                }
        
        elif '>' in where_str:
            parts = where_str.split('>')
            if len(parts) == 2:
                field = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                return {
                    'field': field,
                    'operator': '>',
                    'value': value
                }
        
        elif '<' in where_str:
            parts = where_str.split('<')
            if len(parts) == 2:
                field = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                return {
                    'field': field,
                    'operator': '<',
                    'value': value
                }
        
        # Handle equality (check last to avoid conflicts)
        elif '=' in where_str:
            parts = where_str.split('=')
            if len(parts) == 2:
                field = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                return {
                    'field': field,
                    'operator': '=',
                    'value': value
                }
        
        # Fallback to raw for complex cases
        return {'_raw': where_str}
