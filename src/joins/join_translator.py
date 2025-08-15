"""
JOIN translator - converts JOIN operations to MongoDB aggregation pipelines
"""
from typing import List, Dict, Any, Optional
from .join_types import JoinOperation, JoinType, get_join_handler

class JoinTranslator:
    """Translates JOIN operations to MongoDB aggregation pipelines"""
    
    def __init__(self):
        pass
    
    def translate_joins_to_pipeline(self, joins: List[JoinOperation], base_collection: str) -> List[Dict[str, Any]]:
        """Convert JOIN operations to MongoDB aggregation pipeline stages"""
        if not joins:
            return []
        
        pipeline = []
        previous_joins = []  # Track previous joins for field resolution
        
        for join_op in joins:
            # Update left table if not set (use base collection for first join)
            if not join_op.left_table:
                join_op.left_table = base_collection
            
            # Get handler for this JOIN type
            handler = get_join_handler(join_op.join_type)
            
            # Add $lookup stage with context of previous joins
            lookup_stage = self._create_enhanced_lookup_stage(join_op, handler, previous_joins)
            pipeline.append(lookup_stage)
            
            # Add $unwind stage if needed
            if handler.requires_unwind():
                unwind_stage = self._create_unwind_stage(join_op, handler)
                pipeline.append(unwind_stage)
            
            # Add $match stage for filtering if needed
            match_stage = handler.create_match_stage(join_op)
            if match_stage:
                pipeline.append(match_stage)
            
            # Track this join for future reference
            previous_joins.append(join_op)
        
        return pipeline
    
    def _create_enhanced_lookup_stage(self, join_op: JoinOperation, handler, previous_joins: List[JoinOperation]) -> Dict[str, Any]:
        """Create $lookup stage considering previous joins"""
        # For RIGHT JOIN, use the handler's logic directly
        if join_op.join_type == JoinType.RIGHT:
            return handler.create_lookup_stage(join_op)
        
        # For other JOIN types, use enhanced logic
        condition = join_op.conditions[0]  # Handle single condition for now
        
        # Determine the correct localField based on previous joins
        local_field = condition.left_column
        
        # Check if the left side references a previously joined table
        for prev_join in previous_joins:
            if (condition.left_table == prev_join.right_table or 
                condition.left_table == prev_join.alias_right):
                # This field comes from a previous join
                local_field = f"{prev_join.right_table}_joined.{condition.left_column}"
                break
        
        return {
            "$lookup": {
                "from": join_op.right_table,
                "localField": local_field,
                "foreignField": condition.right_column,
                "as": f"{join_op.right_table}_joined"
            }
        }

    def _create_unwind_stage(self, join_op: JoinOperation, handler) -> Dict[str, Any]:
        """Create $unwind stage for JOIN operation"""
        if join_op.join_type == JoinType.RIGHT:
            # RIGHT JOIN: unwind the left table that was joined
            field_path = f"${join_op.left_table}_joined"
        else:
            # LEFT/INNER JOIN: unwind the right table that was joined
            field_path = f"${join_op.right_table}_joined"
        
        if join_op.join_type in [JoinType.LEFT, JoinType.RIGHT]:
            # LEFT/RIGHT JOIN preserves documents even if joined array is empty
            return {
                "$unwind": {
                    "path": field_path,
                    "preserveNullAndEmptyArrays": True
                }
            }
        else:
            # INNER JOIN and others
            return {
                "$unwind": field_path
            }
    
    def create_projection_with_joins(self, columns: List[str], joins: List[JoinOperation], 
                                   base_collection: str) -> Dict[str, Any]:
        """Create projection stage that handles joined table columns"""
        projection = {"_id": 0}  # Exclude MongoDB _id by default
        
        # Map of table aliases to actual table names
        table_map = {base_collection: base_collection}
        
        for join_op in joins:
            if join_op.join_type == JoinType.RIGHT:
                # For RIGHT JOIN, add both left and right table mappings
                if join_op.alias_left:
                    table_map[join_op.alias_left] = join_op.left_table
                if join_op.alias_right:
                    table_map[join_op.alias_right] = join_op.right_table
                table_map[join_op.left_table] = join_op.left_table
                table_map[join_op.right_table] = join_op.right_table
            else:
                # For INNER/LEFT JOIN
                if join_op.alias_right:
                    table_map[join_op.alias_right] = join_op.right_table
                table_map[join_op.right_table] = join_op.right_table
        
        # Process each column
        for col in columns:
            if col == '*':
                # Include all fields from base collection
                projection.update(self._get_all_fields_projection(base_collection, joins))
            else:
                # Handle specific column
                proj_entry = self._create_column_projection(col, table_map, joins)
                if proj_entry:
                    projection.update(proj_entry)
        
        return {"$project": projection}
    
    def _get_all_fields_projection(self, base_collection: str, joins: List[JoinOperation]) -> Dict[str, Any]:
        """Create projection for SELECT * with JOINs"""
        projection = {}
        
        # Include all base collection fields (except _id)
        # This would need schema information in a real implementation
        projection["*"] = 1
        
        # Include joined table fields
        for join_op in joins:
            joined_field = f"{join_op.right_table}_joined"
            projection[f"{join_op.right_table}.*"] = f"${joined_field}"
        
        return projection
    
    def _create_column_projection(self, column: str, table_map: Dict[str, str], 
                                joins: List[JoinOperation]) -> Optional[Dict[str, Any]]:
        """Create projection for a specific column"""
        # Handle table.column format
        if '.' in column:
            table_part, col_part = column.split('.', 1)
            
            # Check if it's a joined table
            actual_table = table_map.get(table_part, table_part)
            
            # Find if this is from a joined table
            for join_op in joins:
                if join_op.join_type == JoinType.RIGHT:
                    # For RIGHT JOIN, check both left and right tables
                    if (join_op.left_table == actual_table or 
                        join_op.alias_left == table_part):
                        # Field from left table (which was joined)
                        joined_field = f"{join_op.left_table}_joined"
                        return {col_part: f"${joined_field}.{col_part}"}
                    elif (join_op.right_table == actual_table or 
                          join_op.alias_right == table_part):
                        # Field from right table (base collection)
                        return {col_part: f"${col_part}"}
                else:
                    # For INNER/LEFT JOIN
                    if (join_op.right_table == actual_table or 
                        join_op.alias_right == table_part):
                        # Field from joined table - use just the column name as key
                        joined_field = f"{join_op.right_table}_joined"
                        return {col_part: f"${joined_field}.{col_part}"}
            
            # Field from base table - use just the column name as key
            return {col_part: f"${col_part}"}
        else:
            # Simple column name - assume from base table
            return {column: 1}
    
    def optimize_pipeline_for_mongodb(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize the aggregation pipeline for better MongoDB performance"""
        optimized = []
        
        # Group consecutive $match stages
        current_match = {}
        
        for stage in pipeline:
            if "$match" in stage:
                # Merge with existing match conditions
                current_match.update(stage["$match"])
            else:
                # If we have accumulated match conditions, add them first
                if current_match:
                    optimized.append({"$match": current_match})
                    current_match = {}
                
                optimized.append(stage)
        
        # Add any remaining match conditions
        if current_match:
            optimized.append({"$match": current_match})
        
        return optimized
    
    def _adjust_where_fields_for_joins(self, match_filter: Dict[str, Any], joins: List[JoinOperation], base_collection: str) -> Dict[str, Any]:
        """Adjust field names in WHERE clause for JOIN context"""
        adjusted_filter = {}
        
        for field, condition in match_filter.items():
            # Handle special MongoDB operators like $or, $and
            if field in ['$or', '$and']:
                # Recursively adjust field names in each condition
                adjusted_conditions = []
                for sub_condition in condition:
                    adjusted_sub_condition = self._adjust_where_fields_for_joins(sub_condition, joins, base_collection)
                    adjusted_conditions.append(adjusted_sub_condition)
                adjusted_filter[field] = adjusted_conditions
            elif '.' in field:
                # Check if field has table prefix (e.g., c.customerName)
                table_alias, column_name = field.split('.', 1)
                
                # Find which table this refers to and map to correct field
                mapped_field = None
                
                # Check if it's the base collection
                if base_collection.startswith(table_alias) or table_alias == base_collection:
                    mapped_field = column_name
                else:
                    # Check if it's from a joined table
                    for join_op in joins:
                        if join_op.join_type == JoinType.RIGHT:
                            # For RIGHT JOIN, left table is joined
                            if (join_op.alias_left == table_alias or 
                                join_op.left_table == table_alias):
                                mapped_field = f"{join_op.left_table}_joined.{column_name}"
                                break
                            elif (join_op.alias_right == table_alias or 
                                  join_op.right_table == table_alias):
                                mapped_field = column_name  # Right table is base
                                break
                        else:
                            # For INNER/LEFT JOIN, right table is joined
                            if (join_op.alias_right == table_alias or 
                                join_op.right_table == table_alias):
                                mapped_field = f"{join_op.right_table}_joined.{column_name}"
                                break
                            elif (join_op.alias_left == table_alias or 
                                  join_op.left_table == table_alias):
                                mapped_field = column_name  # Left table is base
                                break
                
                if mapped_field:
                    adjusted_filter[mapped_field] = condition
                else:
                    # Fallback: use original field
                    adjusted_filter[field] = condition
            else:
                # No table prefix, use as-is
                adjusted_filter[field] = condition
        
        return adjusted_filter
    
    def translate_join_query(self, parsed_sql: Dict[str, Any]) -> Dict[str, Any]:
        """Translate a complete SQL query with JOINs to MongoDB aggregation"""
        joins = parsed_sql.get('joins', [])
        base_collection = parsed_sql.get('from')
        
        if not joins:
            # No JOINs, return regular find() operation
            return None
        
        # For RIGHT JOIN, we need to start from the right table
        if joins and joins[0].join_type == JoinType.RIGHT:
            base_collection = joins[0].right_table
            # Also need to swap the lookup logic for RIGHT JOIN
        
        # Start building aggregation pipeline
        pipeline = []
        
        # Add JOIN stages
        join_stages = self.translate_joins_to_pipeline(joins, base_collection)
        pipeline.extend(join_stages)
        
        # Add WHERE conditions
        if parsed_sql.get('where'):
            # Use standalone WHERE translator to avoid circular imports
            from ..translators.where_translator import WhereTranslator
            where_translator = WhereTranslator()
            match_filter = where_translator.translate_where(parsed_sql['where'])
            if match_filter:  # Only add if translation successful
                # Adjust field names for JOIN context
                adjusted_filter = self._adjust_where_fields_for_joins(match_filter, joins, base_collection)
                if adjusted_filter:
                    match_stage = {"$match": adjusted_filter}
                    pipeline.append(match_stage)
        
        # Add projection
        columns = parsed_sql.get('columns', ['*'])
        projection = self.create_projection_with_joins(columns, joins, base_collection)
        pipeline.append(projection)
        
        # Add ORDER BY
        if parsed_sql.get('order_by'):
            sort_stage = {"$sort": parsed_sql['order_by']}
            pipeline.append(sort_stage)
        
        # Add LIMIT
        if parsed_sql.get('limit'):
            limit_value = parsed_sql['limit']
            if isinstance(limit_value, dict) and 'count' in limit_value:
                limit_stage = {"$limit": limit_value['count']}
            else:
                limit_stage = {"$limit": limit_value}
            pipeline.append(limit_stage)
        
        # Optimize pipeline
        pipeline = self.optimize_pipeline_for_mongodb(pipeline)
        
        return {
            'operation': 'aggregate',
            'collection': base_collection,
            'pipeline': pipeline
        }
