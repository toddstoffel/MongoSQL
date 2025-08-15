"""
ORDER BY translation to MongoDB aggregation pipeline
"""
from typing import Dict, Any, List, Optional
from .orderby_types import OrderByClause, OrderField, SortDirection

class OrderByTranslator:
    """Translates ORDER BY clauses to MongoDB aggregation pipeline stages"""
    
    def __init__(self):
        self.field_mappings = {}
    
    def translate(self, order_by: OrderByClause, collection_schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Translate ORDER BY clause to MongoDB $sort stage
        
        Args:
            order_by: Parsed ORDER BY clause
            collection_schema: Optional schema information for field validation
            
        Returns:
            MongoDB $sort aggregation stage
        """
        if order_by.is_empty():
            return {}
        
        sort_spec = {}
        
        for field in order_by.fields:
            # Map field name if needed
            mongo_field = self._map_field_name(field.field, collection_schema)
            
            # Convert direction to MongoDB sort value
            sort_value = 1 if field.direction == SortDirection.ASC else -1
            sort_spec[mongo_field] = sort_value
        
        return {"$sort": sort_spec}
    
    def _map_field_name(self, field_name: str, schema: Optional[Dict] = None) -> str:
        """
        Map SQL field name to MongoDB field name
        
        Args:
            field_name: SQL field name
            schema: Optional collection schema
            
        Returns:
            MongoDB field name
        """
        # Handle function calls in ORDER BY
        if field_name.startswith('(') and field_name.endswith(')'):
            # This is likely a function result, keep as-is for now
            return field_name
        
        # Check for field mappings
        if field_name in self.field_mappings:
            return self.field_mappings[field_name]
        
        # Use schema if available to validate field exists
        if schema and 'fields' in schema:
            if field_name in schema['fields']:
                return field_name
            
            # Try case-insensitive match
            for schema_field in schema['fields']:
                if schema_field.lower() == field_name.lower():
                    return schema_field
        
        # Default: return field name as-is
        return field_name
    
    def add_field_mapping(self, sql_field: str, mongo_field: str):
        """
        Add a field name mapping from SQL to MongoDB
        
        Args:
            sql_field: SQL field name
            mongo_field: Corresponding MongoDB field name
        """
        self.field_mappings[sql_field] = mongo_field
    
    def get_sort_pipeline_stage(self, order_by: OrderByClause, collection_schema: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Get ORDER BY as a list of pipeline stages
        
        Args:
            order_by: Parsed ORDER BY clause
            collection_schema: Optional schema information
            
        Returns:
            List containing $sort stage (empty list if no ORDER BY)
        """
        sort_stage = self.translate(order_by, collection_schema)
        
        if sort_stage:
            return [sort_stage]
        else:
            return []
