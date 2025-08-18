"""
REGEXP Translator Module

This module translates REGEXP operations to MongoDB aggregation stages.
Handles infix REGEXP/RLIKE expressions in SELECT, WHERE, and HAVING clauses.
"""

from typing import Dict, Any, List, Optional
from .regexp_types import RegexpOperation, RegexpOperationType, InfixRegexpExpression


class RegexpTranslator:
    """Translator for REGEXP operations to MongoDB"""
    
    def translate_select_regexp(self, operations: List[RegexpOperation]) -> Dict[str, Any]:
        """Translate REGEXP operations in SELECT clause to MongoDB projection"""
        projection = {}
        
        for operation in operations:
            if operation.context == 'SELECT':
                field_projection = operation.to_mongodb_projection()
                projection.update(field_projection)
        
        return projection
    
    def translate_where_regexp(self, operations: List[RegexpOperation]) -> List[Dict[str, Any]]:
        """Translate REGEXP operations in WHERE clause to MongoDB match conditions"""
        conditions = []
        
        for operation in operations:
            if operation.context == 'WHERE':
                condition = self._build_match_condition(operation.expression)
                if condition:
                    conditions.append(condition)
        
        return conditions
    
    def translate_having_regexp(self, operations: List[RegexpOperation]) -> List[Dict[str, Any]]:
        """Translate REGEXP operations in HAVING clause to MongoDB match conditions"""
        conditions = []
        
        for operation in operations:
            if operation.context == 'HAVING':
                condition = self._build_match_condition(operation.expression)
                if condition:
                    conditions.append(condition)
        
        return conditions
    
    def _build_match_condition(self, expression: InfixRegexpExpression) -> Optional[Dict[str, Any]]:
        """Build MongoDB match condition for REGEXP expression"""
        field_name = self._extract_field_name(expression.left_operand)
        pattern = self._extract_pattern(expression.right_operand)
        
        if not field_name or not pattern:
            return None
        
        # Build the base regex condition
        base_condition = {
            field_name: {
                "$regex": pattern,
                "$options": "i"  # Case-insensitive by default
            }
        }
        
        # Handle NOT REGEXP
        if expression.operator.upper() == "NOT REGEXP":
            return {field_name: {"$not": {"$regex": pattern, "$options": "i"}}}
        else:
            return base_condition
    
    def _extract_field_name(self, operand: str) -> Optional[str]:
        """Extract field name from left operand"""
        operand = operand.strip()
        
        # Remove table aliases (e.g., 'c.customerName' -> 'customerName')
        if '.' in operand:
            parts = operand.split('.')
            return parts[-1]  # Take the last part (field name)
        
        # Remove quotes from string literals - these should be converted to expressions
        if operand.startswith("'") and operand.endswith("'"):
            # This is a string literal, not a field reference
            return None
        elif operand.startswith('"') and operand.endswith('"'):
            # This is a string literal, not a field reference
            return None
        
        return operand
    
    def _extract_pattern(self, operand: str) -> Optional[str]:
        """Extract regex pattern from right operand"""
        operand = operand.strip()
        
        # Remove quotes from pattern
        if operand.startswith("'") and operand.endswith("'"):
            return operand[1:-1]
        elif operand.startswith('"') and operand.endswith('"'):
            return operand[1:-1]
        
        return operand
    
    def build_aggregation_pipeline(self, operations: List[RegexpOperation], base_pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build complete aggregation pipeline with REGEXP operations"""
        pipeline = base_pipeline.copy()
        
        # Add REGEXP operations to SELECT (project stage)
        select_operations = [op for op in operations if op.context == 'SELECT']
        if select_operations:
            projection = self.translate_select_regexp(select_operations)
            if projection:
                # Find existing $project stage or add new one
                project_stage_index = -1
                for i, stage in enumerate(pipeline):
                    if '$project' in stage:
                        project_stage_index = i
                        break
                
                if project_stage_index >= 0:
                    # Update existing project stage
                    pipeline[project_stage_index]['$project'].update(projection)
                else:
                    # Add new project stage
                    pipeline.append({'$project': projection})
        
        # Add REGEXP operations to WHERE (match stage)
        where_operations = [op for op in operations if op.context == 'WHERE']
        if where_operations:
            conditions = self.translate_where_regexp(where_operations)
            if conditions:
                # Find existing $match stage or add new one
                match_stage_index = -1
                for i, stage in enumerate(pipeline):
                    if '$match' in stage:
                        match_stage_index = i
                        break
                
                if match_stage_index >= 0:
                    # Update existing match stage
                    for condition in conditions:
                        pipeline[match_stage_index]['$match'].update(condition)
                else:
                    # Add new match stage
                    match_stage = {'$match': {}}
                    for condition in conditions:
                        match_stage['$match'].update(condition)
                    pipeline.insert(0, match_stage)
        
        # Add REGEXP operations to HAVING (match stage after group)
        having_operations = [op for op in operations if op.context == 'HAVING']
        if having_operations:
            conditions = self.translate_having_regexp(having_operations)
            if conditions:
                # Add match stage after grouping
                having_stage = {'$match': {}}
                for condition in conditions:
                    having_stage['$match'].update(condition)
                pipeline.append(having_stage)
        
        return pipeline
    
    def translate_regexp_expression_for_projection(self, expression: InfixRegexpExpression, alias: Optional[str] = None) -> Dict[str, Any]:
        """Translate REGEXP expression for use in MongoDB projection/aggregation expressions"""
        field_name = alias or expression.original_expression
        
        # Create MongoDB expression for REGEXP evaluation
        mongo_expr = expression.to_mongodb_expression()
        
        # Return 1/0 like MariaDB REGEXP
        return {
            field_name: {
                "$cond": [mongo_expr, 1, 0]
            }
        }
    
    def is_supported_regexp_operator(self, operator: str) -> bool:
        """Check if the operator is a supported REGEXP operator"""
        return operator.upper() in ['REGEXP', 'RLIKE', 'NOT REGEXP']
