"""
GROUP BY translator for SQL to MongoDB translation
Handles translation of GROUP BY operations to MongoDB aggregation pipelines
"""

from typing import Dict, Any, List
from .groupby_types import GroupByStructure, AggregateFunction


class GroupByTranslator:
    """Translator for GROUP BY operations to MongoDB aggregation pipelines"""
    
    def __init__(self):
        """Initialize the translator"""
        pass
    
    def translate(self, group_by_structure: GroupByStructure, parsed_sql: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate GROUP BY structure to MongoDB aggregation pipeline
        """
        if group_by_structure.is_empty():
            return None
        
        pipeline = []
        
        # Build match stage from WHERE clause
        where_conditions = parsed_sql.get('where', {})
        if where_conditions:
            pipeline.append({"$match": where_conditions})
        
        # Build group stage
        group_stage = self._build_group_stage(group_by_structure)
        pipeline.append(group_stage)
        
        # Handle HAVING clause
        if group_by_structure.having_conditions:
            pipeline.append({"$match": group_by_structure.having_conditions})
        
        # Handle ORDER BY
        orderby_info = parsed_sql.get('order_by', [])
        if orderby_info:
            sort_spec = self._build_sort_stage(orderby_info)
            if sort_spec:
                pipeline.append({"$sort": sort_spec})
        
        # Handle LIMIT
        limit_info = parsed_sql.get('limit')
        if limit_info:
            limit_count = self._extract_limit_count(limit_info)
            if limit_count:
                pipeline.append({"$limit": limit_count})
        
        return {
            'operation': 'aggregate',
            'pipeline': pipeline,
            'collection': parsed_sql.get('from', '')
        }
    
    def _build_group_stage(self, group_by_structure: GroupByStructure) -> Dict[str, Any]:
        """Build the $group stage for the aggregation pipeline"""
        group_stage = {"$group": {"_id": {}}}
        
        # Add GROUP BY fields to _id
        group_fields = group_by_structure.get_group_field_names()
        if group_fields:
            if len(group_fields) == 1:
                # Single field grouping
                field = group_fields[0]
                group_stage["$group"]["_id"] = f"${field}"
            else:
                # Multiple field grouping
                for field in group_fields:
                    group_stage["$group"]["_id"][field] = f"${field}"
        
        # Add aggregate functions
        for agg_func in group_by_structure.aggregate_functions:
            # Use original_call as field name if available, otherwise fall back to constructed name
            alias = agg_func.alias or agg_func.original_call or f"{agg_func.function_name.lower()}_{agg_func.field_name}"
            
            # Handle specific aggregate functions
            if agg_func.function_name == 'COUNT':
                if agg_func.field_name == '*':
                    group_stage["$group"][alias] = {"$sum": 1}
                else:
                    group_stage["$group"][alias] = {"$sum": {"$cond": [{"$ne": [f"${agg_func.field_name}", None]}, 1, 0]}}
            elif agg_func.function_name == 'SUM':
                group_stage["$group"][alias] = {"$sum": f"${agg_func.field_name}"}
            elif agg_func.function_name == 'AVG':
                group_stage["$group"][alias] = {"$avg": f"${agg_func.field_name}"}
            elif agg_func.function_name == 'MAX':
                group_stage["$group"][alias] = {"$max": f"${agg_func.field_name}"}
            elif agg_func.function_name == 'MIN':
                group_stage["$group"][alias] = {"$min": f"${agg_func.field_name}"}
            else:
                # Function not supported
                group_stage["$group"][alias] = {"$literal": f"Function {agg_func.function_name} not supported"}
        
        # Add regular columns as first values (for GROUP BY)
        for col in group_by_structure.regular_columns:
            group_stage["$group"][col] = {"$first": f"${col}"}
        
        return group_stage
    
    def _build_sort_stage(self, orderby_info: List[Dict[str, Any]]) -> Dict[str, int]:
        """Build sort specification from ORDER BY info"""
        sort_spec = {}
        for order_item in orderby_info:
            field = order_item.get('field')
            direction = order_item.get('direction', 'ASC')
            if field:
                sort_spec[field] = 1 if direction.upper() == 'ASC' else -1
        return sort_spec
    
    def _extract_limit_count(self, limit_info: Any) -> int:
        """Extract limit count from limit info"""
        if isinstance(limit_info, dict) and 'count' in limit_info:
            return limit_info['count']
        elif isinstance(limit_info, int):
            return limit_info
        return None
