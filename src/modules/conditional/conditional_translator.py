"""
Translator for conditional SQL functions to MongoDB aggregation operators
Uses MongoDB $cond, $switch, $ifNull operators
"""

from typing import Dict, Any, List, Optional, Union

from .conditional_types import (
    ConditionalExpression, ConditionalType, IfExpression,
    CaseExpression, WhenClause, CoalesceExpression, NullIfExpression
)


class ConditionalTranslator:
    """Translates conditional SQL expressions to MongoDB aggregation operators"""
    
    def __init__(self):
        self.comparison_operators = {
            '=': '$eq',
            '!=': '$ne',
            '<>': '$ne',
            '<': '$lt',
            '<=': '$lte',
            '>': '$gt',
            '>=': '$gte',
            'IS NULL': {'$eq': [None]},
            'IS NOT NULL': {'$ne': [None]}
        }
    
    def translate_conditional(self, conditional_expr: ConditionalExpression) -> Dict[str, Any]:
        """Translate a conditional expression to MongoDB aggregation operator"""
        
        if conditional_expr.conditional_type == ConditionalType.IF:
            return self._translate_if(conditional_expr.expression)
        
        elif conditional_expr.conditional_type == ConditionalType.CASE_WHEN:
            return self._translate_case_when(conditional_expr.expression)
        
        elif conditional_expr.conditional_type == ConditionalType.COALESCE:
            return self._translate_coalesce(conditional_expr.expression)
        
        elif conditional_expr.conditional_type == ConditionalType.NULLIF:
            return self._translate_nullif(conditional_expr.expression)
        
        else:
            raise ValueError(f"Unsupported conditional type: {conditional_expr.conditional_type}")
    
    def _translate_if(self, if_expr: IfExpression) -> Dict[str, Any]:
        """
        Translate IF(condition, value_if_true, value_if_false) to MongoDB $cond
        
        MongoDB $cond syntax:
        {
            "$cond": {
                "if": <boolean-expression>,
                "then": <true-case>,
                "else": <false-case>
            }
        }
        """
        condition = self._translate_condition(if_expr.condition)
        then_value = self._translate_value(if_expr.value_if_true)
        else_value = self._translate_value(if_expr.value_if_false)
        
        return {
            "$cond": {
                "if": condition,
                "then": then_value,
                "else": else_value
            }
        }
    
    def _translate_case_when(self, case_expr: CaseExpression) -> Dict[str, Any]:
        """
        Translate CASE WHEN to MongoDB $switch
        
        MongoDB $switch syntax:
        {
            "$switch": {
                "branches": [
                    { "case": <expression>, "then": <expression> },
                    { "case": <expression>, "then": <expression> },
                    ...
                ],
                "default": <expression>
            }
        }
        """
        branches = []
        
        for when_clause in case_expr.when_clauses:
            condition = self._translate_condition(when_clause.condition)
            value = self._translate_value(when_clause.value)
            
            branches.append({
                "case": condition,
                "then": value
            })
        
        switch_expr = {
            "$switch": {
                "branches": branches
            }
        }
        
        # Add default if else_value exists
        if case_expr.else_value is not None:
            switch_expr["$switch"]["default"] = self._translate_value(case_expr.else_value)
        
        return switch_expr
    
    def _translate_coalesce(self, coalesce_expr: CoalesceExpression) -> Dict[str, Any]:
        """
        Translate COALESCE(value1, value2, ...) to MongoDB $ifNull chain
        
        MongoDB $ifNull syntax:
        { "$ifNull": [ <expression>, <replacement-expression-if-null> ] }
        
        For multiple values, we chain $ifNull operators:
        { "$ifNull": [ value1, { "$ifNull": [ value2, value3 ] } ] }
        """
        if len(coalesce_expr.values) < 2:
            raise ValueError("COALESCE requires at least 2 values")
        
        # Start with the last value as the base
        result = self._translate_value(coalesce_expr.values[-1])
        
        # Work backwards through the values, creating nested $ifNull
        for value in reversed(coalesce_expr.values[:-1]):
            translated_value = self._translate_value(value)
            result = {
                "$ifNull": [translated_value, result]
            }
        
        return result
    
    def _translate_nullif(self, nullif_expr: NullIfExpression) -> Dict[str, Any]:
        """
        Translate NULLIF(expr1, expr2) to MongoDB conditional
        
        NULLIF returns NULL if expr1 equals expr2, otherwise returns expr1
        
        MongoDB equivalent:
        {
            "$cond": {
                "if": { "$eq": [ expr1, expr2 ] },
                "then": null,
                "else": expr1
            }
        }
        """
        expr1 = self._translate_value(nullif_expr.expr1)
        expr2 = self._translate_value(nullif_expr.expr2)
        
        return {
            "$cond": {
                "if": {"$eq": [expr1, expr2]},
                "then": None,
                "else": expr1
            }
        }
    
    def _translate_condition(self, condition: Any) -> Dict[str, Any]:
        """Translate a condition to MongoDB boolean expression"""
        if isinstance(condition, str):
            # Parse simple conditions
            condition = condition.strip()
            
            # Handle comparison operators
            for op in ['>=', '<=', '!=', '<>', '>', '<', '=']:
                if op in condition:
                    parts = condition.split(op)
                    if len(parts) == 2:
                        left = self._translate_value(parts[0].strip())
                        right = self._translate_value(parts[1].strip())
                        mongo_op = self.comparison_operators.get(op, '$eq')
                        
                        return {mongo_op: [left, right]}
            
            # Handle IS NULL / IS NOT NULL
            if condition.upper().endswith(' IS NULL'):
                field = condition[:-8].strip()
                return {"$eq": [self._translate_value(field), None]}
            elif condition.upper().endswith(' IS NOT NULL'):
                field = condition[:-12].strip()
                return {"$ne": [self._translate_value(field), None]}
            
            # Default: treat as field reference
            return self._translate_value(condition)
        
        else:
            # Already translated or complex condition
            return condition if isinstance(condition, dict) else self._translate_value(condition)
    
    def _translate_value(self, value: Any) -> Any:
        """Translate a value to MongoDB format"""
        if value is None:
            return None
        
        elif isinstance(value, (int, float, bool)):
            return value
        
        elif isinstance(value, str):
            value = value.strip()
            
            # Check if it's a numeric literal
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                pass
            
            # Check if it's a string literal (quoted)
            if ((value.startswith("'") and value.endswith("'")) or
                (value.startswith('"') and value.endswith('"'))):
                return value[1:-1]  # Remove quotes
            
            # Treat as field reference
            return f"${value}"
        
        elif isinstance(value, dict):
            # Already a MongoDB expression
            return value
        
        else:
            # Convert to string and treat as field reference
            return f"${str(value)}"
    
    def _is_field_reference(self, value: str) -> bool:
        """Check if a string value is a field reference"""
        # Simple heuristic: if it contains only alphanumeric characters and underscores,
        # and doesn't look like a quoted string, treat as field reference
        if not value:
            return False
        
        # Skip quoted strings
        if ((value.startswith("'") and value.endswith("'")) or
            (value.startswith('"') and value.endswith('"'))):
            return False
        
        # Check for numeric values
        try:
            float(value)
            return False
        except ValueError:
            pass
        
        # If it looks like an identifier, treat as field reference
        return value.replace('_', '').replace('.', '').isalnum()
