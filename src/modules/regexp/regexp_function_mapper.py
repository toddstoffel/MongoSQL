"""
REGEXP Function Mapper Module

This module provides integration between REGEXP module and the main translator.
Maps REGEXP operations and provides hooks for core translator integration.
"""

from typing import Dict, Any, List, Optional, Tuple
from .regexp_parser import RegexpParser
from .regexp_translator import RegexpTranslator
from .regexp_types import RegexpOperation, InfixRegexpExpression


class RegexpFunctionMapper:
    """Maps REGEXP operations for integration with core translator"""
    
    def __init__(self):
        self.parser = RegexpParser()
        self.translator = RegexpTranslator()
    
    def has_regexp_expressions(self, sql: str) -> bool:
        """Check if SQL contains REGEXP expressions"""
        return self.parser.has_regexp_expressions(sql)
    
    def parse_and_translate_regexp(self, sql: str, base_pipeline: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[RegexpOperation]]:
        """Parse SQL for REGEXP operations and integrate with pipeline"""
        operations = self.parser.parse_sql(sql)
        
        if not operations:
            return base_pipeline, []
        
        # Build enhanced pipeline with REGEXP operations
        enhanced_pipeline = self.translator.build_aggregation_pipeline(operations, base_pipeline)
        
        return enhanced_pipeline, operations
    
    def get_select_regexp_projections(self, sql: str) -> Dict[str, Any]:
        """Get projection mappings for REGEXP in SELECT expressions"""
        operations = self.parser.parse_sql(sql)
        select_operations = [op for op in operations if op.context == 'SELECT']
        
        if not select_operations:
            return {}
        
        return self.translator.translate_select_regexp(select_operations)
    
    def get_where_regexp_conditions(self, sql: str) -> List[Dict[str, Any]]:
        """Get match conditions for REGEXP in WHERE clause"""
        operations = self.parser.parse_sql(sql)
        where_operations = [op for op in operations if op.context == 'WHERE']
        
        if not where_operations:
            return []
        
        return self.translator.translate_where_regexp(where_operations)
    
    def get_having_regexp_conditions(self, sql: str) -> List[Dict[str, Any]]:
        """Get match conditions for REGEXP in HAVING clause"""
        operations = self.parser.parse_sql(sql)
        having_operations = [op for op in operations if op.context == 'HAVING']
        
        if not having_operations:
            return []
        
        return self.translator.translate_having_regexp(having_operations)
    
    def translate_infix_regexp(self, expression: str, context: str = 'SELECT', alias: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Translate a single infix REGEXP expression"""
        from .regexp_types import parse_regexp_expression, is_regexp_expression
        
        if not is_regexp_expression(expression):
            return None
        
        regexp_expr = parse_regexp_expression(expression)
        if not regexp_expr:
            return None
        
        if context == 'SELECT':
            return self.translator.translate_regexp_expression_for_projection(regexp_expr, alias)
        elif context in ['WHERE', 'HAVING']:
            # Build match condition
            condition = self.translator._build_match_condition(regexp_expr)
            return condition
        
        return None
    
    def enhance_projection_with_regexp(self, projection: Dict[str, Any], sql: str) -> Dict[str, Any]:
        """Enhance existing projection with REGEXP expressions"""
        regexp_projections = self.get_select_regexp_projections(sql)
        
        if regexp_projections:
            enhanced_projection = projection.copy()
            enhanced_projection.update(regexp_projections)
            return enhanced_projection
        
        return projection
    
    def enhance_match_with_regexp(self, match_stage: Dict[str, Any], sql: str, context: str = 'WHERE') -> Dict[str, Any]:
        """Enhance existing match stage with REGEXP conditions"""
        if context == 'WHERE':
            conditions = self.get_where_regexp_conditions(sql)
        elif context == 'HAVING':
            conditions = self.get_having_regexp_conditions(sql)
        else:
            return match_stage
        
        if conditions:
            enhanced_match = match_stage.copy()
            for condition in conditions:
                enhanced_match.update(condition)
            return enhanced_match
        
        return match_stage
    
    def process_regexp_in_select_item(self, select_item: str, alias: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Process a single SELECT item for REGEXP expressions"""
        return self.translate_infix_regexp(select_item, 'SELECT', alias)
    
    def get_regexp_operations_summary(self, sql: str) -> Dict[str, int]:
        """Get summary of REGEXP operations found in SQL"""
        operations = self.parser.parse_sql(sql)
        
        summary = {
            'total': len(operations),
            'select': len([op for op in operations if op.context == 'SELECT']),
            'where': len([op for op in operations if op.context == 'WHERE']),
            'having': len([op for op in operations if op.context == 'HAVING'])
        }
        
        return summary


# Global instance for easy access
regexp_mapper = RegexpFunctionMapper()


def has_regexp_expressions(sql: str) -> bool:
    """Module-level function to check for REGEXP expressions"""
    return regexp_mapper.has_regexp_expressions(sql)


def process_regexp_sql(sql: str, base_pipeline: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[RegexpOperation]]:
    """Module-level function to process REGEXP in SQL"""
    return regexp_mapper.parse_and_translate_regexp(sql, base_pipeline)


def get_regexp_projection(select_item: str, alias: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Module-level function to get REGEXP projection for SELECT items"""
    return regexp_mapper.process_regexp_in_select_item(select_item, alias)
