"""
JOIN parser - extracts JOIN information from SQL statements using sqlparse tokens
"""
import sqlparse
from sqlparse.sql import Statement, Identifier, IdentifierList, Token
from sqlparse.tokens import Keyword as KeywordToken, Name, Punctuation
from typing import List, Dict, Any, Optional
from .join_types import JoinType, JoinCondition, JoinOperation

class JoinParser:
    """Parses JOIN clauses from SQL statements using sqlparse"""
    
    def __init__(self):
        pass
    
    def parse_joins_from_sql(self, sql: str) -> List[JoinOperation]:
        """Extract all JOIN operations from SQL statement using sqlparse"""
        parsed = sqlparse.parse(sql)[0]
        joins = []
        
        # Find all JOIN keywords and their associated clauses
        tokens = list(parsed.flatten())
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Look for JOIN keywords
            if (token.ttype is KeywordToken and 
                token.value.upper() in ['JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS']):
                
                join_info = self._extract_join_sequence(tokens, i)
                if join_info:
                    join_op = self._build_join_operation(join_info)
                    if join_op:
                        joins.append(join_op)
                        i = join_info['end_index']
                        continue
            
            i += 1
        
        return joins
    
    def _extract_join_sequence(self, tokens: List[Token], start_idx: int) -> Optional[Dict[str, Any]]:
        """Extract a complete JOIN sequence from tokens"""
        join_type_tokens = []
        table_name = None
        table_alias = None
        
        i = start_idx
        
        # Collect JOIN type tokens (INNER, LEFT, etc.)
        while i < len(tokens):
            token = tokens[i]
            if (token.ttype is KeywordToken and 
                token.value.upper() in ['INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS', 'OUTER']):
                join_type_tokens.append(token.value.upper())
                i += 1
            elif token.ttype is KeywordToken and token.value.upper() == 'JOIN':
                join_type_tokens.append('JOIN')
                i += 1
                break
            else:
                i += 1
                
        if not join_type_tokens or 'JOIN' not in join_type_tokens:
            return None
        
        # Get table name and alias
        while i < len(tokens):
            token = tokens[i]
            if token.ttype is Name or (token.ttype is None and token.value.strip()):
                if not table_name:
                    table_name = token.value.strip()
                elif not table_alias and token.value.strip().upper() != 'ON':
                    table_alias = token.value.strip()
                i += 1
            elif token.ttype is KeywordToken and token.value.upper() == 'ON':
                i += 1
                break
            else:
                i += 1
        
        # Get ON conditions
        condition_tokens = []
        paren_depth = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token.value == '(':
                paren_depth += 1
            elif token.value == ')':
                paren_depth -= 1
                
            # Stop at next JOIN, WHERE, GROUP BY, ORDER BY, or LIMIT
            if (paren_depth == 0 and token.ttype is KeywordToken and 
                token.value.upper() in ['JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS',
                                       'WHERE', 'GROUP', 'ORDER', 'LIMIT', 'HAVING']):
                break
                
            condition_tokens.append(token)
            i += 1
        
        return {
            'join_type_tokens': join_type_tokens,
            'table_name': table_name,
            'table_alias': table_alias,
            'condition_tokens': condition_tokens,
            'end_index': i
        }
    
    def _build_join_operation(self, join_info: Dict[str, Any]) -> Optional[JoinOperation]:
        """Build a JoinOperation from extracted token information"""
        # Determine JOIN type
        join_type = self._determine_join_type_from_tokens(join_info['join_type_tokens'])
        
        # Parse conditions
        conditions = self._parse_on_conditions(join_info['condition_tokens'])
        
        if not conditions:
            return None
        
        return JoinOperation(
            join_type=join_type,
            left_table=None,  # Will be set later from context
            right_table=join_info['table_name'],
            conditions=conditions,
            alias_right=join_info['table_alias']
        )
    
    def _determine_join_type_from_tokens(self, tokens: List[str]) -> JoinType:
        """Determine JOIN type from token sequence"""
        tokens_upper = [t.upper() for t in tokens]
        
        if 'LEFT' in tokens_upper:
            return JoinType.LEFT
        elif 'RIGHT' in tokens_upper:
            return JoinType.RIGHT
        elif 'FULL' in tokens_upper:
            return JoinType.FULL
        elif 'CROSS' in tokens_upper:
            return JoinType.CROSS
        else:
            return JoinType.INNER
    
    def _parse_on_conditions(self, condition_tokens: List[Token]) -> List[JoinCondition]:
        """Parse ON clause conditions from tokens"""
        conditions = []
        
        # Convert tokens to string and parse
        condition_str = ''.join(token.value for token in condition_tokens if token.value.strip())
        
        if not condition_str.strip():
            return conditions
        
        # Split by AND (simple implementation)
        parts = condition_str.split(' AND ')
        
        for part in parts:
            condition = self._parse_single_condition_from_string(part.strip())
            if condition:
                conditions.append(condition)
        
        return conditions
    
    def _parse_single_condition_from_string(self, condition_str: str) -> Optional[JoinCondition]:
        """Parse a single condition like 'table1.col1 = table2.col2'"""
        # Simple parsing for now - can be enhanced later
        for op in ['=', '!=', '<>', '<', '>', '<=', '>=']:
            if op in condition_str:
                parts = condition_str.split(op, 1)
                if len(parts) == 2:
                    left_part = parts[0].strip()
                    right_part = parts[1].strip()
                    
                    # Parse table.column format
                    if '.' in left_part and '.' in right_part:
                        left_table, left_col = left_part.split('.', 1)
                        right_table, right_col = right_part.split('.', 1)
                        
                        return JoinCondition(
                            left_table=left_table.strip(),
                            left_column=left_col.strip(),
                            right_table=right_table.strip(),
                            right_column=right_col.strip(),
                            operator=op
                        )
        
        return None
    
    def update_parsed_sql_with_joins(self, parsed_sql: Dict[str, Any], sql: str) -> Dict[str, Any]:
        """Update parsed SQL dictionary with JOIN information"""
        joins = self.parse_joins_from_sql(sql)
        parsed_sql['joins'] = joins
        
        # Extract table aliases from FROM clause
        if joins and parsed_sql.get('from'):
            from_clause = parsed_sql['from']
            # Handle "table_name alias" format by checking if there are spaces
            if ' ' in from_clause.strip():
                parts = from_clause.strip().split()
                if len(parts) >= 2:
                    parsed_sql['from'] = parts[0]
                    parsed_sql['from_alias'] = parts[1]
                    
                    # Set the left table for first join
                    for join in joins:
                        if not join.left_table:
                            join.left_table = parts[0]
                            join.alias_left = parts[1] if len(parts) > 1 else None
                            break
        
        return parsed_sql
