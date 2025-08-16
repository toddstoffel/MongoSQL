"""
Subquery translator - converts subqueries to MongoDB aggregation pipelines
"""
from typing import List, Dict, Any, Optional
from .subquery_types import SubqueryType, SubqueryOperation
from .subquery_parser import SubqueryParser

class SubqueryTranslator:
    """Translates subqueries to MongoDB aggregation operations"""
    
    def __init__(self):
        self.parser = SubqueryParser()
        self.debug = False
    
    def translate_subqueries_to_pipeline(self, subqueries: List[SubqueryOperation], 
                                       base_collection: str) -> List[Dict[str, Any]]:
        """Convert subqueries to MongoDB aggregation pipeline stages"""
        if not subqueries:
            return []
        
        pipeline = []
        
        for subquery_op in subqueries:
            if subquery_op.subquery_type == SubqueryType.SCALAR:
                stages = self._translate_scalar_subquery(subquery_op, base_collection)
            elif subquery_op.subquery_type == SubqueryType.IN_LIST:
                stages = self._translate_in_subquery(subquery_op, base_collection)
            elif subquery_op.subquery_type == SubqueryType.EXISTS:
                stages = self._translate_exists_subquery(subquery_op, base_collection)
            elif subquery_op.subquery_type == SubqueryType.ROW:
                stages = self._translate_row_subquery(subquery_op, base_collection)
            elif subquery_op.subquery_type == SubqueryType.DERIVED:
                stages = self._translate_derived_subquery(subquery_op, base_collection)
            else:
                if self.debug:
                    print(f"Unsupported subquery type: {subquery_op.subquery_type}")
                continue
                
            pipeline.extend(stages)
        
        return pipeline
    
    def _translate_scalar_subquery(self, subquery_op: SubqueryOperation, 
                                 base_collection: str) -> List[Dict[str, Any]]:
        """Translate scalar subquery to MongoDB pipeline"""
        stages = []
        
        # Step 1: Get the scalar value from subquery using $lookup
        lookup_stage = {
            "$lookup": {
                "from": subquery_op.inner_collection,
                "pipeline": self._build_subquery_pipeline(subquery_op.inner_query),
                "as": f"subquery_{subquery_op.inner_collection}"
            }
        }
        stages.append(lookup_stage)
        
        # Check if this is a WHERE clause comparison (has outer_field) or SELECT clause subquery
        if subquery_op.outer_field:
            # WHERE clause: field = (SELECT ...) - add comparison match
            match_stage = {
                "$match": {
                    "$expr": {
                        "$eq": [
                            f"${subquery_op.outer_field}",
                            {
                                "$arrayElemAt": [
                                    f"$subquery_{subquery_op.inner_collection}.{subquery_op.inner_field}",
                                    0
                                ]
                            }
                        ]
                    }
                }
            }
            stages.append(match_stage)
            
            # Clean up temporary fields for WHERE clause
            project_stage = {
                "$project": {
                    f"subquery_{subquery_op.inner_collection}": 0
                }
            }
            stages.append(project_stage)
        else:
            # SELECT clause: (SELECT ...) as alias - add as field using $addFields
            # Note: The final projection will handle the field mapping
            # For now, just keep the lookup result for later processing
            pass
        
        return stages
        stages.append(project_stage)
        
        return stages
    
    def _translate_in_subquery(self, subquery_op: SubqueryOperation, 
                             base_collection: str) -> List[Dict[str, Any]]:
        """Translate IN subquery to MongoDB pipeline"""
        # For IN subquery: field IN (SELECT field FROM table ...)
        # We need to get all values from subquery and use $in
        
        stages = []
        
        # Step 1: Get all values from subquery
        lookup_stage = {
            "$lookup": {
                "from": subquery_op.inner_collection,
                "pipeline": self._build_subquery_pipeline(subquery_op.inner_query),
                "as": f"subquery_{subquery_op.inner_collection}"
            }
        }
        stages.append(lookup_stage)
        
        # Step 2: Match using $in with array of values
        match_stage = {
            "$match": {
                "$expr": {
                    "$in": [
                        f"${subquery_op.outer_field}",
                        f"$subquery_{subquery_op.inner_collection}.{subquery_op.inner_field}"
                    ]
                }
            }
        }
        stages.append(match_stage)
        
        # Step 3: Clean up temporary fields
        project_stage = {
            "$project": {
                f"subquery_{subquery_op.inner_collection}": 0
            }
        }
        stages.append(project_stage)
        
        return stages
    
    def _translate_exists_subquery(self, subquery_op: SubqueryOperation, 
                                 base_collection: str) -> List[Dict[str, Any]]:
        """Translate EXISTS subquery to MongoDB pipeline"""
        # For EXISTS subquery: EXISTS (SELECT 1 FROM table WHERE correlation)
        # We need to check if any matching documents exist
        
        stages = []
        
        # Check if this is a correlated EXISTS
        if self._is_correlated_exists(subquery_op):
            # Use $lookup with correlation
            lookup_stage = {
                "$lookup": {
                    "from": subquery_op.inner_collection,
                    "let": self._build_correlation_let(subquery_op),
                    "pipeline": self._build_correlated_pipeline(subquery_op),
                    "as": f"exists_{subquery_op.inner_collection}"
                }
            }
            stages.append(lookup_stage)
            
            # Match only documents where lookup found results
            match_stage = {
                "$match": {
                    "$expr": {
                        "$gt": [
                            {"$size": f"$exists_{subquery_op.inner_collection}"},
                            0
                        ]
                    }
                }
            }
            stages.append(match_stage)
            
        else:
            # Non-correlated EXISTS - simpler approach
            lookup_stage = {
                "$lookup": {
                    "from": subquery_op.inner_collection,
                    "pipeline": self._build_subquery_pipeline(subquery_op.inner_query),
                    "as": f"exists_{subquery_op.inner_collection}"
                }
            }
            stages.append(lookup_stage)
            
            match_stage = {
                "$match": {
                    "$expr": {
                        "$gt": [
                            {"$size": f"$exists_{subquery_op.inner_collection}"},
                            0
                        ]
                    }
                }
            }
            stages.append(match_stage)
        
        # Clean up temporary fields
        project_stage = {
            "$project": {
                f"exists_{subquery_op.inner_collection}": 0
            }
        }
        stages.append(project_stage)
        
        return stages
    
    def _translate_row_subquery(self, subquery_op: SubqueryOperation, 
                               base_collection: str) -> List[Dict[str, Any]]:
        """Translate ROW subquery to MongoDB pipeline"""
        # ROW subquery: (field1, field2) = (SELECT field1, field2 FROM ...)
        # Strategy: Use $lookup to get subquery result, then match on multiple fields
        
        stages = []
        
        # Parse outer fields from comma-separated string
        outer_fields = [f.strip() for f in subquery_op.outer_field.split(',')]
        
        # Step 1: Get the tuple values from subquery using $lookup
        lookup_stage = {
            "$lookup": {
                "from": subquery_op.inner_collection,
                "pipeline": self._build_subquery_pipeline(subquery_op.inner_query),
                "as": f"subquery_{subquery_op.inner_collection}"
            }
        }
        stages.append(lookup_stage)
        
        # Step 2: Match documents where all fields in the tuple match
        # For ROW subquery, we need to match each field in the tuple
        match_conditions = []
        
        for i, outer_field in enumerate(outer_fields):
            # Create condition for each field in the tuple
            condition = {
                "$eq": [
                    f"${outer_field}",
                    {
                        "$arrayElemAt": [
                            f"$subquery_{subquery_op.inner_collection}.{outer_field}",
                            0
                        ]
                    }
                ]
            }
            match_conditions.append(condition)
        
        # Combine all conditions with $and
        if len(match_conditions) == 1:
            match_expr = match_conditions[0]
        else:
            match_expr = {"$and": match_conditions}
        
        match_stage = {
            "$match": {
                "$expr": match_expr
            }
        }
        stages.append(match_stage)
        
        # Step 3: Clean up temporary fields
        project_stage = {
            "$project": {
                f"subquery_{subquery_op.inner_collection}": 0
            }
        }
        stages.append(project_stage)
        
        return stages
    
    def _translate_derived_subquery(self, subquery_op: SubqueryOperation, 
                                   base_collection: str) -> List[Dict[str, Any]]:
        """Translate DERIVED subquery to MongoDB pipeline"""
        # DERIVED subquery: FROM (SELECT ...) alias
        # Strategy: Use $lookup with pipeline to create the derived table, then join
        
        stages = []
        
        # For DERIVED subqueries, we need to completely reconstruct the query
        # as a single aggregation pipeline that combines the base table with the derived result
        
        # Step 1: Create the derived table using $lookup with the subquery pipeline
        derived_alias = f"derived_{subquery_op.inner_collection}"
        
        lookup_stage = {
            "$lookup": {
                "from": subquery_op.inner_collection,
                "pipeline": self._build_subquery_pipeline(subquery_op.inner_query),
                "as": derived_alias
            }
        }
        stages.append(lookup_stage)
        
        # Step 2: For DERIVED tables, we need to unwind and create a cross-product
        # This simulates the FROM table1, (SELECT ...) table2 behavior
        unwind_stage = {
            "$unwind": f"${derived_alias}"
        }
        stages.append(unwind_stage)
        
        # Step 3: Project fields to simulate the derived table join
        # We need to flatten the derived table fields to the root level
        # This will be handled in the main query processing after subquery translation
        
        return stages

    def _build_subquery_pipeline(self, subquery_sql: str) -> List[Dict[str, Any]]:
        """Build MongoDB pipeline for subquery SQL"""
        pipeline = []
        
        # For now, implement basic WHERE clause parsing
        # In full implementation, this should use the main SQL parser
        
        # Extract WHERE clause conditions and convert to $match
        if "WHERE" in subquery_sql.upper():
            match_filter = self._parse_subquery_where(subquery_sql)
            if match_filter:
                pipeline.append({"$match": match_filter})
        
        # Parse ORDER BY
        if "ORDER BY" in subquery_sql.upper():
            field = self._extract_order_field(subquery_sql)
            if field:
                if "DESC" in subquery_sql.upper():
                    pipeline.append({"$sort": {field: -1}})
                else:
                    pipeline.append({"$sort": {field: 1}})
        
        # Parse GROUP BY
        if "GROUP BY" in subquery_sql.upper():
            group_fields, aggregations = self._extract_group_by_info(subquery_sql)
            if group_fields:
                # Create $group stage
                group_stage = {"$group": {"_id": f"${group_fields[0]}"}}
                
                # Add aggregation functions
                for field, func in aggregations.items():
                    if func.upper() == 'COUNT':
                        group_stage["$group"][field] = {"$sum": 1}
                    elif func.upper() == 'SUM':
                        group_stage["$group"][field] = {"$sum": f"${field}"}
                    elif func.upper() == 'AVG':
                        group_stage["$group"][field] = {"$avg": f"${field}"}
                    elif func.upper() == 'MIN':
                        group_stage["$group"][field] = {"$min": f"${field}"}
                    elif func.upper() == 'MAX':
                        group_stage["$group"][field] = {"$max": f"${field}"}
                
                pipeline.append(group_stage)
                
                # Add projection to rename _id back to original field and include aggregated fields
                project_stage = {"$project": {}}
                project_stage["$project"][group_fields[0]] = "$_id"
                project_stage["$project"]["_id"] = 0
                
                # Add aggregated fields
                for field in aggregations.keys():
                    project_stage["$project"][field] = f"${field}"
                
                pipeline.append(project_stage)
        
        # Parse LIMIT
        if "LIMIT" in subquery_sql.upper():
            limit_value = self._extract_limit_value(subquery_sql)
            if limit_value:
                pipeline.append({"$limit": limit_value})
        
        return pipeline
    
    def _parse_subquery_where(self, subquery_sql: str) -> Optional[Dict[str, Any]]:
        """Parse WHERE clause from subquery SQL using token-based parsing"""
        try:
            import sqlparse
            from sqlparse.tokens import Keyword, Name, Operator, Literal
            
            # Parse the subquery SQL using sqlparse tokens
            parsed = sqlparse.parse(subquery_sql)[0]
            tokens = list(parsed.flatten())
            
            # Find WHERE clause and extract condition
            where_found = False
            field = None
            operator = None
            value = None
            
            i = 0
            while i < len(tokens):
                token = tokens[i]
                
                if token.ttype is Keyword and token.value.upper() == 'WHERE':
                    where_found = True
                elif where_found and token.ttype is Name and not field:
                    # Found field name after WHERE
                    field = token.value
                elif where_found and token.ttype is Operator.Comparison and not operator:
                    # Found comparison operator
                    operator = token.value
                elif where_found and operator and not value:
                    # Found value after operator
                    if token.ttype in (Literal.Number.Integer, Literal.Number.Float):
                        # Numeric value
                        if '.' in token.value:
                            value = float(token.value)
                        else:
                            value = int(token.value)
                    elif token.ttype in (Literal.String.Single, Literal.String.Double):
                        # String value - remove quotes
                        value = token.value[1:-1]  # Remove surrounding quotes
                    elif token.value and token.value.strip():
                        # Other value types
                        stripped = token.value.strip()
                        if stripped.startswith('"') and stripped.endswith('"'):
                            value = stripped[1:-1]
                        elif stripped.startswith("'") and stripped.endswith("'"):
                            value = stripped[1:-1]
                        else:
                            # Try to parse as number, fallback to string
                            try:
                                if '.' in stripped:
                                    value = float(stripped)
                                else:
                                    value = int(stripped)
                            except ValueError:
                                value = stripped
                    
                    # If we have all components, build the filter
                    if field and operator and value is not None:
                        if operator == '=':
                            return {field: value}
                        elif operator == '>':
                            return {field: {"$gt": value}}
                        elif operator == '<':
                            return {field: {"$lt": value}}
                        elif operator == '>=':
                            return {field: {"$gte": value}}
                        elif operator == '<=':
                            return {field: {"$lte": value}}
                        elif operator == '!=':
                            return {field: {"$ne": value}}
                        else:
                            # Default to equality for unknown operators
                            return {field: value}
                
                i += 1
                
            return None
            
        except Exception:
            return None
    
    def _extract_order_field(self, sql: str) -> Optional[str]:
        """Extract field name from ORDER BY clause using token-based parsing"""
        try:
            import sqlparse
            from sqlparse.tokens import Keyword, Name
            
            parsed = sqlparse.parse(sql)[0]
            tokens = list(parsed.flatten())
            
            # Look for ORDER BY keyword (can be single token "ORDER BY" or separate tokens)
            order_by_found = False
            
            for i, token in enumerate(tokens):
                # Check for "ORDER BY" as single token
                if token.ttype is Keyword and "ORDER BY" in token.value.upper():
                    order_by_found = True
                # Check for separate "ORDER" and "BY" tokens
                elif token.ttype is Keyword and token.value.upper() == 'ORDER':
                    # Look for next BY token
                    for j in range(i+1, min(i+3, len(tokens))):  # Look ahead a few tokens
                        if tokens[j].ttype is Keyword and tokens[j].value.upper() == 'BY':
                            order_by_found = True
                            break
                elif order_by_found and token.ttype is Name:
                    # This is the field name after ORDER BY
                    return token.value
                    
            return None
        except:
            return None
    
    def _extract_limit_value(self, sql: str) -> Optional[int]:
        """Extract LIMIT value - simplified"""
        try:
            parts = sql.upper().split("LIMIT")[1].strip().split()[0]
            return int(parts)
        except:
            return None
    
    def _extract_group_by_info(self, sql: str) -> tuple:
        """Extract GROUP BY fields and aggregation functions from SQL"""
        try:
            import sqlparse
            from sqlparse.tokens import Keyword, Name, Punctuation, Wildcard
            
            parsed = sqlparse.parse(sql)[0]
            tokens = list(parsed.flatten())
            
            # Find GROUP BY clause
            group_by_found = False
            group_fields = []
            
            for i, token in enumerate(tokens):
                if (hasattr(token, 'ttype') and token.ttype is Keyword and 
                    token.value.upper() == 'GROUP BY'):
                    group_by_found = True
                elif group_by_found and hasattr(token, 'ttype') and token.ttype is Name:
                    group_fields.append(token.value)
                    break  # For simplicity, just take the first field
            
            # Extract aggregation functions from SELECT clause
            aggregations = {}
            
            for i, token in enumerate(tokens):
                if (hasattr(token, 'ttype') and token.ttype is Name and 
                    token.value.upper() in ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']):
                    func_name = token.value.upper()
                    
                    # Look for AS alias after the function
                    for j in range(i+1, min(i+15, len(tokens))):
                        if (hasattr(tokens[j], 'ttype') and tokens[j].ttype is Keyword and 
                            tokens[j].value.upper() == 'AS'):
                            # Next token should be the alias
                            if (j+1 < len(tokens) and hasattr(tokens[j+1], 'ttype') and 
                                tokens[j+1].ttype is Name):
                                alias = tokens[j+1].value
                                aggregations[alias] = func_name
                                break
                        elif (hasattr(tokens[j], 'ttype') and tokens[j].ttype is Name and
                              j > i + 3):  # Skip the function parentheses
                            # Direct alias without AS keyword
                            alias = tokens[j].value
                            if alias.upper() not in ['FROM', 'WHERE', 'GROUP', 'ORDER']:
                                aggregations[alias] = func_name
                                break
            
            return group_fields, aggregations
            
        except:
            return [], {}

    def _is_correlated_exists(self, subquery_op: SubqueryOperation) -> bool:
        """Check if EXISTS subquery is correlated"""
        # Check if subquery references outer table
        return ("customers." in subquery_op.inner_query or 
                "orders." in subquery_op.inner_query)
    
    def _build_correlation_let(self, subquery_op: SubqueryOperation) -> Dict[str, str]:
        """Build let clause for correlated subquery"""
        # For EXISTS with correlation like:
        # WHERE orders.customerNumber = customers.customerNumber
        return {
            "outer_customer_number": "$customerNumber"
        }
    
    def _build_correlated_pipeline(self, subquery_op: SubqueryOperation) -> List[Dict[str, Any]]:
        """Build pipeline for correlated EXISTS subquery"""
        return [
            {
                "$match": {
                    "$expr": {
                        "$eq": ["$customerNumber", "$$outer_customer_number"]
                    }
                }
            }
        ]
