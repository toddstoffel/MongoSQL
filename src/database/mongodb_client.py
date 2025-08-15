"""
MongoDB client for connecting to and executing queries on MongoDB
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import Dict, List, Any, Optional
import threading

class MongoDBClient:
    """MongoDB database client with connection pooling"""
    
    _instance = None
    _lock = threading.Lock()
    _client = None
    _connection_params = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern for connection reuse"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MongoDBClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, host: str = 'localhost', port: int = 27017, 
                 database: str = None, username: str = None, password: str = None,
                 retry_writes: str = 'true', write_concern: str = 'majority', app_name: str = 'MongoSQL'):
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
            
        self.host = host
        self.port = port
        self.database_name = database
        self.username = username
        self.password = password
        self.retry_writes = retry_writes
        self.write_concern = write_concern
        self.app_name = app_name
        self.database = None
        self._initialized = True
    
    def connect(self):
        """Connect to MongoDB server (database selection is optional) - with connection reuse"""
        # Check if we already have a connection with the same parameters
        current_params = (self.host, self.port, self.username, self.password, self.database_name)
        
        if MongoDBClient._client is not None and MongoDBClient._connection_params == current_params:
            # Reuse existing connection
            self.client = MongoDBClient._client
            if self.database_name:
                self.database = self.client[self.database_name]
            return
        
        try:
            # Build connection string using MongoDB+SRV format for Atlas
            if self.username and self.password:
                # Use SRV format for MongoDB Atlas connections
                if 'mongodb.net' in self.host:
                    connection_string = f"mongodb+srv://{self.username}:{self.password}@{self.host}/?retryWrites={self.retry_writes}&w={self.write_concern}&appName={self.app_name}"
                else:
                    # Fallback to standard format for local/other MongoDB instances
                    connection_string = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/"
            else:
                # For connections without authentication
                if 'mongodb.net' in self.host:
                    connection_string = f"mongodb+srv://{self.host}/?retryWrites={self.retry_writes}&w={self.write_concern}&appName={self.app_name}"
                else:
                    connection_string = f"mongodb://{self.host}:{self.port}/"
            
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            
            # Test connection and authentication
            self.client.admin.command('ping')
            
            # Cache the connection
            MongoDBClient._client = self.client
            MongoDBClient._connection_params = current_params
            
            # If we have credentials, test access to the specific database
            if self.database_name and (self.username or self.password):
                test_db = self.client[self.database_name]
                # Try to list collections to verify database access
                collections = list(test_db.list_collection_names(maxTimeMS=5000))
                
                # Check if database actually exists (has collections)
                all_db_names = [db['name'] for db in self.client.list_databases()]
                if self.database_name not in all_db_names:
                    raise Exception(f"ERROR 1049 (42000): Unknown database '{self.database_name}'")
            
            # Set the database if specified
            if self.database_name:
                self.database = self.client[self.database_name]
            else:
                self.database = None
            
            return True
            
        except ConnectionFailure as e:
            raise Exception(f"ERROR 2003 (HY000): Can't connect to MongoDB server on '{self.host}' ({e})")
        except OperationFailure as e:
            if e.code == 18:  # Authentication failed
                import socket
                hostname = socket.gethostname()
                raise Exception(f"ERROR 1045 (28000): Access denied for user '{self.username}'@'{hostname}' (using password: YES)")
            else:
                raise Exception(f"ERROR 1045 (28000): Access denied for user '{self.username}'@'{self.host}' (using password: YES)")
        except Exception as e:
            error_msg = str(e)
            if 'ERROR 1049' in error_msg:
                # Re-raise database errors as-is
                raise e
            elif 'authentication' in error_msg.lower() or 'unauthorized' in error_msg.lower() or 'access denied' in error_msg.lower():
                import socket
                hostname = socket.gethostname()
                raise Exception(f"ERROR 1045 (28000): Access denied for user '{self.username}'@'{hostname}' (using password: YES)")
            else:
                raise Exception(f"ERROR 2003 (HY000): Can't connect to MongoDB server on '{self.host}' ({e})")
    
    def close(self):
        """Close the MongoDB connection"""
        if self.client:
            self.client.close()
    
    def field_exists(self, collection_name: str, field_name: str) -> bool:
        """Check if a field exists in the collection"""
        if self.database is None:
            return False
        
        collection = self.database[collection_name]
        # Check if any document has this field
        result = collection.find_one({field_name: {"$exists": True}})
        return result is not None
    
    def _extract_field_references(self, expression) -> List[str]:
        """Extract field references from MongoDB aggregation expressions"""
        fields = []
        
        if isinstance(expression, str) and expression.startswith('$'):
            # Direct field reference like "$field_name"
            fields.append(expression[1:])  # Remove the $ prefix
        elif isinstance(expression, dict):
            # Recursive search in nested expressions
            for value in expression.values():
                if isinstance(value, (dict, list)):
                    fields.extend(self._extract_field_references(value))
                elif isinstance(value, str) and value.startswith('$'):
                    fields.append(value[1:])  # Remove the $ prefix
        elif isinstance(expression, list):
            # Search in array elements
            for item in expression:
                fields.extend(self._extract_field_references(item))
        
        return fields
    
    def _validate_query_fields(self, mql_query: Dict[str, Any], collection_name: str):
        """Validate that all fields referenced in the query exist in the collection"""
        # Skip validation for now - field validation should happen at a higher level
        # after JOIN processing and alias resolution
        return
    
    def _extract_filter_fields(self, filter_doc: Dict[str, Any]) -> set:
        """Extract field names from MongoDB filter document"""
        fields = set()
        
        for key, value in filter_doc.items():
            if key.startswith('$'):
                # Logical operators like $and, $or
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            fields.update(self._extract_filter_fields(item))
                elif isinstance(value, dict):
                    fields.update(self._extract_filter_fields(value))
            else:
                # Regular field name
                fields.add(key)
        
        return fields
    
    def switch_database(self, database_name: str):
        """Switch to a different database"""
        if not self.client:
            raise Exception("Not connected to MongoDB")
        
        self.database_name = database_name
        self.database = self.client[database_name]
    
    def get_collections(self) -> List[str]:
        """Get list of collections in current database"""
        if self.database is None:
            raise Exception("ERROR 1046 (3D000): No database selected")
        
        return self.database.list_collection_names()
    
    def get_databases(self):
        """Get list of databases"""
        return [db['name'] for db in self.client.list_databases()]
    
    def execute_query(self, mql_query: Dict[str, Any]) -> Any:
        """Execute a MongoDB query"""
        operation = mql_query.get('operation')
        
        # Handle operations that don't require a database selection
        if operation == 'show_databases':
            databases = self.get_databases()
            # Format as list of dictionaries to match table display
            return [{"Database": db} for db in databases]
        
        if operation == 'use_database':
            database_name = mql_query.get('database')
            if not database_name:
                raise Exception("No database name specified")
            self.switch_database(database_name)
            return f"\n\033[1mDatabase changed\033[0m"
        
        # Handle no-table queries (e.g., SELECT 1+1, SELECT NOW())
        if operation == 'eval':
            return self._handle_eval_query(mql_query)
        
        # For other operations, require a database
        if self.database is None:
            raise Exception("ERROR 1046 (3D000): No database selected")
        
        # Handle operations that don't require a collection
        if operation == 'show_collections':
            collections = self.get_collections()
            # Format as list of dictionaries to match table display
            table_name = f"Tables_in_{self.database_name}" if self.database_name else "Tables"
            return [{table_name: collection} for collection in collections]
        
        collection_name = mql_query.get('collection')
        if not collection_name:
            raise Exception("No collection specified")
        
        # Validate fields before executing any query
        self._validate_query_fields(mql_query, collection_name)
        
        collection = self.database[collection_name]
        
        try:
            if operation == 'find':
                filter_doc = mql_query.get('filter', {})
                projection = mql_query.get('projection')
                sort = mql_query.get('sort')
                limit = mql_query.get('limit')
                skip = mql_query.get('skip')
                
                # Exclude _id by default unless specifically requested
                if projection is None:
                    projection = {'_id': 0}
                elif isinstance(projection, dict) and '_id' not in projection:
                    projection['_id'] = 0
                
                cursor = collection.find(filter_doc, projection)
                
                if sort:
                    cursor = cursor.sort(sort)
                if skip:
                    cursor = cursor.skip(skip)
                if limit:
                    cursor = cursor.limit(limit)
                
                return list(cursor)
            
            elif operation == 'insert_one':
                document = mql_query.get('document')
                result = collection.insert_one(document)
                return {'inserted_id': str(result.inserted_id), 'acknowledged': result.acknowledged}
            
            elif operation == 'insert_many':
                documents = mql_query.get('documents')
                result = collection.insert_many(documents)
                return {'inserted_ids': [str(id) for id in result.inserted_ids], 
                       'acknowledged': result.acknowledged}
            
            elif operation == 'update_one':
                filter_doc = mql_query.get('filter', {})
                update_doc = mql_query.get('update')
                upsert = mql_query.get('upsert', False)
                result = collection.update_one(filter_doc, update_doc, upsert=upsert)
                return {'matched_count': result.matched_count, 
                       'modified_count': result.modified_count,
                       'acknowledged': result.acknowledged}
            
            elif operation == 'update_many':
                filter_doc = mql_query.get('filter', {})
                update_doc = mql_query.get('update')
                upsert = mql_query.get('upsert', False)
                result = collection.update_many(filter_doc, update_doc, upsert=upsert)
                return {'matched_count': result.matched_count, 
                       'modified_count': result.modified_count,
                       'acknowledged': result.acknowledged}
            
            elif operation == 'delete_one':
                filter_doc = mql_query.get('filter', {})
                result = collection.delete_one(filter_doc)
                return {'deleted_count': result.deleted_count, 'acknowledged': result.acknowledged}
            
            elif operation == 'delete_many':
                filter_doc = mql_query.get('filter', {})
                result = collection.delete_many(filter_doc)
                return {'deleted_count': result.deleted_count, 'acknowledged': result.acknowledged}
            
            elif operation == 'count':
                filter_doc = mql_query.get('filter', {})
                return collection.count_documents(filter_doc)
            
            elif operation == 'aggregate':
                pipeline = mql_query.get('pipeline', [])
                return list(collection.aggregate(pipeline))
            
            elif operation == 'distinct':
                field = mql_query.get('field')
                filter_doc = mql_query.get('filter', {})
                distinct_values = collection.distinct(field, filter_doc)
                # Format as list of dictionaries for consistent display
                return [{field: value} for value in distinct_values]
            
            else:
                raise Exception(f"Unsupported operation: {operation}")
                
        except OperationFailure as e:
            # Translate MongoDB errors to MySQL equivalents
            if e.code == 26:  # NamespaceNotFound
                raise Exception(f"ERROR 1146 (42S02): Table '{collection_name}' doesn't exist")
            elif e.code == 18:  # AuthenticationFailed
                raise Exception(f"ERROR 1045 (28000): Access denied")
            elif e.code == 13:  # Unauthorized
                raise Exception(f"ERROR 1142 (42000): SELECT command denied")
            else:
                # Generic database error
                raise Exception(f"ERROR 1064 (42000): You have an error in your SQL syntax")
        except Exception as e:
            error_msg = str(e).lower()
            if 'collection' in error_msg and 'not found' in error_msg:
                raise Exception(f"ERROR 1146 (42S02): Table '{collection_name}' doesn't exist")
            elif 'timeout' in error_msg:
                raise Exception(f"ERROR 2006 (HY000): MySQL server has gone away")
            else:
                # Generic error
                raise Exception(f"ERROR 1064 (42000): You have an error in your SQL syntax")

    def _handle_eval_query(self, mql_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle evaluation queries that don't require a collection (e.g., SELECT 1+1, SELECT NOW())"""
        projection = mql_query.get('projection', {})
        
        # Create a single result document by evaluating all the projections
        result_doc = {}
        
        for field_name, expression in projection.items():
            if isinstance(expression, dict) and '$literal' in expression:
                # Simple literal value
                result_doc[field_name] = expression['$literal']
            elif isinstance(expression, dict):
                # MongoDB expression - evaluate it
                # For now, we'll simulate the evaluation since we can't use aggregation without a collection
                result_doc[field_name] = self._evaluate_expression(expression)
            else:
                # Direct value
                result_doc[field_name] = expression
        
        return [result_doc]
    
    def _evaluate_expression(self, expression: Dict[str, Any]) -> Any:
        """Evaluate MongoDB expressions for no-table queries"""
        
        if '$dateToString' in expression:
            # Format date as string
            date_expr = expression['$dateToString']
            if isinstance(date_expr, dict):
                date_part = date_expr.get('date')
                format_str = date_expr.get('format', '%Y-%m-%d')
                
                # Handle nested expressions or direct dateFromString
                if isinstance(date_part, dict):
                    # Check if it's a direct $dateFromString
                    if '$dateFromString' in date_part:
                        date_string = date_part['$dateFromString']['dateString']
                    else:
                        # Recursively evaluate nested expression (like $dateAdd, $dateFromParts, etc.)
                        evaluated_date = self._evaluate_expression(date_part)
                        if evaluated_date:
                            date_string = str(evaluated_date)
                        else:
                            return None
                    
                    from datetime import datetime
                    try:
                        # Try different date formats
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%H:%M:%S']:
                            try:
                                date_obj = datetime.strptime(date_string, fmt)
                                break
                            except:
                                continue
                        else:
                            return None
                        
                        # Convert MongoDB format to Python format
                        python_format = format_str.replace('%Y', '%Y').replace('%m', '%m').replace('%d', '%d')
                        return date_obj.strftime(python_format)
                    except:
                        return None
            return str(date_expr)
        
        elif '$hour' in expression:
            # Extract hour from time/datetime string
            date_expr = expression['$hour']
            if isinstance(date_expr, dict) and '$dateFromString' in date_expr:
                date_string = date_expr['$dateFromString']['dateString']
                from datetime import datetime
                try:
                    # Try different date formats that include time
                    for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%H:%M:%S']:
                        try:
                            date_obj = datetime.strptime(date_string, fmt)
                            return date_obj.hour
                        except:
                            continue
                    return None
                except:
                    return None
            return None
        
        elif '$minute' in expression:
            # Extract minute from time/datetime string
            date_expr = expression['$minute']
            if isinstance(date_expr, dict) and '$dateFromString' in date_expr:
                date_string = date_expr['$dateFromString']['dateString']
                from datetime import datetime
                try:
                    # Try different date formats that include time
                    for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%H:%M:%S']:
                        try:
                            date_obj = datetime.strptime(date_string, fmt)
                            return date_obj.minute
                        except:
                            continue
                    return None
                except:
                    return None
            return None
        
        elif '$second' in expression:
            # Extract second from time/datetime string
            date_expr = expression['$second']
            if isinstance(date_expr, dict) and '$dateFromString' in date_expr:
                date_string = date_expr['$dateFromString']['dateString']
                from datetime import datetime
                try:
                    # Try different date formats that include time
                    for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%H:%M:%S']:
                        try:
                            date_obj = datetime.strptime(date_string, fmt)
                            return date_obj.second
                        except:
                            continue
                    return None
                except:
                    return None
            return None
        
        elif '$add' in expression:
            # Addition
            values = expression['$add']
            if isinstance(values, list):
                try:
                    result = 0
                    for val in values:
                        if isinstance(val, dict):
                            # Recursively evaluate nested expressions
                            val = self._evaluate_expression(val)
                        result += float(val) if val is not None else 0
                    # Preserve integer type if all inputs were integers
                    if all(isinstance(v, int) or (isinstance(v, dict) and isinstance(self._evaluate_expression(v), int)) for v in values):
                        return int(result)
                    return result
                except:
                    return None
            return float(values) if values is not None else None
        
        elif '$cond' in expression:
            # Conditional expression (if-then-else)
            cond_expr = expression['$cond']
            if isinstance(cond_expr, dict):
                if_expr = cond_expr.get('if')
                then_expr = cond_expr.get('then')
                else_expr = cond_expr.get('else')
                
                # Evaluate the condition
                if isinstance(if_expr, dict):
                    condition_result = self._evaluate_expression(if_expr)
                else:
                    condition_result = bool(if_expr)
                
                # Return then or else based on condition
                if condition_result:
                    if isinstance(then_expr, dict):
                        return self._evaluate_expression(then_expr)
                    return then_expr
                else:
                    if isinstance(else_expr, dict):
                        return self._evaluate_expression(else_expr)
                    return else_expr
            return None
        
        elif '$gte' in expression:
            # Greater than or equal comparison
            values = expression['$gte']
            if isinstance(values, list) and len(values) >= 2:
                left, right = values[0], values[1]
                
                # Evaluate nested expressions
                if isinstance(left, dict):
                    left = self._evaluate_expression(left)
                if isinstance(right, dict):
                    right = self._evaluate_expression(right)
                
                try:
                    return float(left) >= float(right)
                except:
                    return str(left) >= str(right)
            return False
        
        elif '$subtract' in expression:
            # Subtraction
            values = expression['$subtract']
            if isinstance(values, list) and len(values) >= 2:
                try:
                    # Evaluate the first value
                    first_val = values[0]
                    if isinstance(first_val, dict):
                        first_val = self._evaluate_expression(first_val)
                    result = float(first_val)
                    
                    # Subtract the remaining values
                    for val in values[1:]:
                        if isinstance(val, dict):
                            # Recursively evaluate nested expressions
                            val = self._evaluate_expression(val)
                        result -= float(val) if val is not None else 0
                    
                    # Preserve integer type if result is a whole number
                    if result == int(result):
                        return int(result)
                    return result
                except:
                    return None
            return None
        
        elif '$toInt' in expression:
            # Convert to integer
            value = expression['$toInt']
            if isinstance(value, dict):
                value = self._evaluate_expression(value)
            try:
                return int(float(value))
            except:
                return None
        
        elif '$divide' in expression:
            # Division
            values = expression['$divide']
            if isinstance(values, list) and len(values) >= 2:
                try:
                    dividend = values[0]
                    divisor = values[1]
                    if isinstance(dividend, dict):
                        dividend = self._evaluate_expression(dividend)
                    if isinstance(divisor, dict):
                        divisor = self._evaluate_expression(divisor)
                    return float(dividend) / float(divisor)
                except:
                    return None
            return None
        
        elif '$abs' in expression:
            # Absolute value
            value = expression['$abs']
            try:
                # Preserve integer type if the input is an integer
                if isinstance(value, int):
                    return abs(value)
                else:
                    return abs(float(value))
            except:
                return None
        
        elif '$toUpper' in expression:
            # Convert to uppercase
            value = expression['$toUpper']
            if isinstance(value, str):
                return value.upper()
            return value
        
        elif '$toLower' in expression:
            # Convert to lowercase
            value = expression['$toLower']
            if isinstance(value, str):
                return value.lower()
            return value
        
        elif '$concat' in expression:
            # String concatenation
            values = expression['$concat']
            if isinstance(values, list):
                return ''.join(str(v) for v in values)
            return str(values)
        
        elif '$strLenCP' in expression:
            # String length
            value = expression['$strLenCP']
            return len(str(value))
        
        elif '$substr' in expression:
            # Substring
            values = expression['$substr']
            if isinstance(values, list) and len(values) >= 3:
                string, start, length = values[0], values[1], values[2]
                
                # Evaluate any nested expressions
                if isinstance(string, dict):
                    string = self._evaluate_expression(string)
                if isinstance(start, dict):
                    start = self._evaluate_expression(start)
                if isinstance(length, dict):
                    length = self._evaluate_expression(length)
                
                # Convert to proper types
                string = str(string)
                start = int(start) if start is not None else 0
                length = int(length) if length is not None else len(string)
                
                # Ensure start is not negative and doesn't exceed string length
                start = max(0, min(start, len(string)))
                length = max(0, length)
                
                return string[start:start+length]
            return str(values)
        
        elif '$trim' in expression:
            # Trim whitespace
            value = expression['$trim']
            return str(value).strip()
        
        elif '$replaceAll' in expression:
            # Replace all occurrences
            values = expression['$replaceAll']
            if isinstance(values, list) and len(values) >= 3:
                string, find, replace = values[0], values[1], values[2]
                return str(string).replace(str(find), str(replace))
            return str(values)
        
        elif '$reverse' in expression:
            # Reverse string
            value = expression['$reverse']
            return str(value)[::-1]
        
        elif '$round' in expression:
            # Round to decimal places
            values = expression['$round']
            if isinstance(values, list) and len(values) >= 2:
                number, precision = values[0], values[1]
                return round(float(number), int(precision))
            else:
                return round(float(values))
        
        elif '$ceil' in expression:
            # Ceiling
            value = expression['$ceil']
            import math
            return math.ceil(float(value))
        
        elif '$floor' in expression:
            # Floor
            value = expression['$floor']
            import math
            return math.floor(float(value))
        
        elif '$sqrt' in expression:
            # Square root
            value = expression['$sqrt']
            import math
            return math.sqrt(float(value))
        
        elif '$pow' in expression:
            # Power
            values = expression['$pow']
            if isinstance(values, list) and len(values) >= 2:
                base, exponent = values[0], values[1]
                return pow(float(base), float(exponent))
            return float(values)
        
        elif '$sin' in expression:
            # Sine
            value = expression['$sin']
            if isinstance(value, dict):
                value = self._evaluate_expression(value)
            import math
            return math.sin(float(value))
        
        elif '$cos' in expression:
            # Cosine
            value = expression['$cos']
            if isinstance(value, dict):
                value = self._evaluate_expression(value)
            import math
            return math.cos(float(value))
        
        elif '$ln' in expression:
            # Natural logarithm
            value = expression['$ln']
            import math
            return math.log(float(value))
        
        elif '$max' in expression:
            # Maximum value
            values = expression['$max']
            if isinstance(values, list):
                return max(float(v) for v in values)
            return float(values)
        
        elif '$dateFromParts' in expression:
            # Date from parts
            parts = expression['$dateFromParts']
            from datetime import datetime
            try:
                year = parts.get('year', 1970)
                month = parts.get('month', 1)
                day = parts.get('day', 1)
                hour = parts.get('hour', 0)
                minute = parts.get('minute', 0)
                second = parts.get('second', 0)
                
                # Recursively evaluate if parts are expressions
                if isinstance(year, dict):
                    year = self._evaluate_expression(year)
                if isinstance(month, dict):
                    month = self._evaluate_expression(month)
                if isinstance(day, dict):
                    day = self._evaluate_expression(day)
                if isinstance(hour, dict):
                    hour = self._evaluate_expression(hour)
                if isinstance(minute, dict):
                    minute = self._evaluate_expression(minute)
                if isinstance(second, dict):
                    second = self._evaluate_expression(second)
                
                date_obj = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                
                # If only time components are significant (year=1970, month=1, day=1), return time format
                if int(year) == 1970 and int(month) == 1 and int(day) == 1:
                    return date_obj.strftime('%H:%M:%S')
                else:
                    return date_obj.strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                return None
        
        elif '$dateAdd' in expression:
            # Date add
            add_parts = expression['$dateAdd']
            from datetime import datetime, timedelta
            try:
                start_date = add_parts.get('startDate')
                unit = add_parts.get('unit', 'day')
                amount = add_parts.get('amount', 0)
                
                # Recursively evaluate start date if it's an expression
                if isinstance(start_date, dict):
                    start_date = self._evaluate_expression(start_date)
                
                # Parse start date
                if isinstance(start_date, str):
                    # Try different date formats
                    date_obj = None
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%H:%M:%S']:
                        try:
                            date_obj = datetime.strptime(start_date, fmt)
                            break
                        except:
                            continue
                    
                    if not date_obj:
                        return None
                else:
                    return None
                
                # Add based on unit
                if unit in ['day', 'days']:
                    date_obj += timedelta(days=int(amount))
                elif unit in ['hour', 'hours']:
                    date_obj += timedelta(hours=int(amount))
                elif unit in ['minute', 'minutes']:
                    date_obj += timedelta(minutes=int(amount))
                elif unit in ['second', 'seconds']:
                    date_obj += timedelta(seconds=int(amount))
                elif unit in ['millisecond', 'milliseconds']:
                    date_obj += timedelta(milliseconds=int(amount))
                elif unit in ['week', 'weeks']:
                    date_obj += timedelta(weeks=int(amount))
                elif unit in ['month', 'months']:
                    # Proper month addition
                    year = date_obj.year
                    month = date_obj.month + int(amount)
                    day = date_obj.day
                    
                    # Handle month overflow
                    while month > 12:
                        year += 1
                        month -= 12
                    while month < 1:
                        year -= 1
                        month += 12
                    
                    # Handle day overflow for shorter months
                    import calendar
                    max_day = calendar.monthrange(year, month)[1]
                    if day > max_day:
                        day = max_day
                    
                    date_obj = date_obj.replace(year=year, month=month, day=day)
                elif unit in ['year', 'years']:
                    # Proper year addition
                    year = date_obj.year + int(amount)
                    date_obj = date_obj.replace(year=year)
                elif unit in ['quarter', 'quarters']:
                    # Quarter is 3 months
                    year = date_obj.year
                    month = date_obj.month + (int(amount) * 3)
                    day = date_obj.day
                    
                    # Handle month overflow
                    while month > 12:
                        year += 1
                        month -= 12
                    while month < 1:
                        year -= 1
                        month += 12
                    
                    # Handle day overflow for shorter months
                    import calendar
                    max_day = calendar.monthrange(year, month)[1]
                    if day > max_day:
                        day = max_day
                    
                    date_obj = date_obj.replace(year=year, month=month, day=day)
                
                # Return appropriate format
                if unit in ['hour', 'hours', 'minute', 'minutes', 'second', 'seconds', 'millisecond', 'milliseconds']:
                    return date_obj.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    return date_obj.strftime('%Y-%m-%d')
            except Exception as e:
                return None
        
        elif '$dateSubtract' in expression:
            # Date subtract
            sub_parts = expression['$dateSubtract']
            from datetime import datetime, timedelta
            try:
                start_date = sub_parts.get('startDate')
                unit = sub_parts.get('unit', 'day')
                amount = sub_parts.get('amount', 0)
                
                # Recursively evaluate start date if it's an expression
                if isinstance(start_date, dict):
                    start_date = self._evaluate_expression(start_date)
                
                # Parse start date
                if isinstance(start_date, str):
                    # Try different date formats
                    date_obj = None
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%H:%M:%S']:
                        try:
                            date_obj = datetime.strptime(start_date, fmt)
                            break
                        except:
                            continue
                    
                    if not date_obj:
                        return None
                else:
                    return None
                
                # Subtract based on unit  
                if unit in ['day', 'days']:
                    date_obj -= timedelta(days=int(amount))
                elif unit in ['hour', 'hours']:
                    date_obj -= timedelta(hours=int(amount))
                elif unit in ['minute', 'minutes']:
                    date_obj -= timedelta(minutes=int(amount))
                elif unit in ['second', 'seconds']:
                    date_obj -= timedelta(seconds=int(amount))
                elif unit in ['millisecond', 'milliseconds']:
                    date_obj -= timedelta(milliseconds=int(amount))
                elif unit in ['week', 'weeks']:
                    date_obj -= timedelta(weeks=int(amount))
                elif unit in ['month', 'months']:
                    # Proper month subtraction
                    year = date_obj.year
                    month = date_obj.month - int(amount)
                    day = date_obj.day
                    
                    # Handle month underflow
                    while month < 1:
                        year -= 1
                        month += 12
                    while month > 12:
                        year += 1
                        month -= 12
                    
                    # Handle day overflow for shorter months
                    import calendar
                    max_day = calendar.monthrange(year, month)[1]
                    if day > max_day:
                        day = max_day
                    
                    date_obj = date_obj.replace(year=year, month=month, day=day)
                elif unit in ['year', 'years']:
                    # Proper year subtraction
                    year = date_obj.year - int(amount)
                    date_obj = date_obj.replace(year=year)
                elif unit in ['quarter', 'quarters']:
                    # Quarter is 3 months
                    year = date_obj.year
                    month = date_obj.month - (int(amount) * 3)
                    day = date_obj.day
                    
                    # Handle month underflow
                    while month < 1:
                        year -= 1
                        month += 12
                    while month > 12:
                        year += 1
                        month -= 12
                    
                    # Handle day overflow for shorter months
                    import calendar
                    max_day = calendar.monthrange(year, month)[1]
                    if day > max_day:
                        day = max_day
                    
                    date_obj = date_obj.replace(year=year, month=month, day=day)
                
                # Return appropriate format
                if unit in ['hour', 'hours', 'minute', 'minutes', 'second', 'seconds', 'millisecond', 'milliseconds']:
                    return date_obj.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    return date_obj.strftime('%Y-%m-%d')
            except Exception as e:
                return None
        
        elif '$dateFromString' in expression:
            # Parse date from string
            date_expr = expression['$dateFromString']
            if isinstance(date_expr, dict):
                date_string = date_expr.get('dateString', '')
                # Simply return the date string as-is since it's already in the right format
                return str(date_string).strip("'\"")
            return None
        
        elif '$year' in expression:
            # Extract year
            date_expr = expression['$year']
            from datetime import datetime
            try:
                if isinstance(date_expr, str):
                    date_obj = datetime.strptime(date_expr, '%Y-%m-%d')
                    return date_obj.year
                elif isinstance(date_expr, dict) and '$dateFromString' in date_expr:
                    date_string = date_expr['$dateFromString']['dateString']
                    date_obj = datetime.strptime(date_string, '%Y-%m-%d')
                    return date_obj.year
            except:
                pass
            return None
        
        elif '$month' in expression:
            # Extract month
            date_expr = expression['$month']
            from datetime import datetime
            try:
                if isinstance(date_expr, str):
                    date_obj = datetime.strptime(date_expr, '%Y-%m-%d')
                    return date_obj.month
                elif isinstance(date_expr, dict) and '$dateFromString' in date_expr:
                    date_string = date_expr['$dateFromString']['dateString']
                    date_obj = datetime.strptime(date_string, '%Y-%m-%d')
                    return date_obj.month
            except:
                pass
            return None
        
        elif '$toDays' in expression:
            # Custom TO_DAYS implementation
            date_expr = expression['$toDays']
            from datetime import datetime
            try:
                if isinstance(date_expr, dict) and '$dateFromString' in date_expr:
                    date_string = date_expr['$dateFromString']['dateString']
                else:
                    date_string = str(date_expr).strip("'\"")
                
                # Parse the date
                date_obj = None
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%H:%M:%S']:
                    try:
                        date_obj = datetime.strptime(date_string, fmt)
                        break
                    except:
                        continue
                
                if not date_obj:
                    return None
                
                # Calculate days since year 0000-01-01 (MariaDB epoch)
                # This is the algorithm used by MariaDB
                year = date_obj.year
                month = date_obj.month
                day = date_obj.day
                
                # MariaDB TO_DAYS calculation
                if year < 1 or year > 9999:
                    return None
                
                # Algorithm from MariaDB source
                days = 365 * year + (year - 1) // 4 - (year - 1) // 100 + (year - 1) // 400
                
                # Days for months
                month_days = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
                days += month_days[month - 1]
                
                # Add leap day if needed
                if month > 2 and year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                    days += 1
                
                days += day
                
                return days
            except Exception as e:
                return None
        
        elif '$timestampAdd' in expression:
            # Custom TIMESTAMPADD implementation
            add_expr = expression['$timestampAdd']
            unit = add_expr.get('unit', '').upper()
            interval = add_expr.get('interval', 0)
            date_expr = add_expr.get('date')
            
            from datetime import datetime, timedelta
            try:
                # Evaluate the date expression
                if isinstance(date_expr, dict):
                    date_str = self._evaluate_expression(date_expr)
                else:
                    date_str = str(date_expr).strip("'\"")
                
                # Parse the date
                date_obj = None
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%H:%M:%S']:
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        break
                    except:
                        continue
                
                if not date_obj:
                    return None
                
                # Add the interval based on unit
                if unit in ['DAY', 'DAYS']:
                    date_obj += timedelta(days=int(interval))
                elif unit in ['HOUR', 'HOURS']:
                    date_obj += timedelta(hours=int(interval))
                elif unit in ['MINUTE', 'MINUTES']:
                    date_obj += timedelta(minutes=int(interval))
                elif unit in ['SECOND', 'SECONDS']:
                    date_obj += timedelta(seconds=int(interval))
                elif unit in ['WEEK', 'WEEKS']:
                    date_obj += timedelta(weeks=int(interval))
                elif unit in ['MONTH', 'MONTHS']:
                    # Proper month addition
                    year = date_obj.year
                    month = date_obj.month + int(interval)
                    day = date_obj.day
                    
                    while month > 12:
                        year += 1
                        month -= 12
                    while month < 1:
                        year -= 1
                        month += 12
                    
                    import calendar
                    max_day = calendar.monthrange(year, month)[1]
                    if day > max_day:
                        day = max_day
                    
                    date_obj = date_obj.replace(year=year, month=month, day=day)
                elif unit in ['YEAR', 'YEARS']:
                    year = date_obj.year + int(interval)
                    date_obj = date_obj.replace(year=year)
                elif unit in ['QUARTER', 'QUARTERS']:
                    # Quarter is 3 months
                    year = date_obj.year
                    month = date_obj.month + (int(interval) * 3)
                    day = date_obj.day
                    
                    while month > 12:
                        year += 1
                        month -= 12
                    while month < 1:
                        year -= 1
                        month += 12
                    
                    import calendar
                    max_day = calendar.monthrange(year, month)[1]
                    if day > max_day:
                        day = max_day
                    
                    date_obj = date_obj.replace(year=year, month=month, day=day)
                
                # Return in appropriate format
                if len(date_str) == 10:  # Date only
                    return date_obj.strftime('%Y-%m-%d')
                else:
                    return date_obj.strftime('%Y-%m-%d %H:%M:%S')
                    
            except Exception as e:
                return None
        
        elif '$addTime' in expression:
            # Custom ADDTIME implementation
            add_expr = expression['$addTime']
            datetime_expr = add_expr.get('datetime')
            time_str = add_expr.get('time', '')
            
            from datetime import datetime, timedelta
            try:
                # Evaluate the datetime expression
                if isinstance(datetime_expr, dict):
                    datetime_str = self._evaluate_expression(datetime_expr)
                else:
                    datetime_str = str(datetime_expr).strip("'\"")
                
                # Parse the datetime
                datetime_obj = None
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%H:%M:%S']:
                    try:
                        datetime_obj = datetime.strptime(datetime_str, fmt)
                        break
                    except:
                        continue
                
                if not datetime_obj:
                    return None
                
                # Parse the time to add
                time_parts = time_str.split(':')
                if len(time_parts) >= 3:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = int(float(time_parts[2]))
                    
                    datetime_obj += timedelta(hours=hours, minutes=minutes, seconds=seconds)
                    
                    # Return in same format as input
                    if len(datetime_str) > 10:  # Input was datetime
                        return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
                    else:  # Input was just time
                        return datetime_obj.strftime('%H:%M:%S')
                
            except Exception as e:
                return None
        
        elif '$subTime' in expression:
            # Custom SUBTIME implementation
            sub_expr = expression['$subTime']
            datetime_expr = sub_expr.get('datetime')
            time_str = sub_expr.get('time', '')
            
            from datetime import datetime, timedelta
            try:
                # Evaluate the datetime expression
                if isinstance(datetime_expr, dict):
                    datetime_str = self._evaluate_expression(datetime_expr)
                else:
                    datetime_str = str(datetime_expr).strip("'\"")
                
                # Parse the datetime
                datetime_obj = None
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%H:%M:%S']:
                    try:
                        datetime_obj = datetime.strptime(datetime_str, fmt)
                        break
                    except:
                        continue
                
                if not datetime_obj:
                    return None
                
                # Parse the time to subtract
                time_parts = time_str.split(':')
                if len(time_parts) >= 3:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = int(float(time_parts[2]))
                    
                    datetime_obj -= timedelta(hours=hours, minutes=minutes, seconds=seconds)
                    
                    # Return in same format as input
                    if len(datetime_str) > 10:  # Input was datetime
                        return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
                    else:  # Input was just time
                        return datetime_obj.strftime('%H:%M:%S')
                
            except Exception as e:
                return None
        
        elif '$dayOfMonth' in expression:
            # Extract day of month
            date_expr = expression['$dayOfMonth']
            from datetime import datetime
            try:
                if isinstance(date_expr, str):
                    date_obj = datetime.strptime(date_expr, '%Y-%m-%d')
                    return date_obj.day
                elif isinstance(date_expr, dict) and '$dateFromString' in date_expr:
                    date_string = date_expr['$dateFromString']['dateString']
                    date_obj = datetime.strptime(date_string, '%Y-%m-%d')
                    return date_obj.day
            except:
                pass
            return None
        
        # Add more expression evaluations as needed
        
        # Default: return the expression as-is
        return str(expression)
