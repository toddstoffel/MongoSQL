"""
SQL Parser for parsing MariaDB/MySQL syntax using proper token-based parsing
"""
import sqlparse
from sqlparse.sql import Statement, IdentifierList, Identifier, Function, Where, Comparison
from typing import List, Dict, Any, Optional
from ..where import WhereParser
from sqlparse.tokens import Keyword, Name, Number, String, Operator, Punctuation, Literal
from typing import Dict, List, Any, Optional, Union
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from ..joins.join_parser import JoinParser
from ..joins.join_types import JoinOperation, JoinCondition, JoinType

class TokenBasedSQLParser:
    """Parser for SQL statements using proper token-based parsing"""
    
    def __init__(self):
        """Initialize the token-based SQL parser"""
        self.where_parser = WhereParser()
    
    def parse(self, sql: str) -> Dict[str, Any]:
        """Parse SQL statement and return structured data"""
        # Parse SQL using sqlparse
        parsed = sqlparse.parse(sql)[0]
        
        # Get statement type
        statement_type = self._get_statement_type(parsed)
        
        if statement_type == 'SELECT':
            return self._parse_select(parsed)
        elif statement_type == 'INSERT':
            return self._parse_insert(parsed)
        elif statement_type == 'UPDATE':
            return self._parse_update(parsed)
        elif statement_type == 'DELETE':
            return self._parse_delete(parsed)
        elif statement_type == 'SHOW':
            return self._parse_show(parsed)
        elif statement_type == 'USE':
            return self._parse_use(parsed)
        else:
            raise Exception(f"Unsupported SQL type: {statement_type}")
    
    def _get_statement_type(self, tokens):
        """Determine the type of SQL statement"""
        for token in tokens:
            if token.ttype is sqlparse.tokens.Keyword.DML or token.ttype is sqlparse.tokens.Keyword:
                token_value = token.value.upper()
                if token_value == 'SELECT':
                    return 'SELECT'
                elif token_value == 'INSERT':
                    return 'INSERT'
                elif token_value == 'UPDATE':
                    return 'UPDATE'
                elif token_value == 'DELETE':
                    return 'DELETE'
        
        raise Exception(f"Could not determine statement type from tokens: {[(t.ttype, t.value) for t in tokens[:5]]}")
    
    def _parse_select(self, parsed: Statement) -> Dict[str, Any]:
        """Parse SELECT statement using sqlparse tokens"""
        result = {
            'type': 'SELECT',
            'columns': [],
            'from': None,
            'where': None,
            'group_by': [],
            'having': None,
            'order_by': [],
            'limit': None,
            'offset': None,
            'joins': [],
            'distinct': False
        }
        
        tokens = list(parsed.flatten())
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            if token.ttype in (Keyword, Keyword.DML) and token.value.upper() == 'SELECT':
                i = self._parse_select_clause(tokens, i + 1, result)
            elif token.ttype is Keyword and token.value.upper() == 'FROM':
                i = self._parse_from_clause(tokens, i + 1, result)
            elif token.ttype is Keyword and token.value.upper() == 'WHERE':
                i = self._parse_where_clause(tokens, i + 1, result)
            elif token.ttype is Keyword and token.value.upper() == 'GROUP BY':
                from ..groupby.groupby_parser import GroupByParser
                groupby_parser = GroupByParser()
                fields, i = groupby_parser.parse_group_by_from_tokens(tokens, i + 1)
                result['group_by'] = fields
            elif token.ttype is Keyword and token.value.upper() == 'HAVING':
                i = self._parse_having_clause(tokens, i + 1, result)
            elif token.ttype is Keyword and token.value.upper() == 'ORDER BY':
                i = self._parse_order_clause(tokens, i, result)
            elif token.ttype is Keyword and token.value.upper() == 'LIMIT':
                i = self._parse_limit_clause(tokens, i + 1, result)
            elif token.ttype is Keyword and 'JOIN' in token.value.upper():
                i = self._parse_join_clause(tokens, i, result)
            else:
                i += 1
        
        return result
    
    def _parse_select_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse SELECT column list"""
        i = start_idx
        columns = []
        current_column_tokens = []
        paren_depth = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            # Track parentheses depth
            if token.ttype is Punctuation and token.value == '(':
                paren_depth += 1
            elif token.ttype is Punctuation and token.value == ')':
                paren_depth -= 1
            
            # Stop at FROM keyword only if not inside parentheses
            if token.ttype is Keyword and token.value.upper() == 'FROM' and paren_depth == 0:
                break
            
            # Handle DISTINCT
            if token.ttype is Keyword and token.value.upper() == 'DISTINCT':
                result['distinct'] = True
                i += 1
                continue
            
            # Track parentheses depth
            if token.ttype is Punctuation and token.value == '(':
                paren_depth += 1
            elif token.ttype is Punctuation and token.value == ')':
                paren_depth -= 1
            
            # Handle column separators (commas) - only split at top level
            if token.ttype is Punctuation and token.value == ',' and paren_depth == 0:
                if current_column_tokens:
                    # Join tokens with proper spacing
                    column_str = self._reconstruct_column_from_tokens(current_column_tokens)
                    columns.append(column_str)
                    current_column_tokens = []
                i += 1
                continue
            
            # Collect all non-whitespace tokens for the column
            if token.ttype is not sqlparse.tokens.Text.Whitespace:
                current_column_tokens.append(token)
            elif current_column_tokens:  # Only add space if we have content
                # Add a space token to preserve spacing
                current_column_tokens.append(token)
            
            i += 1
        
        # Add final column if exists
        if current_column_tokens:
            column_str = self._reconstruct_column_from_tokens(current_column_tokens)
            columns.append(column_str)
        
        result['columns'] = columns
        return i
    
    def _reconstruct_column_from_tokens(self, tokens: List) -> str:
        """Reconstruct column string from tokens with proper spacing"""
        if not tokens:
            return ""
        
        result_parts = []
        for i, token in enumerate(tokens):
            if token.ttype is sqlparse.tokens.Text.Whitespace:
                # Only add single space, not the actual whitespace content
                if result_parts and not result_parts[-1].endswith(' '):
                    result_parts.append(' ')
            else:
                result_parts.append(token.value)
        
        column_str = ''.join(result_parts).strip()
        
        # Check if this is a function call and parse it
        if '(' in column_str and column_str.endswith(')'):
            return self._parse_function_column(column_str)
        
        return column_str
    
    def _parse_function_column(self, column_str: str) -> Dict[str, Any]:
        """Parse a function call column using proper token-based parsing"""
        # Parse the column string using sqlparse to get proper tokens
        try:
            parsed = sqlparse.parse(column_str)[0]
            function_token = None
            
            # Look for Function tokens in the parsed result
            for token in parsed.flatten():
                if hasattr(token, 'get_name') and hasattr(token, 'get_parameters'):
                    function_token = token
                    break
                elif str(type(token).__name__) == 'Function':
                    function_token = token
                    break
            
            if function_token:
                func_name = function_token.get_name().upper()
                parameters = function_token.get_parameters()
                args_str = str(parameters).strip() if parameters else ""
                
                # Remove extra parentheses if present
                if args_str.startswith('(') and args_str.endswith(')'):
                    args_str = args_str[1:-1].strip()
                
                column_info = {
                    'function': func_name,
                    'args_str': args_str,
                    'original_call': column_str
                }
                return column_info
                
        except Exception:
            # Fall back to manual parsing if sqlparse fails
            pass
        
        # Manual parsing with proper parentheses handling
        func_match = None
        for i, char in enumerate(column_str):
            if char == '(' and column_str[:i].strip():
                func_name = column_str[:i].strip().upper()
                start_paren = i
                break
        else:
            return column_str  # Not a function call
        
        # Find matching closing parenthesis
        paren_count = 0
        end_paren = -1
        
        for i in range(start_paren, len(column_str)):
            if column_str[i] == '(':
                paren_count += 1
            elif column_str[i] == ')':
                paren_count -= 1
                if paren_count == 0:
                    end_paren = i
                    break
        
        if end_paren == -1:
            return column_str  # Malformed function call
        
        # Extract arguments between the parentheses
        args_str = column_str[start_paren + 1:end_paren].strip()
        
        # Check for alias after the function
        remaining = column_str[end_paren + 1:].strip()
        alias = None
        if remaining.upper().startswith('AS '):
            alias = remaining[3:].strip()
        elif ' ' in remaining and not remaining.upper().startswith('FROM'):
            alias = remaining.strip()
        
        column_info = {
            'function': func_name, 
            'args_str': args_str,
            'original_call': column_str
        }
        if alias:
            column_info['alias'] = alias
            
        return column_info
    
    def _parse_from_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse FROM table with optional alias"""
        i = start_idx
        table_parts = []
        
        while i < len(tokens):
            token = tokens[i]
            
            # Stop at keywords that end FROM clause
            if (token.ttype is Keyword and 
                (token.value.upper() in ['WHERE', 'ORDER BY', 'GROUP BY', 'LIMIT', 'HAVING'] or
                 'JOIN' in token.value.upper())):
                break
            
            # Skip whitespace
            if token.value.strip() == '':
                i += 1
                continue
            
            # Collect table name and potential alias
            if token.ttype is Name or token.ttype is None:
                table_parts.append(token.value.strip())
            
            i += 1
        
        if table_parts:
            result['from'] = table_parts[0]
            if len(table_parts) > 1:
                result['from_alias'] = table_parts[1]
        
        return i
    
    def _parse_join_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse JOIN clause"""
        i = start_idx
        
        # Get JOIN type from current token
        join_token = tokens[i]
        join_type = join_token.value.upper()
        
        # Move past JOIN keyword
        i += 1
        
        # Skip whitespace
        while i < len(tokens) and tokens[i].ttype is sqlparse.tokens.Text.Whitespace:
            i += 1
        
        # Get table name
        if i >= len(tokens):
            return i
            
        table_name = tokens[i].value
        i += 1
        
        # Skip whitespace
        while i < len(tokens) and tokens[i].ttype is sqlparse.tokens.Text.Whitespace:
            i += 1
        
        # Get table alias if present
        table_alias = None
        if (i < len(tokens) and 
            tokens[i].ttype is sqlparse.tokens.Name and 
            tokens[i].value.upper() != 'ON'):
            table_alias = tokens[i].value
            i += 1
        
        # Skip whitespace
        while i < len(tokens) and tokens[i].ttype is sqlparse.tokens.Text.Whitespace:
            i += 1
        
        # Expect ON keyword
        if i < len(tokens) and tokens[i].ttype is Keyword and tokens[i].value.upper() == 'ON':
            i += 1
            # Parse join condition
            condition_tokens = []
            while i < len(tokens):
                token = tokens[i]
                if (token.ttype is Keyword and 
                    ('JOIN' in token.value.upper() or 
                     token.value.upper() in ['WHERE', 'ORDER', 'LIMIT', 'GROUP'])):
                    break
                condition_tokens.append(token)
                i += 1
            
            # Build condition string
            condition = ''.join(t.value for t in condition_tokens).strip()
            
            # Parse condition to create JoinCondition object
            join_condition = self._parse_join_condition(condition)
            
            # Map JOIN type string to enum
            join_type_map = {
                'INNER JOIN': JoinType.INNER,
                'LEFT JOIN': JoinType.LEFT,
                'RIGHT JOIN': JoinType.RIGHT,
                'FULL OUTER JOIN': JoinType.FULL,
                'CROSS JOIN': JoinType.CROSS
            }
            
            join_type_enum = join_type_map.get(join_type, JoinType.INNER)
            
            # Create proper JoinOperation object
            join_operation = JoinOperation(
                join_type=join_type_enum,
                left_table=result.get('from', ''),  # Base table
                right_table=table_name,
                conditions=[join_condition] if join_condition else [],
                alias_left=result.get('from_alias'),
                alias_right=table_alias
            )
            
            result['joins'].append(join_operation)
        
        return i
    
    def _parse_join_condition(self, condition_str: str) -> Optional[JoinCondition]:
        """Parse JOIN condition string into JoinCondition object"""
        if not condition_str or '=' not in condition_str:
            return None
        
        # Simple parsing for "table1.col1 = table2.col2" format
        parts = condition_str.split('=')
        if len(parts) != 2:
            return None
        
        left_part = parts[0].strip()
        right_part = parts[1].strip()
        
        # Parse left side
        if '.' in left_part:
            left_table, left_column = left_part.split('.', 1)
        else:
            left_table, left_column = '', left_part
        
        # Parse right side  
        if '.' in right_part:
            right_table, right_column = right_part.split('.', 1)
        else:
            right_table, right_column = '', right_part
        
        return JoinCondition(
            left_table=left_table.strip(),
            left_column=left_column.strip(),
            right_table=right_table.strip(),
            right_column=right_column.strip(),
            operator='='
        )

    def _parse_where_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse WHERE clause"""
        i = start_idx
        where_tokens = []
        
        while i < len(tokens):
            token = tokens[i]
            
            # Stop at keywords that end WHERE clause
            if (token.ttype is Keyword and 
                token.value.upper() in ['ORDER', 'GROUP', 'LIMIT', 'HAVING']):
                break
            
            where_tokens.append(token)
            i += 1
        
        if where_tokens:
            where_str = ''.join(t.value for t in where_tokens)
            result['where'] = self._parse_where_from_string(where_str.strip())
        
        return i
    
    def _parse_order_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse ORDER BY clause"""
        i = start_idx
        
        # Skip ORDER BY keyword (might be combined as "ORDER BY" or separate "ORDER" "BY")
        if tokens[i].value.upper() == 'ORDER BY':
            # Combined token, move to next
            i += 1
        else:
            # Separate tokens, skip ORDER and BY
            while i < len(tokens) and tokens[i].value.upper() != 'BY':
                i += 1
            i += 1  # Skip BY
        
        order_tokens = []
        while i < len(tokens):
            token = tokens[i]
            
            # Stop at LIMIT or other keywords
            if token.ttype is Keyword and token.value.upper() in ['LIMIT', 'GROUP', 'HAVING']:
                break
            
            order_tokens.append(token)
            i += 1
        
        if order_tokens:
            order_str = ''.join(t.value for t in order_tokens)
            result['order_by'] = self._parse_order_by(order_str.strip())
        
        return i
    
    def _parse_limit_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse LIMIT clause"""
        i = start_idx
        
        # Skip whitespace
        while i < len(tokens) and tokens[i].ttype is sqlparse.tokens.Text.Whitespace:
            i += 1
        
        if i < len(tokens) and tokens[i].ttype is sqlparse.tokens.Literal.Number.Integer:
            limit_count = int(tokens[i].value)
            result['limit'] = {'count': limit_count}
            i += 1
        
        return i
    
    def _parse_where_from_string(self, where_str: str) -> Dict[str, Any]:
        """Parse WHERE clause from string using modular WHERE parser"""
        return self.where_parser.parse_where_string(where_str)
    
    def _parse_order_by(self, order_str: str) -> List[Dict[str, Any]]:
        """Parse ORDER BY clause - temporary until full token parsing"""
        # This is a simplified implementation
        # TODO: Replace with proper token-based parsing
        parts = order_str.split(',')
        order_list = []
        for part in parts:
            part = part.strip()
            if part.upper().endswith(' DESC'):
                field = part[:-5].strip()
                direction = 'DESC'
            else:
                field = part.replace(' ASC', '').strip()
                direction = 'ASC'
            order_list.append({'field': field, 'direction': direction})
        return order_list
    
    def _parse_having_clause(self, tokens: List, start_idx: int, result: Dict) -> int:
        """Parse HAVING clause"""
        i = start_idx
        having_tokens = []
        
        # Collect all tokens until we hit another keyword or end
        while i < len(tokens):
            token = tokens[i]
            
            # Stop at other SQL keywords
            if (token.ttype is Keyword and 
                token.value.upper() in ['ORDER BY', 'LIMIT', 'UNION', 'EXCEPT', 'INTERSECT']):
                break
            
            having_tokens.append(token)
            i += 1
        
        # Parse the HAVING condition
        if having_tokens:
            having_str = ''.join(t.value for t in having_tokens).strip()
            # For now, store as string - can be enhanced later with WHERE parser
            result['having'] = having_str
        
        return i
    
    # Placeholder methods for other statement types
    def _parse_insert(self, parsed: Statement) -> Dict[str, Any]:
        return {'type': 'INSERT', 'error': 'Not implemented with token parsing yet'}
    
    def _parse_update(self, parsed: Statement) -> Dict[str, Any]:
        return {'type': 'UPDATE', 'error': 'Not implemented with token parsing yet'}
    
    def _parse_delete(self, parsed: Statement) -> Dict[str, Any]:
        return {'type': 'DELETE', 'error': 'Not implemented with token parsing yet'}
    
    def _parse_show(self, parsed: Statement) -> Dict[str, Any]:
        return {'type': 'SHOW', 'error': 'Not implemented with token parsing yet'}
    
    def _parse_use(self, parsed: Statement) -> Dict[str, Any]:
        return {'type': 'USE', 'error': 'Not implemented with token parsing yet'}
