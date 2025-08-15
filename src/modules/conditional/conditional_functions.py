"""
Conditional function mappings for SQL to MongoDB translation
Handles IF, CASE WHEN, COALESCE, NULLIF functions
"""
from typing import Dict, List, Any, Optional


class LegacyConditionalFunctionMapper:
    """Maps SQL conditional functions to MongoDB aggregation expressions"""
    
    def __init__(self):
        self.conditional_functions = {
            'IF': {
                'type': 'conditional',
                'mongodb_op': '$cond',
                'args': ['condition', 'if_true', 'if_false'],
                'description': 'IF(condition, value_if_true, value_if_false)'
            },
            'COALESCE': {
                'type': 'conditional', 
                'mongodb_op': '$ifNull',
                'args': ['expression', 'replacement'],
                'description': 'COALESCE(value1, value2, ...) - returns first non-null value'
            },
            'NULLIF': {
                'type': 'conditional',
                'mongodb_op': '$cond',
                'args': ['expr1', 'expr2'],
                'description': 'NULLIF(expr1, expr2) - returns null if expr1=expr2, else expr1'
            },
            'CASE': {
                'type': 'conditional',
                'mongodb_op': '$switch',
                'args': ['branches', 'default'],
                'description': 'CASE WHEN condition THEN result ... ELSE default END'
            }
        }
    
    def get_supported_functions(self) -> List[str]:
        """Get list of supported conditional function names"""
        return list(self.conditional_functions.keys())
    
    def is_conditional_function(self, function_name: str) -> bool:
        """Check if function is a conditional function"""
        return function_name.upper() in self.conditional_functions
    
    def get_function_mapping(self, function_name: str) -> Optional[Dict[str, Any]]:
        """Get MongoDB mapping for conditional function"""
        return self.conditional_functions.get(function_name.upper())
    
    def translate_if_function(self, args: List[Any]) -> Dict[str, Any]:
        """Translate IF(condition, if_true, if_false) to MongoDB $cond"""
        if len(args) != 3:
            raise ValueError("IF function requires exactly 3 arguments")
        
        condition, if_true, if_false = args
        
        return {
            "$cond": {
                "if": self._parse_condition(condition),
                "then": if_true,
                "else": if_false
            }
        }
    
    def translate_coalesce_function(self, args: List[Any]) -> Dict[str, Any]:
        """Translate COALESCE(...) to MongoDB $ifNull chain"""
        if len(args) < 2:
            raise ValueError("COALESCE function requires at least 2 arguments")
        
        # For multiple arguments, create nested $ifNull operations
        result = args[-1]  # Start with the last argument
        for arg in reversed(args[:-1]):
            result = {
                "$ifNull": [arg, result]
            }
        
        return result
    
    def translate_nullif_function(self, args: List[Any]) -> Dict[str, Any]:
        """Translate NULLIF(expr1, expr2) to MongoDB $cond"""
        if len(args) != 2:
            raise ValueError("NULLIF function requires exactly 2 arguments")
        
        expr1, expr2 = args
        
        return {
            "$cond": {
                "if": {"$eq": [expr1, expr2]},
                "then": None,
                "else": expr1
            }
        }
    
    def translate_case_when(self, case_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Translate CASE WHEN ... THEN ... ELSE ... END to MongoDB $switch"""
        branches = []
        
        for when_clause in case_structure.get('when_clauses', []):
            branches.append({
                "case": self._parse_condition(when_clause['condition']),
                "then": when_clause['result']
            })
        
        switch_expr = {
            "$switch": {
                "branches": branches
            }
        }
        
        # Add default case if present
        if 'else_clause' in case_structure:
            switch_expr["$switch"]["default"] = case_structure['else_clause']
        
        return switch_expr
    
    def _parse_condition(self, condition: Any) -> Dict[str, Any]:
        """Parse a condition expression for MongoDB"""
        if isinstance(condition, str):
            # Handle string conditions like "creditLimit > 50000"
            # This is a simplified parser - in production, use proper token parsing
            if '>' in condition:
                parts = condition.split('>')
                if len(parts) == 2:
                    field = parts[0].strip()
                    value = parts[1].strip()
                    try:
                        # Try to convert to number
                        numeric_value = float(value) if '.' in value else int(value)
                        return {"$gt": [f"${field}", numeric_value]}
                    except ValueError:
                        return {"$gt": [f"${field}", value]}
            elif '<' in condition:
                parts = condition.split('<')
                if len(parts) == 2:
                    field = parts[0].strip()
                    value = parts[1].strip()
                    try:
                        numeric_value = float(value) if '.' in value else int(value)
                        return {"$lt": [f"${field}", numeric_value]}
                    except ValueError:
                        return {"$lt": [f"${field}", value]}
            elif '=' in condition:
                parts = condition.split('=')
                if len(parts) == 2:
                    field = parts[0].strip()
                    value = parts[1].strip()
                    try:
                        numeric_value = float(value) if '.' in value else int(value)
                        return {"$eq": [f"${field}", numeric_value]}
                    except ValueError:
                        return {"$eq": [f"${field}", value]}
        
        # Fallback for complex conditions
        return condition if isinstance(condition, dict) else {"$literal": condition}
