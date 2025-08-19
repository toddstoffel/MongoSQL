"""
Enhanced Aggregate Function Mapper

This module provides integration between the enhanced aggregate module and the main translator.
Maps enhanced aggregate operations and provides hooks for core translator integration.
"""

from typing import Dict, Any, List, Optional, Tuple
from .enhanced_aggregate_parser import EnhancedAggregateParser
from .enhanced_aggregate_translator import EnhancedAggregateTranslator
from .enhanced_aggregate_types import (
    EnhancedAggregateOperation,
    GroupConcatFunction,
    StatisticalFunction,
    BitwiseFunction,
    is_enhanced_aggregate_function
)


class EnhancedAggregateFunctionMapper:
    """Maps enhanced aggregate operations for integration with core translator"""
    
    def __init__(self):
        self.parser = EnhancedAggregateParser()
        self.translator = EnhancedAggregateTranslator()
    
    def has_enhanced_aggregate_functions(self, sql: str) -> bool:
        """Check if SQL contains enhanced aggregate functions"""
        return self.parser.has_enhanced_aggregate_functions(sql)
    
    def parse_and_translate_enhanced_aggregates(self, sql: str, base_pipeline: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[EnhancedAggregateOperation]]:
        """Parse SQL for enhanced aggregate operations and integrate with pipeline"""
        operations = self.parser.parse_sql(sql)
        
        if not operations:
            return base_pipeline, []
        
        # Build enhanced pipeline with aggregate operations
        enhanced_pipeline = self.translator.translate_operations(operations, base_pipeline)
        
        return enhanced_pipeline, operations
    
    def get_group_concat_projections(self, sql: str) -> Dict[str, Any]:
        """Get projection mappings for GROUP_CONCAT in SELECT expressions"""
        operations = self.parser.parse_sql(sql)
        group_concat_operations = [op for op in operations if isinstance(op.function, GroupConcatFunction)]
        
        if not group_concat_operations:
            return {}
        
        projections = {}
        for operation in group_concat_operations:
            field_name = f"group_concat_{operation.function.field}"
            projections[field_name] = f"${field_name}"
        
        return projections
    
    def get_statistical_projections(self, sql: str) -> Dict[str, Any]:
        """Get projection mappings for statistical functions in SELECT expressions"""
        operations = self.parser.parse_sql(sql)
        statistical_operations = [op for op in operations if isinstance(op.function, StatisticalFunction)]
        
        if not statistical_operations:
            return {}
        
        projections = {}
        for operation in statistical_operations:
            func_name = operation.function.function_type.value
            field_name = f"{func_name.lower()}_{operation.function.field}"
            projections[field_name] = operation.function.to_mongodb_aggregation()
        
        return projections
    
    def get_bitwise_projections(self, sql: str) -> Dict[str, Any]:
        """Get projection mappings for bitwise functions in SELECT expressions"""
        operations = self.parser.parse_sql(sql)
        bitwise_operations = [op for op in operations if isinstance(op.function, BitwiseFunction)]
        
        if not bitwise_operations:
            return {}
        
        projections = {}
        for operation in bitwise_operations:
            func_name = operation.function.function_type.value
            field_name = f"{func_name.lower()}_{operation.function.field}"
            projections[field_name] = operation.function.to_mongodb_aggregation()
        
        return projections
    
    def translate_group_concat_simple(self, field: str, separator: str = ",", distinct: bool = False) -> List[Dict[str, Any]]:
        """Simple GROUP_CONCAT translation helper"""
        return self.translator.translate_group_concat_simple(field, separator, distinct)
    
    def is_supported_enhanced_aggregate(self, function_name: str) -> bool:
        """Check if the function is a supported enhanced aggregate function"""
        return is_enhanced_aggregate_function(function_name)
    
    def get_supported_functions(self) -> List[str]:
        """Get list of supported enhanced aggregate functions"""
        return [
            'GROUP_CONCAT', 
            'STDDEV_POP', 'STDDEV_SAMP', 
            'VAR_POP', 'VAR_SAMP',
            'BIT_AND', 'BIT_OR', 'BIT_XOR'
        ]
    
    def map_enhanced_aggregate_function(self, function_name: str, args: str, original_call: str) -> Optional[Dict[str, Any]]:
        """Map a specific enhanced aggregate function call to MongoDB operations"""
        function_name_upper = function_name.upper()
        
        if function_name_upper == 'GROUP_CONCAT':
            return self._map_group_concat(args, original_call)
        elif function_name_upper in ['STDDEV_POP', 'STDDEV_SAMP', 'VAR_POP', 'VAR_SAMP']:
            return self._map_statistical_function(function_name_upper, args, original_call)
        elif function_name_upper in ['BIT_AND', 'BIT_OR', 'BIT_XOR']:
            return self._map_bitwise_function(function_name_upper, args, original_call)
        
        return None
    
    def _map_group_concat(self, args: str, original_call: str) -> Dict[str, Any]:
        """Map GROUP_CONCAT function"""
        # Extract field name from args  
        field = self._extract_field_from_args(args)
        
        # Return GROUP_CONCAT pipeline stages
        return {
            "type": "group_concat",
            "field": field,
            "pipeline": self.translator.translate_group_concat_simple(field)
        }
    
    def _map_statistical_function(self, function_name: str, args: str, original_call: str) -> Dict[str, Any]:
        """Map statistical functions with MariaDB precision in the expected format"""
        # Extract field name from args
        field = self._extract_field_from_args(args)
        
        # Create function type and get MongoDB expression with precision
        from .enhanced_aggregate_types import EnhancedAggregateFunctionType
        func_type = EnhancedAggregateFunctionType(function_name)
        
        # Return in the format expected by the core translator
        return {
            'operator': self.translator.get_statistical_function_expression(func_type, field),
            'value': f'${field}',  # This will be ignored since we use the full expression in operator
            'stage': '$group'
        }
    
    def _map_bitwise_function(self, function_name: str, args: str, original_call: str) -> Dict[str, Any]:
        """Map bitwise functions"""
        # Extract field name from args
        field = self._extract_field_from_args(args)
        
        # Create function type and get MongoDB expression
        from .enhanced_aggregate_types import EnhancedAggregateFunctionType
        func_type = EnhancedAggregateFunctionType(function_name)
        
        return {
            "type": "bitwise",
            "function": function_name,
            "field": field,
            "expression": self.translator.get_bitwise_function_expression(func_type, field)
        }
    
    def _extract_field_from_args(self, args: str) -> str:
        """Extract field name from function arguments"""
        # Handle different argument formats
        if isinstance(args, list) and len(args) > 0:
            return str(args[0])
        
        # Handle string representation of list: "['fieldname']"
        args_str = str(args).strip()
        if args_str.startswith("['") and args_str.endswith("']"):
            # Extract from "['fieldname']" format
            field = args_str[2:-2]  # Remove [' and ']
            return field
        elif args_str.startswith('[') and args_str.endswith(']'):
            # Extract from "[fieldname]" format
            field = args_str[1:-1]  # Remove [ and ]
            return field.strip().strip("'\"")
        elif args_str.startswith('(') and args_str.endswith(')'):
            # Extract from "(fieldname)" format
            field = args_str[1:-1]  # Remove ( and )
            return field.strip().strip("'\"")
        else:
            # Simple field name
            return args_str.strip().strip("'\"")


# Global instance for easy access
enhanced_aggregate_mapper = EnhancedAggregateFunctionMapper()
