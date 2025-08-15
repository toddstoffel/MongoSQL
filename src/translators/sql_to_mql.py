"""
SQL to MongoDB Query Language (MQL) translator
"""
from typing import Dict, List, Any, Optional
from ..mappers.function_mapper import FunctionMapper
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from ..joins.join_translator import JoinTranslator
from ..orderby import OrderByParser, OrderByTranslator

class MongoSQLTranslator:
    """Translates parsed SQL to MongoDB Query Language"""
    
    def __init__(self):
        self.function_mapper = FunctionMapper()
        self.join_translator = JoinTranslator()
        self.orderby_parser = OrderByParser()
        self.orderby_translator = OrderByTranslator()
    
    def _is_aggregate_function(self, function_name: str) -> bool:
        """Check if a function is an aggregate function using the function mapper"""
        if not function_name:
            return False
        return self.function_mapper.is_aggregate_function(function_name)
    
    def translate(self, parsed_sql: Dict[str, Any]) -> Dict[str, Any]:
        """Translate parsed SQL to MQL"""
        sql_type = parsed_sql.get('type')
        
        if sql_type == 'SELECT':
            return self._translate_select(parsed_sql)
        elif sql_type == 'INSERT':
            return self._translate_insert(parsed_sql)
        elif sql_type == 'UPDATE':
            return self._translate_update(parsed_sql)
        elif sql_type == 'DELETE':
            return self._translate_delete(parsed_sql)
        elif sql_type == 'SHOW':
            return self._translate_show(parsed_sql)
        elif sql_type == 'USE':
            return self._translate_use(parsed_sql)
        else:
            raise Exception(f"Unsupported SQL type: {sql_type}")
    
    def _translate_select(self, parsed_sql: Dict[str, Any]) -> Dict[str, Any]:
        """Translate SELECT statement to MongoDB find()"""
        
        # Check if this query has JOINs
        if parsed_sql.get('joins'):
            return self.join_translator.translate_join_query(parsed_sql)
        
        # Handle DISTINCT queries
        if parsed_sql.get('distinct'):
            # For DISTINCT, we need to use MongoDB's distinct() operation
            columns = parsed_sql.get('columns', [])
            if len(columns) == 1 and columns[0] != '*':
                # Single column DISTINCT
                field_name = columns[0] if isinstance(columns[0], str) else columns[0].get('column', columns[0])
                
                # Check if we have LIMIT - if so, use aggregation pipeline
                if parsed_sql.get('limit'):
                    return self._translate_distinct_with_limit(parsed_sql, field_name)
                
                mql = {
                    'operation': 'distinct',
                    'collection': parsed_sql.get('from'),
                    'field': field_name
                }
                
                # Handle WHERE clause for distinct
                if parsed_sql.get('where'):
                    mql['filter'] = self._translate_where(parsed_sql['where'])
                    
                return mql
            else:
                # Multiple column DISTINCT - use aggregation pipeline
                return self._translate_distinct_multiple(parsed_sql)
        
        # Regular SELECT handling
        
        # Check for queries without FROM clause (like SELECT 1+1, SELECT NOW())
        if not parsed_sql.get('from'):
            return self._handle_no_table_query(parsed_sql)
        
        # Check for aggregate functions
        if parsed_sql.get('columns'):
            aggregate_result = self._handle_aggregate_functions(parsed_sql)
            if aggregate_result:
                return aggregate_result
        
        mql = {
            'operation': 'find',
            'collection': parsed_sql.get('from')
        }
        
        # Handle WHERE clause
        if parsed_sql.get('where'):
            mql['filter'] = self._translate_where(parsed_sql['where'])
        
        # Handle column selection (projection)
        if parsed_sql.get('columns') and parsed_sql['columns'] != ['*']:
            projection = {}
            has_id_column = False
            query_columns = []  # Track the order of columns in the query
            
            for col in parsed_sql['columns']:
                if isinstance(col, dict) and 'column' in col:
                    # Handle aliased columns
                    col_name = col['column']
                    projection[col_name] = 1
                    query_columns.append(col_name)
                    if col_name == '_id':
                        has_id_column = True
                elif isinstance(col, dict) and 'function' in col:
                    # Handle function columns - check if it's an aggregate function first
                    func_name = col.get('function')
                    if self._is_aggregate_function(func_name):
                        # This is an aggregate function, let the aggregate handler deal with it
                        aggregate_result = self._handle_aggregate_functions(parsed_sql)
                        if aggregate_result:
                            return aggregate_result
                    else:
                        # Non-aggregate function with FROM clause - use aggregation pipeline
                        return self._handle_function_with_from(parsed_sql)
                else:
                    # Handle qualified column names (e.g., "c.customerName")
                    col_name = col
                    if isinstance(col, str) and '.' in col:
                        # Extract just the column name from table.column format
                        parts = col.split('.', 1)
                        if len(parts) == 2:
                            table_alias, col_name = parts
                            # For now, just use the column name
                            # TODO: Validate table alias matches the FROM clause
                    
                    if isinstance(col_name, str):  # Ensure it's a string before using as dict key
                        projection[col_name] = 1
                        query_columns.append(col_name)
                        if col_name == '_id':
                            has_id_column = True
            
            # Exclude _id if it wasn't explicitly requested
            if not has_id_column:
                projection['_id'] = 0
                
            mql['projection'] = projection
            mql['query_columns'] = query_columns  # Preserve query column order
        
        # Handle ORDER BY using modular parser
        if parsed_sql.get('order_by') or parsed_sql.get('original_sql'):
            # First try to use parsed order_by if available
            if parsed_sql.get('order_by'):
                sort_spec = []
                for order_item in parsed_sql['order_by']:
                    direction = 1 if order_item['direction'] == 'ASC' else -1
                    sort_spec.append((order_item['field'], direction))
                mql['sort'] = sort_spec
            else:
                # Try to parse ORDER BY from original SQL using our modular parser
                original_sql = parsed_sql.get('original_sql', '')
                if original_sql:
                    order_by_clause = self.orderby_parser.parse_order_by(original_sql)
                    if order_by_clause and not order_by_clause.is_empty():
                        # Convert to MongoDB sort specification
                        sort_stages = self.orderby_translator.get_sort_pipeline_stage(order_by_clause)
                        if sort_stages:
                            # Extract sort specification from pipeline stage
                            sort_spec = []
                            for field, direction in sort_stages[0]['$sort'].items():
                                sort_spec.append((field, direction))
                            mql['sort'] = sort_spec
        
        # Handle LIMIT
        if parsed_sql.get('limit'):
            limit_info = parsed_sql['limit']
            if 'count' in limit_info:
                mql['limit'] = limit_info['count']
            if 'offset' in limit_info:
                mql['skip'] = limit_info['offset']
        
        return mql
    
    def _translate_distinct_multiple(self, parsed_sql: Dict[str, Any]) -> Dict[str, Any]:
        """Translate multi-column DISTINCT using aggregation pipeline"""
        # This is more complex and would require aggregation pipeline
        # For now, fall back to regular find with a note
        raise Exception("Multi-column DISTINCT not yet supported. Use single column DISTINCT.")
    
    def _translate_distinct_with_limit(self, parsed_sql: Dict[str, Any], field_name: str) -> Dict[str, Any]:
        """Translate DISTINCT with LIMIT using aggregation pipeline"""
        pipeline = []
        
        # Add match stage if WHERE clause exists
        if parsed_sql.get('where'):
            pipeline.append({
                '$match': self._translate_where(parsed_sql['where'])
            })
        
        # Group by the field to get distinct values
        pipeline.append({
            '$group': {
                '_id': f'${field_name}',
                field_name: {'$first': f'${field_name}'}
            }
        })
        
        # Add ORDER BY using modular parser
        if parsed_sql.get('order_by') or parsed_sql.get('original_sql'):
            if parsed_sql.get('order_by'):
                # Use parsed order_by if available
                sort_spec = {}
                for order_item in parsed_sql['order_by']:
                    direction = 1 if order_item['direction'] == 'ASC' else -1
                    sort_spec[order_item['field']] = direction
                pipeline.append({'$sort': sort_spec})
            else:
                # Try to parse ORDER BY from original SQL
                original_sql = parsed_sql.get('original_sql', '')
                if original_sql:
                    order_by_clause = self.orderby_parser.parse_order_by(original_sql)
                    if order_by_clause and not order_by_clause.is_empty():
                        sort_stages = self.orderby_translator.get_sort_pipeline_stage(order_by_clause)
                        if sort_stages:
                            pipeline.extend(sort_stages)
        
        # Add limit if specified
        if parsed_sql.get('limit') and 'count' in parsed_sql['limit']:
            pipeline.append({
                '$limit': parsed_sql['limit']['count']
            })
        
        # Project to clean up the result
        pipeline.append({
            '$project': {
                '_id': 0,
                field_name: '$_id'
            }
        })
        
        return {
            'operation': 'aggregate',
            'collection': parsed_sql.get('from'),
            'pipeline': pipeline
        }
    
    def _translate_insert(self, parsed_sql: Dict[str, Any]) -> Dict[str, Any]:
        """Translate INSERT statement to MongoDB insertOne/insertMany"""
        table = parsed_sql.get('table')
        columns = parsed_sql.get('columns', [])
        values = parsed_sql.get('values', [])
        
        if not table:
            raise Exception("No table specified in INSERT")
        
        if len(values) == 1:
            # Single document insert
            document = {}
            if columns:
                # Columns specified
                for i, col in enumerate(columns):
                    if i < len(values[0]):
                        document[col] = self._convert_value(values[0][i])
            else:
                # No columns specified - this would need schema information
                raise Exception("INSERT without column specification requires schema information")
            
            return {
                'operation': 'insert_one',
                'collection': table,
                'document': document
            }
        else:
            # Multiple document insert
            documents = []
            for value_set in values:
                document = {}
                if columns:
                    for i, col in enumerate(columns):
                        if i < len(value_set):
                            document[col] = self._convert_value(value_set[i])
                documents.append(document)
            
            return {
                'operation': 'insert_many',
                'collection': table,
                'documents': documents
            }
    
    def _translate_update(self, parsed_sql: Dict[str, Any]) -> Dict[str, Any]:
        """Translate UPDATE statement to MongoDB updateOne/updateMany"""
        table = parsed_sql.get('table')
        set_clause = parsed_sql.get('set', {})
        where_clause = parsed_sql.get('where')
        
        if not table:
            raise Exception("No table specified in UPDATE")
        
        # Build update document
        update_doc = {}
        if set_clause:
            update_doc['$set'] = {}
            for field, value in set_clause.items():
                update_doc['$set'][field] = self._convert_value(value)
        
        mql = {
            'operation': 'update_many',  # Default to updateMany
            'collection': table,
            'update': update_doc
        }
        
        # Handle WHERE clause
        if where_clause:
            mql['filter'] = self._translate_where(where_clause)
        
        return mql
    
    def _translate_delete(self, parsed_sql: Dict[str, Any]) -> Dict[str, Any]:
        """Translate DELETE statement to MongoDB deleteOne/deleteMany"""
        table = parsed_sql.get('from')
        where_clause = parsed_sql.get('where')
        
        if not table:
            raise Exception("No table specified in DELETE")
        
        mql = {
            'operation': 'delete_many',  # Default to deleteMany
            'collection': table
        }
        
        # Handle WHERE clause
        if where_clause:
            mql['filter'] = self._translate_where(where_clause)
        else:
            # No WHERE clause means delete all - be careful!
            mql['filter'] = {}
        
        return mql
    
    def _translate_where(self, where_clause: Dict[str, Any]) -> Dict[str, Any]:
        """Translate WHERE clause to MongoDB filter"""
        if '_raw' in where_clause:
            # Handle raw conditions - would need more sophisticated parsing
            print(f"WARNING: Raw WHERE clause not fully supported: {where_clause['_raw']}")
            return {}
        
        # Handle compound WHERE clauses with AND/OR
        if where_clause.get('type') == 'compound':
            return self._translate_compound_where(where_clause)
        
        # Handle simple WHERE clauses
        field = where_clause.get('field')
        operator = where_clause.get('operator')
        value = where_clause.get('value')
        
        if not field or not operator:
            return {}
        
        return self._translate_single_condition(field, operator, value)
    
    def _translate_compound_where(self, where_clause: Dict[str, Any]) -> Dict[str, Any]:
        """Translate compound WHERE clause with AND/OR operators"""
        conditions = where_clause.get('conditions', [])
        operators = where_clause.get('operators', [])
        
        if not conditions:
            return {}
        
        # Translate each condition
        translated_conditions = []
        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')
            
            if field and operator:
                mongo_condition = self._translate_single_condition(field, operator, value)
                if mongo_condition:
                    translated_conditions.append(mongo_condition)
        
        if not translated_conditions:
            return {}
        
        # If only one condition, return it directly
        if len(translated_conditions) == 1:
            return translated_conditions[0]
        
        # Handle multiple conditions with operators
        if not operators:
            # Default to AND if no operators specified
            operators = ['AND'] * (len(translated_conditions) - 1)
        
        # Check if all operators are the same
        unique_operators = set(operators)
        
        if len(unique_operators) == 1:
            # All operators are the same
            op = operators[0]
            if op == 'AND':
                # MongoDB $and
                return {'$and': translated_conditions}
            elif op == 'OR':
                # MongoDB $or
                return {'$or': translated_conditions}
        else:
            # Mixed operators - need to handle precedence
            # For now, use $and as default and nest appropriately
            return {'$and': translated_conditions}
        
        return {}
    
    def _translate_single_condition(self, field: str, operator: str, value: Any) -> Dict[str, Any]:
        """Translate a single WHERE condition"""
        
        # Map SQL operators to MongoDB operators
        if operator == '=':
            converted_value = self._convert_value(value)
            return {field: converted_value}
        elif operator in ['!=', '<>']:
            converted_value = self._convert_value(value)
            return {field: {'$ne': converted_value}}
        elif operator == '>':
            converted_value = self._convert_value(value)
            return {field: {'$gt': converted_value}}
        elif operator == '>=':
            converted_value = self._convert_value(value)
            return {field: {'$gte': converted_value}}
        elif operator == '<':
            converted_value = self._convert_value(value)
            return {field: {'$lt': converted_value}}
        elif operator == '<=':
            converted_value = self._convert_value(value)
            return {field: {'$lte': converted_value}}
        elif operator.upper() == 'BETWEEN':
            # Handle BETWEEN operator
            if isinstance(value, list) and len(value) == 2:
                val1 = self._convert_value(value[0])
                val2 = self._convert_value(value[1])
                return {field: {'$gte': val1, '$lte': val2}}
            return {}
        elif operator.upper() == 'LIKE':
            # Convert SQL LIKE to MongoDB regex
            converted_value = self._convert_value(value)
            regex_pattern = str(converted_value).replace('%', '.*').replace('_', '.')
            return {field: {'$regex': regex_pattern, '$options': 'i'}}
        elif operator.upper() == 'IN':
            # Handle IN operator
            if isinstance(value, list):
                return {field: {'$in': [self._convert_value(v) for v in value]}}
            elif isinstance(value, str):
                # Parse the IN list if it's still a string
                in_values = [v.strip().strip("'\"") for v in value.strip('()').split(',')]
                return {field: {'$in': [self._convert_value(v) for v in in_values]}}
            return {field: {'$in': value}}
        else:
            # Fallback
            converted_value = self._convert_value(value)
            return {field: converted_value}
    
    def _convert_value(self, value) -> Any:
        """Convert SQL value to appropriate Python/MongoDB type"""
        if value is None:
            return None
        
        # Handle new value structure with quote information
        if isinstance(value, dict) and 'value' in value:
            actual_value = value['value']
            was_quoted = value.get('quoted', False)
            
            # If value was quoted, treat as string
            if was_quoted:
                return actual_value
            
            # If not quoted, try to convert to appropriate type
            return self._convert_unquoted_value(actual_value)
        
        # Handle legacy string values
        if isinstance(value, str):
            return self._convert_unquoted_value(value)
        
        return value
    
    def _convert_unquoted_value(self, value_str: str) -> Any:
        """Convert unquoted value string to appropriate type"""
        if value_str is None:
            return None
        
        value_str = str(value_str).strip()
        
        # Handle NULL
        if value_str.upper() == 'NULL':
            return None
        
        # Handle boolean
        if value_str.upper() in ['TRUE', 'FALSE']:
            return value_str.upper() == 'TRUE'
        
        # Handle numbers
        try:
            # Try integer first
            if '.' not in value_str:
                return int(value_str)
            else:
                return float(value_str)
        except ValueError:
            pass
        
        # Return as string for anything else
        return value_str
    
    def translate_function(self, function_name: str, args: List[Any]) -> Dict[str, Any]:
        """Translate SQL function to MongoDB equivalent"""
        return self.function_mapper.map_function(function_name, args)
    
    def _translate_show(self, parsed_sql: Dict[str, Any]) -> Dict[str, Any]:
        """Translate SHOW statement to MongoDB equivalent"""
        show_type = parsed_sql.get('show_type')
        
        if show_type == 'TABLES':
            return {
                'operation': 'show_collections',
                'collection': None
            }
        elif show_type == 'DATABASES':
            return {
                'operation': 'show_databases',
                'collection': None
            }
        else:
            raise Exception(f"Unsupported SHOW type: {show_type}")
    
    def _translate_use(self, parsed_sql: Dict[str, Any]) -> Dict[str, Any]:
        """Translate USE statement to database switch operation"""
        database_name = parsed_sql.get('database')
        
        if not database_name:
            raise Exception("No database name specified in USE statement")
        
        return {
            'operation': 'use_database',
            'database': database_name
        }
    
    def _handle_aggregate_functions(self, parsed_sql: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle aggregate functions like COUNT, MAX, MIN, SUM, AVG"""
        columns = parsed_sql.get('columns', [])
        
        # Find aggregate functions
        aggregate_functions = []
        for col in columns:
            if isinstance(col, dict) and 'function' in col:
                aggregate_functions.append(col)
        
        if not aggregate_functions:
            return None
        
        # Handle single aggregate function
        if len(aggregate_functions) == 1:
            func_info = aggregate_functions[0]
            func_name = func_info.get('function')
            # Check both 'arg' and 'args_str' for backward compatibility
            func_arg = func_info.get('arg') or func_info.get('args_str', '*')
            
            if func_name == 'COUNT':
                return self._translate_count_aggregate(parsed_sql, func_arg)
            elif func_name in ['MAX', 'MIN', 'SUM', 'AVG']:
                return self._translate_math_aggregate(parsed_sql, func_name, func_arg)
        
        # Handle multiple aggregate functions (would need aggregation pipeline)
        # For now, return None to indicate not supported
        return None
    
    def _translate_count_aggregate(self, parsed_sql: Dict[str, Any], arg: str) -> Dict[str, Any]:
        """Translate COUNT aggregate to MongoDB count operation"""
        mql = {
            'operation': 'count',
            'collection': parsed_sql.get('from')
        }
        
        # Handle WHERE clause for count
        if parsed_sql.get('where'):
            mql['filter'] = self._translate_where(parsed_sql['where'])
        
        return mql
    
    def _translate_math_aggregate(self, parsed_sql: Dict[str, Any], func_name: str, field: str) -> Dict[str, Any]:
        """Translate MAX, MIN, SUM, AVG to MongoDB aggregation pipeline"""
        if field == '*':
            raise Exception(f"{func_name} requires a specific field, not *")
        
        # Build aggregation pipeline
        pipeline = []
        
        # Add match stage if WHERE clause exists
        if parsed_sql.get('where'):
            match_filter = self._translate_where(parsed_sql['where'])
            if match_filter:
                pipeline.append({'$match': match_filter})
        
        # Add project stage to convert field to number
        pipeline.append({
            '$project': {
                field: {'$cond': [
                    {'$isNumber': f'${field}'},
                    f'${field}',
                    {'$convert': {'input': f'${field}', 'to': 'double', 'onError': 0}}
                ]},
                '_id': 1
            }
        })
        
        # Add group stage for the aggregate function
        group_stage = {'$group': {'_id': None}}
        
        if func_name == 'MAX':
            group_stage['$group'][f'{func_name}({field})'] = {'$max': f'${field}'}
        elif func_name == 'MIN':
            group_stage['$group'][f'{func_name}({field})'] = {'$min': f'${field}'}
        elif func_name == 'SUM':
            group_stage['$group'][f'{func_name}({field})'] = {'$sum': f'${field}'}
        elif func_name == 'AVG':
            group_stage['$group'][f'{func_name}({field})'] = {'$avg': f'${field}'}
        
        pipeline.append(group_stage)
        
        # Add ORDER BY using modular parser (if applicable for aggregate results)
        if parsed_sql.get('order_by') or parsed_sql.get('original_sql'):
            if parsed_sql.get('order_by'):
                # Use parsed order_by if available
                sort_spec = {}
                for order_item in parsed_sql['order_by']:
                    direction = 1 if order_item['direction'] == 'ASC' else -1
                    # For aggregate results, we may need to map field names
                    field_name = order_item['field']
                    if field_name in [f'{func_name}({field})']:
                        sort_spec[field_name] = direction
                pipeline.append({'$sort': sort_spec})
            else:
                # Try to parse ORDER BY from original SQL
                original_sql = parsed_sql.get('original_sql', '')
                if original_sql:
                    order_by_clause = self.orderby_parser.parse_order_by(original_sql)
                    if order_by_clause and not order_by_clause.is_empty():
                        sort_stages = self.orderby_translator.get_sort_pipeline_stage(order_by_clause)
                        if sort_stages:
                            pipeline.extend(sort_stages)
        
        # Remove the _id field in projection
        pipeline.append({'$project': {'_id': 0}})
        
        return {
            'operation': 'aggregate',
            'collection': parsed_sql.get('from'),
            'pipeline': pipeline
        }
    
    def _handle_no_table_query(self, parsed_sql: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SELECT queries without FROM clause (like SELECT 1+1, SELECT NOW())"""
        columns = parsed_sql.get('columns', [])
        
        if not columns:
            raise Exception("No columns specified in SELECT")
        
        # Create a projection for each column
        projection = {}
        
        for col in columns:
            if isinstance(col, dict):
                # Handle expressions and functions
                if 'expression' in col:
                    # This is a computed expression
                    expr = col['expression']
                    alias = col.get('alias', str(expr))
                    projection[alias] = {'$literal': self._evaluate_expression(expr)}
                elif 'function' in col:
                    # This is a function call
                    func_name = col['function']
                    
                    # Handle both old format (args list) and new format (args_str)
                    if 'args' in col:
                        args = col['args']
                    elif 'args_str' in col:
                        # Parse the args_str to get individual arguments
                        args_str = col['args_str']
                        args = []
                        if args_str:
                            # Enhanced argument parsing - handle nested parentheses and quotes
                            current_arg = ""
                            in_quotes = False
                            quote_char = None
                            paren_depth = 0
                            
                            for char in args_str:
                                if char in ("'", '"') and not in_quotes:
                                    in_quotes = True
                                    quote_char = char
                                    current_arg += char
                                elif char == quote_char and in_quotes:
                                    in_quotes = False
                                    quote_char = None
                                    current_arg += char
                                elif char == '(' and not in_quotes:
                                    paren_depth += 1
                                    current_arg += char
                                elif char == ')' and not in_quotes:
                                    paren_depth -= 1
                                    current_arg += char
                                elif char == ',' and not in_quotes and paren_depth == 0:
                                    # Only split on commas at the top level (not inside parentheses)
                                    args.append(current_arg.strip())
                                    current_arg = ""
                                else:
                                    current_arg += char
                            
                            # Add the last argument
                            if current_arg.strip():
                                args.append(current_arg.strip())
                        
                        # Convert numeric arguments for better type handling
                        converted_args = []
                        for arg in args:
                            # Remove quotes if they exist
                            if arg.startswith("'") and arg.endswith("'"):
                                arg = arg[1:-1]
                            elif arg.startswith('"') and arg.endswith('"'):
                                arg = arg[1:-1]
                            
                            # Check if the argument contains function calls or mathematical expressions
                            if self._contains_expression(arg):
                                # Evaluate the expression
                                try:
                                    evaluated_arg = self._evaluate_argument_expression(arg)
                                    converted_args.append(evaluated_arg)
                                    continue
                                except:
                                    # If evaluation fails, continue with original logic
                                    pass
                            
                            # Try to convert to number if it looks like a number
                            try:
                                # Check if it's an integer
                                if '.' not in arg and arg.lstrip('-').isdigit():
                                    converted_args.append(int(arg))
                                # Check if it's a float
                                else:
                                    converted_args.append(float(arg))
                            except ValueError:
                                # If conversion fails, keep as string
                                converted_args.append(arg)
                        
                        args = converted_args
                    else:
                        args = []
                    
                    # Use original call for alias if available, otherwise use function name
                    if 'original_call' in col:
                        alias = col['original_call']
                    elif 'alias' in col:
                        alias = col['alias']
                    else:
                        alias = f"{func_name}()"
                    
                    try:
                        # Try to map the function
                        function_mapping = self.function_mapper.map_function(func_name, args)
                        projection[alias] = function_mapping
                    except ValueError:
                        # Function not supported, return literal
                        projection[alias] = {'$literal': f"Function {func_name} not supported"}
                else:
                    # Regular column reference (shouldn't happen without FROM)
                    col_name = col.get('column', str(col))
                    projection[col_name] = {'$literal': None}
            else:
                # Simple column or expression string - check if it's a function call or SQL keyword
                if isinstance(col, str):
                    col_stripped = col.strip()
                    
                    # Check for SQL datetime keywords (no parentheses)
                    sql_keywords = {
                        'CURRENT_DATE': self.function_mapper.datetime_mapper._map_curdate([]),
                        'CURRENT_TIME': self.function_mapper.datetime_mapper._map_curtime([]),
                        'CURRENT_TIMESTAMP': self.function_mapper.datetime_mapper._map_now([]),
                    }
                    
                    if col_stripped.upper() in sql_keywords:
                        projection[col_stripped] = sql_keywords[col_stripped.upper()]
                        continue
                    
                    # Check if this looks like a function call (e.g., "NOW()", "YEAR('2024-12-25')")
                    if '(' in col_stripped and col_stripped.endswith(')'):
                        func_call = self._parse_function_call(col_stripped)
                        if func_call:
                            func_name = func_call['function']
                            args = func_call.get('args', [])
                            
                            try:
                                # Try to map the function
                                function_mapping = self.function_mapper.map_function(func_name, args)
                                projection[col_stripped] = function_mapping
                                continue
                            except ValueError:
                                # Function not supported, fall through to literal
                                pass
                    
                    # Check if this has an alias (e.g., "1 as test", "col_name as alias")
                    if ' as ' in col_stripped.lower():
                        # Find the position of the last AS (case-insensitive)
                        col_lower = col_stripped.lower()
                        as_pos = col_lower.rfind(' as ')
                        if as_pos != -1:
                            expression_part = col_stripped[:as_pos].strip()
                            alias_part = col_stripped[as_pos + 4:].strip()  # +4 for " as "
                            
                            # Try to evaluate the expression part
                            try:
                                result = eval(expression_part)  # Simple math expressions like "1"
                                projection[alias_part] = {'$literal': result}
                                continue
                            except:
                                # If eval fails, treat as literal string
                                projection[alias_part] = {'$literal': expression_part}
                                continue
                    
                    # Try to evaluate as expression (like "1+1")
                    try:
                        result = eval(col_stripped)  # Simple math expressions
                        projection[col_stripped] = {'$literal': result}
                    except:
                        projection[col_stripped] = {'$literal': col_stripped}
                else:
                    projection[str(col)] = {'$literal': col}
        
        # Return a special aggregation that creates a single document with the computed values
        # For no-table queries, we don't need a real collection - this will be handled specially
        return {
            'operation': 'eval',
            'type': 'no_table_query',
            'projection': projection
        }
    
    def _evaluate_expression(self, expr):
        """Evaluate simple expressions like 1+1"""
        try:
            # For safety, only allow simple math expressions
            if isinstance(expr, str) and all(c in '0123456789+-*/.() ' for c in expr):
                return eval(expr)
            else:
                return str(expr)
        except:
            return str(expr)
    
    def _parse_function_call(self, func_str: str) -> Optional[Dict[str, Any]]:
        """Parse a function call string like 'NOW()' or 'YEAR('2024-12-25')' into components"""
        if not func_str or not func_str.strip():
            return None
            
        func_str = func_str.strip()
        
        # Must have parentheses
        if not ('(' in func_str and func_str.endswith(')')):
            return None
        
        # Extract function name and arguments
        paren_idx = func_str.find('(')
        func_name = func_str[:paren_idx].strip().upper()
        
        # Extract arguments (everything between parentheses)
        args_str = func_str[paren_idx + 1:-1].strip()
        
        args = []
        if args_str:
            # Enhanced argument parsing - handle nested parentheses and quotes
            current_arg = ""
            in_quotes = False
            quote_char = None
            paren_depth = 0
            
            for char in args_str:
                if char in ("'", '"') and not in_quotes:
                    in_quotes = True
                    quote_char = char
                    current_arg += char
                elif char == quote_char and in_quotes:
                    in_quotes = False
                    quote_char = None
                    current_arg += char
                elif char == '(' and not in_quotes:
                    paren_depth += 1
                    current_arg += char
                elif char == ')' and not in_quotes:
                    paren_depth -= 1
                    current_arg += char
                elif char == ',' and not in_quotes and paren_depth == 0:
                    # Only split on commas at the top level (not inside parentheses)
                    args.append(current_arg.strip())
                    current_arg = ""
                else:
                    current_arg += char
            
            # Add the last argument
            if current_arg.strip():
                args.append(current_arg.strip())
        
        return {
            'function': func_name,
            'args': args
        }

    def _handle_function_with_from(self, parsed_sql: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SELECT queries with functions that have FROM clause using aggregation pipeline"""
        pipeline = []
        
        # Add match stage if WHERE clause exists
        if parsed_sql.get('where'):
            match_filter = self._translate_where(parsed_sql['where'])
            if match_filter:
                pipeline.append({'$match': match_filter})
        
        # Add limit stage if LIMIT exists (before project to improve performance)
        if parsed_sql.get('limit'):
            limit_info = parsed_sql['limit']
            if 'offset' in limit_info:
                pipeline.append({'$skip': limit_info['offset']})
            if 'count' in limit_info:
                pipeline.append({'$limit': limit_info['count']})
        
        # Build projection stage with function evaluation
        projection_stage = {}
        
        for col in parsed_sql['columns']:
            if isinstance(col, dict) and 'function' in col:
                # Function column
                func_name = col['function']
                args = []
                
                # Parse arguments from args_str
                if 'args_str' in col and col['args_str']:
                    args_str = col['args_str'].strip()
                    # Remove outer quotes if they exist
                    if args_str.startswith("'") and args_str.endswith("'"):
                        args = [args_str[1:-1]]
                    elif args_str.startswith('"') and args_str.endswith('"'):
                        args = [args_str[1:-1]]
                    else:
                        # Try to convert to number if it looks like a number
                        try:
                            # Check if it's an integer
                            if '.' not in args_str and args_str.lstrip('-').isdigit():
                                args = [int(args_str)]
                            # Check if it's a float
                            else:
                                args = [float(args_str)]
                        except ValueError:
                            # If conversion fails, keep as string
                            args = [args_str]
                
                # Use original_call as field name if available
                field_name = col.get('original_call', f"{func_name}({col.get('args_str', '')})")
                
                try:
                    # Map the function to MongoDB equivalent
                    function_mapping = self.function_mapper.map_function(func_name, args)
                    projection_stage[field_name] = function_mapping
                except ValueError:
                    # Function not supported
                    projection_stage[field_name] = {'$literal': f"Function {func_name} not supported"}
            
            elif isinstance(col, dict) and 'column' in col:
                # Regular column with alias
                col_name = col['column']
                projection_stage[col_name] = f"${col_name}"
            
            else:
                # Simple column name
                if isinstance(col, str):
                    projection_stage[col] = f"${col}"
        
        # Add the projection stage
        if projection_stage:
            pipeline.append({'$project': projection_stage})
        
        return {
            'operation': 'aggregate',
            'collection': parsed_sql.get('from'),
            'pipeline': pipeline
        }
    
    def _contains_expression(self, arg_str: str) -> bool:
        """Check if the argument string contains function calls or mathematical expressions"""
        # Check for function calls (contains parentheses)
        if '(' in arg_str and ')' in arg_str:
            return True
        
        # Check for mathematical operators, but exclude leading negative signs
        # A leading negative sign alone doesn't make it an expression
        arg_stripped = arg_str.strip()
        if arg_stripped.startswith('-'):
            # Check if it's just a negative number
            remaining = arg_stripped[1:]
            if remaining.replace('.', '').isdigit():
                return False  # It's just a negative number
            # Check for operators after the negative sign
            for op in ['+', '-', '*', '/', '%', '^']:
                if op in remaining:
                    return True
        else:
            # Check for mathematical operators
            math_operators = ['+', '-', '*', '/', '%', '^']
            for op in math_operators:
                if op in arg_str:
                    return True
        
        return False
    
    def _evaluate_argument_expression(self, arg_str: str) -> Any:
        """Evaluate a mathematical expression or function call in an argument"""
        # Handle PI()/2 specifically since it's a common pattern
        if arg_str == 'PI()/2':
            import math
            return math.pi / 2
        
        # Handle PI() function calls
        if 'PI()' in arg_str:
            import math
            # Replace PI() with the actual value and evaluate
            expr = arg_str.replace('PI()', str(math.pi))
            try:
                return eval(expr)
            except:
                pass
        
        # For more complex expressions, we could parse them properly
        # but for now, handle the most common cases
        if '/' in arg_str:
            parts = arg_str.split('/')
            if len(parts) == 2:
                try:
                    left = float(parts[0].strip())
                    right = float(parts[1].strip())
                    return left / right
                except:
                    pass
        
        # If all else fails, return the original string
        return arg_str
