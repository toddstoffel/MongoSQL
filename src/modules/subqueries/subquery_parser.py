"""
Subquery parser - extracts and parses subqueries from SQL statements
Uses token-based parsing (NO REGEX) following project architecture
"""
import sqlparse
from sqlparse.sql import Statement, Parenthesis, Where, Comparison
from sqlparse.tokens import Keyword, Operator, Punctuation, Name
from typing import List, Optional, Tuple, Dict, Any
from .subquery_types import SubqueryType, SubqueryOperation

class SubqueryParser:
    """Parses SQL subqueries using token-based analysis"""
    
    def __init__(self):
        self.debug = False
        
    def has_subqueries(self, sql: str) -> bool:
        """Check if SQL contains subqueries using token analysis"""
        try:
            parsed = sqlparse.parse(sql)[0]
            return self._contains_subquery_tokens(parsed.tokens)
        except Exception:
            return False
    
    def _contains_subquery_tokens(self, tokens) -> bool:
        """Recursively check tokens for subquery patterns"""
        for token in tokens:
            if isinstance(token, Parenthesis):
                # Check if parentheses contain SELECT
                inner_tokens = token.flatten()
                for inner_token in inner_tokens:
                    if (inner_token.ttype in (Keyword, Keyword.DML) and 
                        inner_token.value.upper() == 'SELECT'):
                        return True
                        
            # Recurse into compound tokens
            if hasattr(token, 'tokens'):
                if self._contains_subquery_tokens(token.tokens):
                    return True
                    
        return False
    
    def extract_subqueries(self, sql: str) -> List[SubqueryOperation]:
        """Extract all subqueries from SQL statement"""
        try:
            parsed = sqlparse.parse(sql)[0]
            subqueries = []
            
            # Search all tokens for subqueries, not just WHERE clause
            all_tokens = self._flatten_tokens(parsed.tokens)
            
            # Look for different subquery patterns throughout the SQL
            i = 0
            while i < len(all_tokens):
                token = all_tokens[i]
                
                # Pattern 1: field = (SELECT ...)
                if self._is_scalar_subquery_pattern(all_tokens, i):
                    subquery_op = self._parse_scalar_subquery(all_tokens, i)
                    if subquery_op:
                        subqueries.append(subquery_op)
                        
                # Pattern 2: field IN (SELECT ...)
                elif self._is_in_subquery_pattern(all_tokens, i):
                    subquery_op = self._parse_in_subquery(all_tokens, i)
                    if subquery_op:
                        subqueries.append(subquery_op)
                        
                # Pattern 3: EXISTS (SELECT ...)
                elif self._is_exists_subquery_pattern(all_tokens, i):
                    subquery_op = self._parse_exists_subquery(all_tokens, i)
                    if subquery_op:
                        subqueries.append(subquery_op)
                        
                # Pattern 4: (SELECT ...) in SELECT clause or anywhere else
                elif isinstance(token, Parenthesis) and self._parenthesis_contains_select(token):
                    subquery_sql = self._extract_subquery_sql(token)
                    if subquery_sql:
                        # Determine context based on surrounding tokens
                        subquery_type = self._determine_subquery_type(all_tokens, i)
                        
                        # Parse details from the subquery SQL
                        inner_collection, inner_field = self._parse_subquery_details(subquery_sql)
                        
                        # Determine outer field context (for WHERE clauses)
                        outer_field = self._determine_outer_field(all_tokens, i)
                        
                        # Determine comparison operator based on context
                        comparison_op = self._determine_comparison_operator(all_tokens, i)
                        
                        # Create SubqueryOperation with proper field names
                        subquery_op = SubqueryOperation(
                            subquery_type=subquery_type,
                            outer_field=outer_field,
                            inner_query=subquery_sql,
                            inner_collection=inner_collection,
                            inner_field=inner_field,
                            comparison_op=comparison_op,
                            correlation_fields=[]
                        )
                        subqueries.append(subquery_op)
                        
                i += 1
                
            return subqueries
            
        except Exception as e:
            if self.debug:
                print(f"Error parsing subqueries: {e}")
            return []
    
    def _find_where_clause(self, tokens) -> Optional[Where]:
        """Find WHERE clause in tokens"""
        for token in tokens:
            if isinstance(token, Where):
                return token
            # Recurse into compound tokens
            if hasattr(token, 'tokens'):
                where_clause = self._find_where_clause(token.tokens)
                if where_clause:
                    return where_clause
        return None
    
    def _parse_where_subqueries(self, where_clause: Where) -> List[SubqueryOperation]:
        """Parse subqueries within WHERE clause"""
        subqueries = []
        
        # Recursively search all tokens in WHERE clause for subquery patterns
        all_tokens = self._flatten_tokens(where_clause.tokens)
        
        # Look for different subquery patterns
        i = 0
        while i < len(all_tokens):
            token = all_tokens[i]
            
            # Pattern 1: field = (SELECT ...)
            if self._is_scalar_subquery_pattern(all_tokens, i):
                subquery_op = self._parse_scalar_subquery(all_tokens, i)
                if subquery_op:
                    subqueries.append(subquery_op)
                    
            # Pattern 2: field IN (SELECT ...)
            elif self._is_in_subquery_pattern(all_tokens, i):
                subquery_op = self._parse_in_subquery(all_tokens, i)
                if subquery_op:
                    subqueries.append(subquery_op)
                    
            # Pattern 3: EXISTS (SELECT ...)
            elif self._is_exists_subquery_pattern(all_tokens, i):
                subquery_op = self._parse_exists_subquery(all_tokens, i)
                if subquery_op:
                    subqueries.append(subquery_op)
                    
            i += 1
            
        return subqueries
    
    def _flatten_tokens(self, tokens):
        """Flatten nested tokens into a single list"""
        flat_tokens = []
        for token in tokens:
            flat_tokens.append(token)
            if hasattr(token, 'tokens'):
                flat_tokens.extend(self._flatten_tokens(token.tokens))
        return flat_tokens
    
    def _is_scalar_subquery_pattern(self, tokens, index: int) -> bool:
        """Check for pattern: field = (SELECT ...)"""
        if index + 2 >= len(tokens):
            return False
            
        # Look for: identifier, =, parenthesis
        current = tokens[index]
        next_token = tokens[index + 1] if index + 1 < len(tokens) else None
        after_next = tokens[index + 2] if index + 2 < len(tokens) else None
        
        # Check if we have field = (subquery)
        return (current.ttype not in (Keyword, Punctuation) and
                next_token and str(next_token).strip() == '=' and
                isinstance(after_next, Parenthesis) and
                self._parenthesis_contains_select(after_next))
    
    def _is_in_subquery_pattern(self, tokens, index: int) -> bool:
        """Check for pattern: field IN (SELECT ...)"""
        if index + 2 >= len(tokens):
            return False
            
        current = tokens[index]
        next_token = tokens[index + 1] if index + 1 < len(tokens) else None
        after_next = tokens[index + 2] if index + 2 < len(tokens) else None
        
        return (current.ttype not in (Keyword, Punctuation) and
                next_token and next_token.ttype is Keyword and 
                next_token.value.upper() == 'IN' and
                isinstance(after_next, Parenthesis) and
                self._parenthesis_contains_select(after_next))
    
    def _is_exists_subquery_pattern(self, tokens, index: int) -> bool:
        """Check for pattern: EXISTS (SELECT ...)"""
        if index + 1 >= len(tokens):
            return False
            
        current = tokens[index]
        next_token = tokens[index + 1] if index + 1 < len(tokens) else None
        
        return (current.ttype is Keyword and 
                current.value.upper() == 'EXISTS' and
                isinstance(next_token, Parenthesis) and
                self._parenthesis_contains_select(next_token))
    
    def _parenthesis_contains_select(self, parenthesis: Parenthesis) -> bool:
        """Check if parentheses contain SELECT statement"""
        inner_tokens = parenthesis.flatten()
        for token in inner_tokens:
            if (token.ttype in (Keyword, Keyword.DML) and 
                token.value.upper() == 'SELECT'):
                return True
        return False
    
    def _parse_scalar_subquery(self, tokens, index: int) -> Optional[SubqueryOperation]:
        """Parse scalar subquery: field = (SELECT ...)"""
        try:
            field_token = tokens[index]
            parenthesis = tokens[index + 2]
            
            # Extract field name
            outer_field = str(field_token).strip()
            
            # Extract subquery SQL
            inner_query = str(parenthesis).strip('()')
            
            # Parse inner query details
            inner_collection, inner_field = self._parse_subquery_details(inner_query)
            
            return SubqueryOperation(
                subquery_type=SubqueryType.SCALAR,
                outer_field=outer_field,
                inner_query=inner_query,
                inner_collection=inner_collection,
                inner_field=inner_field,
                comparison_op='='
            )
            
        except Exception as e:
            if self.debug:
                print(f"Error parsing scalar subquery: {e}")
            return None
    
    def _parse_in_subquery(self, tokens, index: int) -> Optional[SubqueryOperation]:
        """Parse IN subquery: field IN (SELECT ...)"""
        try:
            field_token = tokens[index]
            parenthesis = tokens[index + 2]
            
            outer_field = str(field_token).strip()
            inner_query = str(parenthesis).strip('()')
            
            inner_collection, inner_field = self._parse_subquery_details(inner_query)
            
            return SubqueryOperation(
                subquery_type=SubqueryType.IN_LIST,
                outer_field=outer_field,
                inner_query=inner_query,
                inner_collection=inner_collection,
                inner_field=inner_field,
                comparison_op='IN'
            )
            
        except Exception as e:
            if self.debug:
                print(f"Error parsing IN subquery: {e}")
            return None
    
    def _parse_exists_subquery(self, tokens, index: int) -> Optional[SubqueryOperation]:
        """Parse EXISTS subquery: EXISTS (SELECT ...)"""
        try:
            parenthesis = tokens[index + 1]
            inner_query = str(parenthesis).strip('()')
            
            inner_collection, _ = self._parse_subquery_details(inner_query)
            
            # Extract correlation fields for EXISTS
            correlation_fields = self._extract_correlation_fields(inner_query)
            
            return SubqueryOperation(
                subquery_type=SubqueryType.EXISTS,
                outer_field="",  # EXISTS doesn't compare specific field
                inner_query=inner_query,
                inner_collection=inner_collection,
                inner_field=None,
                comparison_op='EXISTS',
                correlation_fields=correlation_fields
            )
            
        except Exception as e:
            if self.debug:
                print(f"Error parsing EXISTS subquery: {e}")
            return None
    
    def _parse_subquery_details(self, subquery_sql: str) -> Tuple[str, Optional[str]]:
        """Extract collection and field from subquery SQL"""
        try:
            parsed = sqlparse.parse(subquery_sql)[0]
            tokens = list(parsed.flatten())  # Convert to list to avoid generator issues
            
            collection = None
            field = None
            
            # Look for FROM clause to get collection
            from_found = False
            for i, token in enumerate(tokens):
                if token.ttype is Keyword and token.value.upper() == 'FROM':
                    from_found = True
                elif from_found and token.ttype is Name and token.value.strip():
                    # Found collection name after FROM
                    collection = token.value.strip()
                    break
                        
            # Look for SELECT field (first non-whitespace token after SELECT)
            select_found = False
            for i, token in enumerate(tokens):
                if token.ttype in (Keyword, Keyword.DML) and token.value.upper() == 'SELECT':
                    select_found = True
                elif select_found and token.ttype is Name and token.value.strip():
                    # This is the first field name
                    field = token.value.strip()
                    # Check if next token is a dot (qualified name)
                    if i + 1 < len(tokens) and tokens[i + 1].ttype is Punctuation and tokens[i + 1].value == '.':
                        # Skip the dot and get the actual field name
                        if i + 2 < len(tokens) and tokens[i + 2].ttype is Name:
                            field = tokens[i + 2].value.strip()
                    break
                    
            return collection or 'unknown', field
            
        except Exception:
            return 'unknown', None
    
    def _determine_subquery_type(self, tokens: List, index: int) -> SubqueryType:
        """Determine the type of subquery based on context"""
        # Look at surrounding tokens to determine type
        if index > 0:
            # Look backwards for keywords that indicate subquery type
            for i in range(index - 1, max(0, index - 20), -1):
                token = tokens[i]
                if hasattr(token, 'ttype') and token.ttype is Keyword:
                    keyword = token.value.upper()
                    if keyword == 'EXISTS':
                        return SubqueryType.EXISTS
                    elif keyword == 'IN':
                        return SubqueryType.IN_LIST
                    elif keyword == 'FROM':
                        # Check if this subquery is ACTUALLY in FROM clause (DERIVED table)
                        # Only return DERIVED if the subquery is directly after FROM or after a comma in FROM clause
                        # Look for pattern: FROM table1, (SELECT ...) alias
                        # or FROM (SELECT ...) alias
                        
                        # Check if there's a WHERE keyword between FROM and the subquery
                        where_between = False
                        for j in range(i + 1, index):
                            if (j < len(tokens) and hasattr(tokens[j], 'ttype') and 
                                tokens[j].ttype is Keyword and tokens[j].value.upper() == 'WHERE'):
                                where_between = True
                                break
                        
                        # If there's a WHERE between FROM and subquery, this is NOT a DERIVED table
                        if where_between:
                            continue  # Keep looking for other patterns
                        
                        # This is likely a DERIVED table subquery
                        return SubqueryType.DERIVED
                        
                # Check for ROW subquery pattern: (field1, field2) = (SELECT ...)
                elif hasattr(token, 'ttype') and token.ttype is Operator.Comparison and token.value.strip() == '=':
                    # Look backwards from the = operator to find tuple pattern
                    # Pattern: ( field1 , field2 ) = 
                    tuple_tokens = []
                    paren_count = 0
                    found_opening_paren = False
                    
                    for j in range(i - 1, max(0, i - 15), -1):
                        check_token = tokens[j]
                        if hasattr(check_token, 'value'):
                            if check_token.value.strip() == ')':
                                paren_count += 1
                                if not found_opening_paren:
                                    found_opening_paren = True
                            elif check_token.value.strip() == '(':
                                paren_count -= 1
                                if found_opening_paren and paren_count == 0:
                                    # We found the complete tuple pattern
                                    # Check if we collected field names and commas
                                    has_comma = any(',' in str(t.value) for t in tuple_tokens)
                                    has_fields = any(hasattr(t, 'ttype') and t.ttype is Name for t in tuple_tokens)
                                    if has_comma and has_fields:
                                        return SubqueryType.ROW
                                    break
                            elif found_opening_paren and paren_count > 0:
                                tuple_tokens.append(check_token)
                        
        # Look ahead for context (less common)
        if index < len(tokens) - 1:
            next_token = tokens[index + 1]
            # More context analysis can be added here
            
        # Default to scalar subquery (common in SELECT clauses and = comparisons)
        return SubqueryType.SCALAR
    
    def _determine_comparison_operator(self, tokens: List, index: int) -> str:
        """Determine the comparison operator for the subquery"""
        # Look backwards for the operator that precedes the subquery
        for i in range(index - 1, max(0, index - 10), -1):
            token = tokens[i]
            if hasattr(token, 'ttype'):
                if token.ttype is Operator.Comparison:
                    return token.value.strip()
                elif token.ttype is Keyword and token.value.upper() in ['IN', 'EXISTS', 'NOT']:
                    # For keywords like IN, EXISTS
                    return token.value.upper()
        
        # Default to = for scalar subqueries
        return '='
    
    def _determine_outer_field(self, tokens: List, index: int) -> str:
        """Determine the outer field being compared in the subquery context"""
        # Look backwards for comparison pattern: field = (subquery)
        # or field IN (subquery), field EXISTS (subquery), etc.
        # For ROW subqueries: (field1, field2) = (subquery)
        
        # Look for comparison operator before the subquery
        for i in range(index - 1, max(0, index - 15), -1):
            token = tokens[i]
            if hasattr(token, 'ttype') and token.ttype is Operator.Comparison:
                # Found comparison operator, look for field(s) before it
                
                # Check for ROW pattern: (field1, field2) = 
                tuple_fields = []
                paren_count = 0
                found_closing_paren = False
                
                for j in range(i - 1, max(0, i - 15), -1):
                    check_token = tokens[j]
                    if hasattr(check_token, 'value'):
                        if check_token.value.strip() == ')':
                            paren_count += 1
                            if not found_closing_paren:
                                found_closing_paren = True
                        elif check_token.value.strip() == '(':
                            paren_count -= 1
                            if found_closing_paren and paren_count == 0:
                                # We found the complete tuple pattern
                                if tuple_fields:
                                    # Reverse the fields since we collected them backwards
                                    tuple_fields.reverse()
                                    return ','.join(tuple_fields)
                                break
                        elif (found_closing_paren and paren_count > 0 and 
                              hasattr(check_token, 'ttype') and check_token.ttype is Name):
                            # This is a field name inside the tuple
                            tuple_fields.append(check_token.value.strip())
                
                # Fallback: look for single field pattern
                for j in range(i - 1, max(0, i - 5), -1):
                    field_token = tokens[j]
                    if (hasattr(field_token, 'ttype') and 
                        field_token.ttype is Name and 
                        field_token.value.strip() and
                        field_token.value.strip() not in ['WHERE', 'AND', 'OR', '(', ')', ',']):
                        return field_token.value.strip()
                        
            # Also check for IN keyword pattern
            elif hasattr(token, 'ttype') and token.ttype is Keyword and token.value.upper() == 'IN':
                # Found IN keyword, look for field before it
                for j in range(i - 1, max(0, i - 5), -1):
                    field_token = tokens[j]
                    if (hasattr(field_token, 'ttype') and 
                        field_token.ttype is Name and 
                        field_token.value.strip() and
                        field_token.value.strip() not in ['WHERE', 'AND', 'OR', '(', ')', ',']):
                        return field_token.value.strip()
        
        # If no specific field context found, return empty (for SELECT clause subqueries)
        return ''
    
    def _extract_subquery_sql(self, parenthesis_token: Parenthesis) -> Optional[str]:
        """Extract SQL from parenthesis token"""
        try:
            # Get the content inside parentheses
            inner_sql = str(parenthesis_token)[1:-1]  # Remove outer parentheses
            return inner_sql.strip()
        except Exception:
            return None
        try:
            parsed = sqlparse.parse(subquery_sql)[0]
            
            # Find FROM clause to get collection
            collection = self._extract_from_table(parsed.tokens)
            
            # Find SELECT clause to get field
            field = self._extract_select_field(parsed.tokens)
            
            return collection, field
            
        except Exception:
            return "", None
    
    def _extract_from_table(self, tokens) -> str:
        """Extract table name from FROM clause"""
        from_found = False
        for token in tokens:
            if from_found and token.ttype not in (Keyword, Punctuation):
                return str(token).strip()
            if token.ttype is Keyword and token.value.upper() == 'FROM':
                from_found = True
        return ""
    
    def _extract_select_field(self, tokens) -> Optional[str]:
        """Extract field name from SELECT clause"""
        select_found = False
        for token in tokens:
            if select_found and token.ttype not in (Keyword, Punctuation):
                field = str(token).strip()
                # Handle SELECT 1 case
                if field == "1":
                    return None
                return field
            if token.ttype in (Keyword, Keyword.DML) and token.value.upper() == 'SELECT':
                select_found = True
        return None
    
    def _extract_correlation_fields(self, subquery_sql: str) -> List[str]:
        """Extract correlation fields from EXISTS subquery"""
        # For now, return empty list - can be enhanced for correlated subqueries
        return []
