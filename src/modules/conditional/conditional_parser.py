"""
Parser for conditional SQL functions (IF, CASE WHEN, COALESCE, NULLIF)
Uses token-based parsing following project standards
"""

import sqlparse
from sqlparse.sql import Function, Parenthesis, Token, Identifier, Comparison
from sqlparse.tokens import Keyword, Punctuation, Name, Literal, Operator
from typing import List, Optional, Any, Union

from .conditional_types import (
    ConditionalType, ConditionalExpression, IfExpression, 
    CaseExpression, WhenClause, CoalesceExpression, NullIfExpression
)


class ConditionalParser:
    """Parses conditional SQL expressions using token-based parsing"""
    
    def __init__(self):
        self.case_keywords = {'CASE', 'WHEN', 'THEN', 'ELSE', 'END'}
        self.conditional_functions = {'IF', 'COALESCE', 'NULLIF'}
    
    def parse_case_when(self, case_args_str: str) -> Optional[ConditionalExpression]:
        """Parse CASE WHEN from args_str format: 'WHEN condition THEN value ELSE default'"""
        try:
            # Parse the args string into tokens
            sql = f"CASE {case_args_str} END"
            parsed = sqlparse.parse(sql)[0]
            return self._parse_case_expression(parsed)
        except Exception as e:
            raise ValueError(f"Error parsing CASE expression: {str(e)}")

    def parse_conditional(self, token: Union[Function, Token]) -> Optional[ConditionalExpression]:
        """Parse a conditional expression from a token"""
        
        if isinstance(token, Function):
            # Handle IF, COALESCE, NULLIF functions
            function_name = token.get_name().upper()
            
            if function_name == 'IF':
                return self._parse_if_function(token)
            elif function_name == 'COALESCE':
                return self._parse_coalesce_function(token)
            elif function_name == 'NULLIF':
                return self._parse_nullif_function(token)
        
        elif self._is_case_expression(token):
            # Handle CASE WHEN expressions
            return self._parse_case_expression(token)
        
        return None
    
    def _parse_if_function(self, function_token: Function) -> Optional[ConditionalExpression]:
        """Parse IF(condition, value_if_true, value_if_false) function"""
        try:
            # Get function parameters
            params = self._extract_function_parameters(function_token)
            
            if len(params) != 3:
                return None
            
            condition = self._parse_expression(params[0])
            value_if_true = self._parse_expression(params[1])
            value_if_false = self._parse_expression(params[2])
            
            if_expr = IfExpression(
                condition=condition,
                value_if_true=value_if_true,
                value_if_false=value_if_false
            )
            
            return ConditionalExpression(
                conditional_type=ConditionalType.IF,
                expression=if_expr
            )
        
        except Exception:
            return None
    
    def _parse_case_expression(self, tokens: Union[Token, List[Token]]) -> Optional[ConditionalExpression]:
        """Parse CASE WHEN ... THEN ... ELSE ... END expression"""
        try:
            # If tokens is a single token, get its tokens
            if hasattr(tokens, 'tokens'):
                token_list = list(tokens.flatten())
            elif isinstance(tokens, list):
                token_list = tokens
            else:
                token_list = [tokens]
            
            when_clauses = []
            else_value = None
            
            i = 0
            while i < len(token_list):
                token = token_list[i]
                
                if token.ttype is Keyword and token.value.upper() == 'WHEN':
                    # Parse WHEN condition
                    i += 1
                    condition_tokens = []
                    
                    # Collect tokens until THEN
                    while i < len(token_list) and not (
                        token_list[i].ttype is Keyword and token_list[i].value.upper() == 'THEN'
                    ):
                        if not token_list[i].is_whitespace:
                            condition_tokens.append(token_list[i])
                        i += 1
                    
                    if i >= len(token_list):
                        break
                    
                    # Skip THEN keyword
                    i += 1
                    
                    # Collect value tokens until next WHEN, ELSE, or END
                    value_tokens = []
                    while i < len(token_list) and not (
                        token_list[i].ttype is Keyword and 
                        token_list[i].value.upper() in ['WHEN', 'ELSE', 'END']
                    ):
                        if not token_list[i].is_whitespace:
                            value_tokens.append(token_list[i])
                        i += 1
                    
                    # Create WHEN clause
                    condition = self._parse_expression(condition_tokens)
                    value = self._parse_expression(value_tokens)
                    
                    when_clauses.append(WhenClause(condition=condition, value=value))
                    continue
                
                elif token.ttype is Keyword and token.value.upper() == 'ELSE':
                    # Parse ELSE value
                    i += 1
                    else_tokens = []
                    
                    # Collect tokens until END
                    while i < len(token_list) and not (
                        token_list[i].ttype is Keyword and token_list[i].value.upper() == 'END'
                    ):
                        if not token_list[i].is_whitespace:
                            else_tokens.append(token_list[i])
                        i += 1
                    
                    else_value = self._parse_expression(else_tokens)
                    break
                
                elif token.ttype is Keyword and token.value.upper() == 'END':
                    break
                
                i += 1
            
            case_expr = CaseExpression(
                when_clauses=when_clauses,
                else_value=else_value
            )
            
            return ConditionalExpression(
                conditional_type=ConditionalType.CASE_WHEN,
                expression=case_expr
            )
        
        except Exception:
            return None
    
    def _parse_coalesce_function(self, function_token: Function) -> Optional[ConditionalExpression]:
        """Parse COALESCE(value1, value2, ...) function"""
        try:
            params = self._extract_function_parameters(function_token)
            
            if len(params) < 2:
                return None
            
            values = [self._parse_expression(param) for param in params]
            
            coalesce_expr = CoalesceExpression(values=values)
            
            return ConditionalExpression(
                conditional_type=ConditionalType.COALESCE,
                expression=coalesce_expr
            )
        
        except Exception:
            return None
    
    def _parse_nullif_function(self, function_token: Function) -> Optional[ConditionalExpression]:
        """Parse NULLIF(expr1, expr2) function"""
        try:
            params = self._extract_function_parameters(function_token)
            
            if len(params) != 2:
                return None
            
            expr1 = self._parse_expression(params[0])
            expr2 = self._parse_expression(params[1])
            
            nullif_expr = NullIfExpression(expr1=expr1, expr2=expr2)
            
            return ConditionalExpression(
                conditional_type=ConditionalType.NULLIF,
                expression=nullif_expr
            )
        
        except Exception:
            return None
    
    def _extract_function_parameters(self, function_token: Function) -> List[List[Token]]:
        """Extract parameters from a function token"""
        params = []
        current_param = []
        paren_level = 0
        
        # Find the parenthesis with parameters
        for token in function_token.tokens:
            if isinstance(token, Parenthesis):
                # Parse tokens inside parenthesis
                for sub_token in token.tokens:
                    if sub_token.ttype is Punctuation:
                        if sub_token.value == '(':
                            paren_level += 1
                        elif sub_token.value == ')':
                            paren_level -= 1
                        elif sub_token.value == ',' and paren_level == 1:
                            # End of parameter
                            if current_param:
                                params.append(current_param)
                                current_param = []
                            continue
                    
                    if paren_level >= 1 and not sub_token.is_whitespace:
                        current_param.append(sub_token)
                
                # Add last parameter
                if current_param:
                    params.append(current_param)
                break
        
        return params
    
    def _is_case_expression(self, token: Token) -> bool:
        """Check if token represents a CASE expression"""
        if hasattr(token, 'tokens'):
            for sub_token in token.flatten():
                if (sub_token.ttype is Keyword and 
                    sub_token.value.upper() == 'CASE'):
                    return True
        return False
    
    def _parse_expression(self, tokens: Union[Token, List[Token]]) -> Any:
        """Parse a general expression from tokens"""
        if not tokens:
            return None
        
        if isinstance(tokens, list):
            if len(tokens) == 1:
                return self._parse_single_token(tokens[0])
            else:
                # Multiple tokens - could be complex expression
                return self._parse_token_sequence(tokens)
        else:
            return self._parse_single_token(tokens)
    
    def _parse_single_token(self, token: Token) -> Any:
        """Parse a single token"""
        if token.ttype in (Literal.String.Single, Literal.String.Symbol):
            # String literal - preserve the quotes to indicate it's a literal
            return token.value
        elif token.ttype in (Literal.Number.Integer, Literal.Number.Float):
            # Numeric literal
            try:
                if '.' in token.value:
                    return float(token.value)
                else:
                    return int(token.value)
            except ValueError:
                return token.value
        elif token.ttype is Name or isinstance(token, Identifier):
            # Column reference
            return token.value
        else:
            # Default to string representation
            return token.value
    
    def _parse_token_sequence(self, tokens: List[Token]) -> Any:
        """Parse a sequence of tokens"""
        # For now, join non-whitespace tokens
        result = []
        for token in tokens:
            if not token.is_whitespace:
                result.append(token.value)
        
        return ' '.join(result) if result else None
