"""
Enhanced Aggregate Function Translator

This module translates enhanced aggregate functions to MongoDB aggregation pipeline operations.
Handles GROUP_CONCAT, statistical functions, and bitwise aggregations.
"""

from typing import Dict, List, Any
from .enhanced_aggregate_types import (
    EnhancedAggregateOperation,
    GroupConcatFunction,
    StatisticalFunction,
    BitwiseFunction,
    EnhancedAggregateFunctionType
)


class EnhancedAggregateTranslator:
    """Translates enhanced aggregate operations to MongoDB aggregation pipelines"""
    
    def translate_operations(self, operations: List[EnhancedAggregateOperation], base_pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Translate enhanced aggregate operations into MongoDB pipeline"""
        pipeline = base_pipeline.copy()
        
        # Group operations by type for efficient processing
        group_concat_ops = [op for op in operations if isinstance(op.function, GroupConcatFunction)]
        statistical_ops = [op for op in operations if isinstance(op.function, StatisticalFunction)]
        bitwise_ops = [op for op in operations if isinstance(op.function, BitwiseFunction)]
        
        # Add GROUP_CONCAT stages
        if group_concat_ops:
            pipeline = self._add_group_concat_stages(pipeline, group_concat_ops)
        
        # Add statistical function stages
        if statistical_ops:
            pipeline = self._add_statistical_stages(pipeline, statistical_ops)
        
        # Add bitwise function stages
        if bitwise_ops:
            pipeline = self._add_bitwise_stages(pipeline, bitwise_ops)
        
        return pipeline
    
    def _add_group_concat_stages(self, pipeline: List[Dict[str, Any]], operations: List[EnhancedAggregateOperation]) -> List[Dict[str, Any]]:
        """Add GROUP_CONCAT stages to pipeline"""
        for operation in operations:
            group_concat = operation.function
            pipeline.extend(self.translate_group_concat_simple(
                group_concat.field,
                group_concat.separator,
                group_concat.distinct
            ))
        
        return pipeline
    
    def _add_statistical_stages(self, pipeline: List[Dict[str, Any]], operations: List[EnhancedAggregateOperation]) -> List[Dict[str, Any]]:
        """Add statistical function stages to pipeline"""
        # Find or create $group stage
        group_stage_index = self._find_group_stage_index(pipeline)
        
        if group_stage_index >= 0:
            # Add to existing group stage
            group_stage = pipeline[group_stage_index]
            for operation in operations:
                func = operation.function
                field_name = f"{func.function_type.value.lower()}_{func.field}"
                group_stage['$group'][field_name] = self.get_statistical_function_expression(func.function_type, func.field)
        else:
            # Create new group stage
            group_fields = {}
            for operation in operations:
                func = operation.function
                field_name = f"{func.function_type.value.lower()}_{func.field}"
                group_fields[field_name] = self.get_statistical_function_expression(func.function_type, func.field)
            
            pipeline.append({
                '$group': {
                    '_id': None,
                    **group_fields
                }
            })
        
        return pipeline
    
    def _add_bitwise_stages(self, pipeline: List[Dict[str, Any]], operations: List[EnhancedAggregateOperation]) -> List[Dict[str, Any]]:
        """Add bitwise function stages to pipeline"""
        # Find or create $group stage
        group_stage_index = self._find_group_stage_index(pipeline)
        
        if group_stage_index >= 0:
            # Add to existing group stage
            group_stage = pipeline[group_stage_index]
            for operation in operations:
                func = operation.function
                field_name = f"{func.function_type.value.lower()}_{func.field}"
                group_stage['$group'][field_name] = self.get_bitwise_function_expression(func.function_type, func.field)
        else:
            # Create new group stage
            group_fields = {}
            for operation in operations:
                func = operation.function
                field_name = f"{func.function_type.value.lower()}_{func.field}"
                group_fields[field_name] = self.get_bitwise_function_expression(func.function_type, func.field)
            
            pipeline.append({
                '$group': {
                    '_id': None,
                    **group_fields
                }
            })
        
        return pipeline
    
    def _find_group_stage_index(self, pipeline: List[Dict[str, Any]]) -> int:
        """Find the index of existing $group stage in pipeline"""
        for i, stage in enumerate(pipeline):
            if '$group' in stage:
                return i
        return -1
    
    def translate_group_concat_simple(self, field: str, separator: str = ",", distinct: bool = False) -> List[Dict[str, Any]]:
        """Translate simple GROUP_CONCAT to MongoDB pipeline stages"""
        stages = []
        
        # Stage 1: Group and collect values
        if distinct:
            # Use $addToSet for distinct values
            stages.append({
                '$group': {
                    '_id': None,
                    f'group_concat_{field}': {'$addToSet': f'${field}'}
                }
            })
        else:
            # Use $push for all values
            stages.append({
                '$group': {
                    '_id': None,
                    f'group_concat_{field}': {'$push': f'${field}'}
                }
            })
        
        # Stage 2: Sort array if distinct (for deterministic ordering)
        if distinct:
            stages.append({
                '$project': {
                    f'group_concat_{field}': {
                        '$sortArray': {
                            'input': f'$group_concat_{field}',
                            'sortBy': 1
                        }
                    }
                }
            })
        
        # Stage 3: Convert array to concatenated string
        stages.append({
            '$project': {
                f'group_concat_{field}': {
                    '$reduce': {
                        'input': f'$group_concat_{field}',
                        'initialValue': '',
                        'in': {
                            '$cond': {
                                "if": {"$eq": ["$$value", ""]},
                                "then": {"$toString": "$$this"},
                                "else": {"$concat": ["$$value", separator, {"$toString": "$$this"}]}
                            }
                        }
                    }
                }
            }
        })
        
        return stages
    
    def get_statistical_function_expression(self, func_type: EnhancedAggregateFunctionType, field: str) -> Dict[str, Any]:
        """Get MongoDB aggregation expression for statistical functions with MariaDB precision"""
        if func_type == EnhancedAggregateFunctionType.STDDEV_POP:
            return {"$round": [{"$stdDevPop": f"${field}"}, 6]}
        elif func_type == EnhancedAggregateFunctionType.STDDEV_SAMP:
            return {"$round": [{"$stdDevSamp": f"${field}"}, 6]}
        elif func_type == EnhancedAggregateFunctionType.VAR_POP:
            return {"$round": [{"$pow": [{"$stdDevPop": f"${field}"}, 2]}, 6]}
        elif func_type == EnhancedAggregateFunctionType.VAR_SAMP:
            return {"$round": [{"$pow": [{"$stdDevSamp": f"${field}"}, 2]}, 6]}
        else:
            raise ValueError(f"Unsupported statistical function: {func_type}")
    
    def get_bitwise_function_expression(self, func_type: EnhancedAggregateFunctionType, field: str) -> Dict[str, Any]:
        """Get MongoDB aggregation expression for bitwise functions"""
        if func_type == EnhancedAggregateFunctionType.BIT_AND:
            return {"$bitAnd": f"${field}"}
        elif func_type == EnhancedAggregateFunctionType.BIT_OR:
            return {"$bitOr": f"${field}"}
        elif func_type == EnhancedAggregateFunctionType.BIT_XOR:
            return {"$bitXor": f"${field}"}
        else:
            raise ValueError(f"Unsupported bitwise function: {func_type}")
