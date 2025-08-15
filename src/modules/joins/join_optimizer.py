"""
JOIN optimizer - optimizes JOIN operations for better MongoDB performance
"""
from typing import List, Dict, Any
from .join_types import JoinOperation, JoinType

class JoinOptimizer:
    """Optimizes JOIN operations for MongoDB aggregation pipelines"""
    
    def __init__(self):
        pass
    
    def optimize_join_order(self, joins: List[JoinOperation]) -> List[JoinOperation]:
        """Optimize the order of JOIN operations for better performance"""
        if len(joins) <= 1:
            return joins
        
        # Simple optimization: put INNER JOINs before LEFT JOINs
        # This reduces the dataset size early in the pipeline
        inner_joins = [j for j in joins if j.join_type == JoinType.INNER]
        left_joins = [j for j in joins if j.join_type == JoinType.LEFT]
        other_joins = [j for j in joins if j.join_type not in [JoinType.INNER, JoinType.LEFT]]
        
        return inner_joins + other_joins + left_joins
    
    def add_early_filtering(self, pipeline: List[Dict[str, Any]], 
                          where_conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Add WHERE conditions as early as possible in the pipeline"""
        if not where_conditions:
            return pipeline
        
        optimized = []
        early_conditions = {}
        late_conditions = {}
        
        # Separate conditions that can be applied early vs late
        for field, condition in where_conditions.items():
            if self._can_apply_early(field, pipeline):
                early_conditions[field] = condition
            else:
                late_conditions[field] = condition
        
        # Add early conditions at the beginning
        if early_conditions:
            optimized.append({"$match": early_conditions})
        
        # Add the rest of the pipeline
        optimized.extend(pipeline)
        
        # Add late conditions after JOINs
        if late_conditions:
            optimized.append({"$match": late_conditions})
        
        return optimized
    
    def _can_apply_early(self, field: str, pipeline: List[Dict[str, Any]]) -> bool:
        """Check if a WHERE condition can be applied before JOINs"""
        # If field contains a dot, check if it's from a joined table
        if '.' in field:
            table_part = field.split('.')[0]
            
            # Check if this table appears in any $lookup operations
            for stage in pipeline:
                if "$lookup" in stage:
                    lookup = stage["$lookup"]
                    if (lookup.get("from") == table_part or 
                        lookup.get("as", "").startswith(table_part)):
                        return False
        
        return True
    
    def suggest_indexes(self, joins: List[JoinOperation], 
                       base_collection: str) -> List[Dict[str, Any]]:
        """Suggest indexes that would improve JOIN performance"""
        suggestions = []
        
        # Index on base collection
        for join_op in joins:
            if join_op.conditions:
                condition = join_op.conditions[0]  # First condition
                
                # Suggest index on the local field (base collection)
                suggestions.append({
                    "collection": base_collection,
                    "index": {condition.left_column: 1},
                    "reason": f"Improves JOIN with {join_op.right_table}"
                })
                
                # Suggest index on the foreign field (joined collection)
                suggestions.append({
                    "collection": join_op.right_table,
                    "index": {condition.right_column: 1},
                    "reason": f"Improves JOIN from {base_collection}"
                })
        
        return suggestions
    
    def estimate_result_size(self, joins: List[JoinOperation]) -> str:
        """Estimate the relative size of the result set"""
        if not joins:
            return "SMALL"
        
        # Simple heuristic based on JOIN types
        inner_count = sum(1 for j in joins if j.join_type == JoinType.INNER)
        left_count = sum(1 for j in joins if j.join_type == JoinType.LEFT)
        cross_count = sum(1 for j in joins if j.join_type == JoinType.CROSS)
        
        if cross_count > 0:
            return "VERY_LARGE"
        elif inner_count > 2 or left_count > 3:
            return "LARGE"
        elif inner_count > 0 or left_count > 1:
            return "MEDIUM"
        else:
            return "SMALL"
    
    def optimize_aggregation_pipeline(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply various optimizations to the aggregation pipeline"""
        optimized = list(pipeline)
        
        # Move $match stages as early as possible
        optimized = self._move_match_stages_early(optimized)
        
        # Combine consecutive $match stages
        optimized = self._combine_match_stages(optimized)
        
        # Add helpful $hint stages for complex JOINs
        optimized = self._add_performance_hints(optimized)
        
        return optimized
    
    def _move_match_stages_early(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Move $match stages before $lookup when possible"""
        optimized = []
        pending_matches = []
        
        for stage in pipeline:
            if "$match" in stage:
                pending_matches.append(stage)
            elif "$lookup" in stage:
                # Add any compatible matches before this lookup
                compatible_matches = []
                remaining_matches = []
                
                for match_stage in pending_matches:
                    if self._match_compatible_with_lookup(match_stage, stage):
                        compatible_matches.append(match_stage)
                    else:
                        remaining_matches.append(match_stage)
                
                optimized.extend(compatible_matches)
                optimized.append(stage)
                pending_matches = remaining_matches
            else:
                optimized.append(stage)
        
        # Add any remaining matches at the end
        optimized.extend(pending_matches)
        
        return optimized
    
    def _match_compatible_with_lookup(self, match_stage: Dict[str, Any], 
                                    lookup_stage: Dict[str, Any]) -> bool:
        """Check if a $match stage can be placed before a $lookup stage"""
        match_fields = set(match_stage["$match"].keys())
        lookup_from = lookup_stage["$lookup"].get("from", "")
        
        # If match operates on fields from the collection being looked up, 
        # it should come after the lookup
        for field in match_fields:
            if field.startswith(lookup_from):
                return False
        
        return True
    
    def _combine_match_stages(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine consecutive $match stages"""
        if not pipeline:
            return pipeline
        
        optimized = []
        current_match = None
        
        for stage in pipeline:
            if "$match" in stage:
                if current_match is None:
                    current_match = {"$match": dict(stage["$match"])}
                else:
                    # Merge conditions
                    current_match["$match"].update(stage["$match"])
            else:
                # Add accumulated match stage if any
                if current_match:
                    optimized.append(current_match)
                    current_match = None
                
                optimized.append(stage)
        
        # Add final match stage if any
        if current_match:
            optimized.append(current_match)
        
        return optimized
    
    def _add_performance_hints(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add performance hints for complex pipelines"""
        # For now, just return the pipeline as-is
        # In a real implementation, this could add $hint stages
        # or reorder operations for better performance
        return pipeline
