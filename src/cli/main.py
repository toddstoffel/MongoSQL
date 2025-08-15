"""
Main CLI module for mongosql client
"""
import click
import os
import sys
import getpass
import readline
import time
from dotenv import load_dotenv

# Lazy loading - only import when needed
_mongodb_client = None
_sql_parser = None
_sql_translator = None
_utils_imported = False

def get_mongodb_client():
    """Lazy load MongoDB client"""
    global _mongodb_client
    if _mongodb_client is None:
        from ..database.mongodb_client import MongoDBClient
        _mongodb_client = MongoDBClient
    return _mongodb_client

def get_sql_parser():
    """Lazy load SQL parser"""
    global _sql_parser
    if _sql_parser is None:
        from ..parsers.token_sql_parser import TokenBasedSQLParser
        _sql_parser = TokenBasedSQLParser()
    return _sql_parser

def get_sql_translator():
    """Lazy load SQL translator"""
    global _sql_translator
    if _sql_translator is None:
        from ..translators.sql_to_mql import MongoSQLTranslator
        _sql_translator = MongoSQLTranslator()
    return _sql_translator

def ensure_utils_imported():
    """Ensure utils are imported"""
    global _utils_imported, get_table_columns, format_value, is_numeric_column
    if not _utils_imported:
        from ..utils.schema import get_table_columns, format_value, is_numeric_column
        globals()['get_table_columns'] = get_table_columns
        globals()['format_value'] = format_value
        globals()['is_numeric_column'] = is_numeric_column
        _utils_imported = True

# Load environment variables only when needed
load_dotenv()

@click.command()
@click.argument('database', required=False)
@click.option('--host', '-h', default=None, help='MongoDB host')
@click.option('--port', '-P', default=None, help='MongoDB port')
@click.option('--username', '-u', default=None, help='Username')
@click.option('--password', '-p', is_flag=True, help='Prompt for password')
@click.option('--execute', '-e', help='Execute statement and exit')
@click.option('--batch', is_flag=True, help='Run in batch mode (non-interactive)')
def main(database, host, port, username, password, execute, batch):
    """MongoSQL - A command-line client that translates SQL to MongoDB queries
    
    DATABASE is the name of the database to connect to (optional)
    """
    
    # Check if input is coming from a pipe (like echo | mongosql)
    is_piped_input = not sys.stdin.isatty()
    
    # Get connection parameters
    mongo_host = host or os.getenv('MONGO_HOST') or os.getenv('MONGODB_HOST', 'localhost')
    mongo_port = int(port or os.getenv('MONGO_PORT') or os.getenv('MONGODB_PORT', 27017))
    mongo_db = database or os.getenv('MONGO_DATABASE') or os.getenv('MONGODB_DATABASE')
    mongo_user = username or os.getenv('MONGO_USERNAME') or os.getenv('MONGODB_USERNAME')
    mongo_pass = os.getenv('MONGO_PASSWORD') or os.getenv('MONGODB_PASSWORD')
    
    if password:
        mongo_pass = getpass.getpass("Enter password: ")
    
    # Database is optional - can be None for initial connection
    
    try:
        # Initialize components using lazy loading
        MongoDBClient = get_mongodb_client()
        db_client = MongoDBClient(
            host=mongo_host,
            port=mongo_port, 
            database=mongo_db,
            username=mongo_user,
            password=mongo_pass
        )
        sql_parser = get_sql_parser()
        translator = get_sql_translator()
        
        # Connect to MongoDB (without requiring a database)
        db_client.connect()
        
        if execute:
            # Execute single statement and exit
            execute_statement(execute, sql_parser, translator, db_client, silent=False, is_execute_mode=True)
        elif batch or is_piped_input:
            # Batch mode - read from stdin (silent for piped input)
            run_batch_mode(sql_parser, translator, db_client, silent=is_piped_input)
        else:
            # Interactive mode - show welcome message
            if not is_piped_input:
                print_welcome()
            run_interactive_mode(sql_parser, translator, db_client)
            
    except Exception as e:
        error_msg = str(e)
        if error_msg.startswith("ERROR"):
            # Already formatted as MySQL/MariaDB error
            print(error_msg, file=sys.stderr)
        else:
            # Legacy error handling
            error_msg_lower = error_msg.lower()
            if 'authentication failed' in error_msg_lower or 'access denied' in error_msg_lower or 'unauthorized' in error_msg_lower:
                # Authentication error - format like MySQL
                username_display = mongo_user or 'unknown'
                import socket
                hostname = socket.gethostname()
                print(f"ERROR 1045 (28000): Access denied for user '{username_display}'@'{hostname}' (using password: {'YES' if mongo_pass else 'NO'})", file=sys.stderr)
            elif 'connection' in error_msg_lower or 'timeout' in error_msg_lower or 'refused' in error_msg_lower:
                # Connection error - format like MySQL
                print(f"ERROR 2003 (HY000): Can't connect to MongoDB server on '{mongo_host}' ({mongo_port})", file=sys.stderr)
            else:
                # Generic error
                print(f"ERROR: {error_msg}", file=sys.stderr)
        return 1
    finally:
        if 'db_client' in locals():
            db_client.close()
    
    return 0

def print_welcome():
    """Print MariaDB-style welcome message"""
    print(f"Welcome to the MongoSQL monitor. Commands end with ; or \\g.")
    print(f"Your MongoSQL connection id is 1")
    print(f"Server version: MongoDB (via mongosql translator)")
    print(f"")
    print(f"Copyright (c) 2025, MongoSQL contributors")
    print(f"")
    print(f"Type 'help;' or '\\h' for help. Type '\\c' to clear the current input statement.")
    print()

def execute_statement(sql, parser, translator, db_client, vertical_format=False, silent=False, is_execute_mode=False):
    """Execute a single SQL statement"""
    try:
        # Remove trailing semicolon if present
        sql = sql.rstrip(';')
        
        # Check for \G terminator (vertical format)
        if sql.endswith('\\G'):
            sql = sql[:-2].strip()
            vertical_format = True
        elif sql.endswith('\\g'):
            sql = sql[:-2].strip()
        
        # Start timing
        start_time = time.time()
        
        # Parse SQL
        parsed = parser.parse(sql)
        
        # Translate to MQL
        mql_query = translator.translate(parsed)
        
        # Execute query
        result = db_client.execute_query(mql_query)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Display result
        display_result(result, mql_query, vertical_format, execution_time, is_execute_mode, silent, parsed)
        
    except Exception as e:
        if not silent:
            error_msg = str(e)
            if error_msg.startswith("ERROR"):
                # Already formatted as MySQL/MariaDB error
                print(error_msg, file=sys.stderr)
            else:
                # Generic error, add ERROR prefix
                print(f"ERROR: {error_msg}", file=sys.stderr)

def run_batch_mode(parser, translator, db_client, silent=False):
    """Run in batch mode reading from stdin"""
    for line in sys.stdin:
        line = line.strip()
        if line and not line.startswith('#'):
            execute_statement(line, parser, translator, db_client, silent=silent)

def run_interactive_mode(parser, translator, db_client):
    """Run in interactive mode"""
    
    # Configure readline for command history and arrow keys
    readline.parse_and_bind('tab: complete')
    readline.parse_and_bind('set editing-mode emacs')
    
    # Set up history file
    history_file = os.path.expanduser('~/.mongosql_history')
    try:
        readline.read_history_file(history_file)
        # Limit history to 1000 entries
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass
    
    try:
        while True:
            try:
                # Get current database name for prompt
                current_db = db_client.database_name or "none"
                
                # Get input with MySQL-style prompt showing database
                sql = input(f"mongosql [{current_db}]> ")
                
                if not sql:
                    continue
                    
                sql = sql.strip()
                
                # Handle \g and \G terminators (equivalent to semicolon in MySQL)
                vertical_format = False
                if sql.endswith('\\G'):
                    sql = sql[:-2].strip()  # Remove \G and execute with vertical format
                    vertical_format = True
                elif sql.endswith('\\g'):
                    sql = sql[:-2].strip()  # Remove \g and execute
                elif sql in ['\\G', '\\g']:
                    # Just \G or \g by itself - nothing to execute
                    continue
                
                # Handle special commands
                if sql.lower() in ['quit', 'exit', 'q', '\\q']:
                    print("Bye")
                    break
                elif sql.lower() in ['help', 'help;', 'help\\g', 'help\\G']:
                    show_help()
                    continue
                elif sql.lower() in ['show tables', 'show tables;', 'show tables\\g', 'show tables\\G']:
                    show_collections(db_client)
                    continue
                elif sql.lower() in ['show databases', 'show databases;', 'show databases\\g', 'show databases\\G']:
                    show_databases(db_client)
                    continue
                elif sql.lower().startswith('use '):
                    db_name = sql[4:].strip().rstrip(';').rstrip('\\g').rstrip('\\G')
                    db_client.switch_database(db_name)
                    print()  # Blank line before message
                    print(f"Database changed")
                    continue
                elif sql == '\\c':
                    print("Query buffer cleared.")
                    continue
                
                # Execute SQL statement
                execute_statement(sql, parser, translator, db_client, vertical_format)
                
            except KeyboardInterrupt:
                print("\nQuery aborted.")
            except EOFError:
                print("\nBye")
                break
    finally:
        # Save history file on exit
        try:
            readline.write_history_file(history_file)
        except:
            pass

def show_help():
    """Display help information in MySQL style"""
    print()
    print("General information about MongoSQL:")
    print()
    print("List of all MongoSQL commands:")
    print("Note that all text commands must be first on line and end with ';'")
    print()
    print("help    (\\h)    Display this help.")
    print("quit    (\\q)    Quit mongosql.")
    print("use     \\u      Use another database. Takes database name as argument.")
    print("SHOW TABLES     Show all tables (collections) in current database.")
    print()
    print("For server side help, type 'help contents'")
    print()

def show_collections(db_client):
    """Show available collections in MySQL style"""
    try:
        collections = db_client.get_collections()
        if collections:
            # Calculate proper column width
            db_name = db_client.database_name or 'db'
            header = f"Collections_in_{db_name}"
            
            # Find the maximum width needed
            max_width = len(header)
            for collection in collections:
                if len(collection) > max_width:
                    max_width = len(collection)
            
            # Ensure minimum width
            max_width = max(max_width, 20)
            
            # Print table with proper width
            border = '+' + '-' * (max_width + 2) + '+'
            print(border)
            print(f"| {header:<{max_width}} |")
            print(border)
            for collection in collections:
                print(f"| {collection:<{max_width}} |")
            print(border)
            print()
        else:
            print("Empty set (0.00 sec)")
            print()
    except Exception as e:
        print(f"ERROR: {e}")

def show_databases(db_client):
    """Show available databases in MySQL style"""
    try:
        databases = db_client.get_databases()
        if databases:
            # Calculate proper column width
            header = "Database"
            
            # Find the maximum width needed
            max_width = len(header)
            for database in databases:
                if len(database) > max_width:
                    max_width = len(database)
            
            # Ensure minimum width
            max_width = max(max_width, 20)
            
            # Print table with proper width
            border = '+' + '-' * (max_width + 2) + '+'
            print(border)
            print(f"| {header:<{max_width}} |")
            print(border)
            for database in databases:
                print(f"| {database:<{max_width}} |")
            print(border)
            print()
        else:
            print("Empty set (0.00 sec)")
            print()
    except Exception as e:
        print(f"ERROR: {e}")

def display_result(result, mql_query, vertical_format=False, execution_time=0.0, is_execute_mode=False, silent=False, parsed_sql=None):
    """Display query result in MySQL/MariaDB client style"""
    
    # Handle USE database result
    if mql_query.get('operation') == 'use_database' and isinstance(result, str):
        if not silent:
            print(result)
        return
    
    # Handle COUNT results
    if mql_query.get('operation') == 'count' and isinstance(result, int):
        # Format COUNT result as a table
        count_result = [{'COUNT(*)': result}]
        display_mysql_table(count_result, False, execution_time, is_execute_mode, silent, None, None)
        return
    
    if isinstance(result, list):
        if result:
            # Display as MySQL-style table
            if isinstance(result[0], dict):
                # Check if this is a SHOW operation
                is_show_operation = mql_query.get('operation', '').startswith('show_')
                if vertical_format and not is_show_operation:
                    display_mysql_vertical(result, execution_time, is_execute_mode, silent)
                else:
                    query_columns = parsed_sql.get('columns', []) if parsed_sql else []
                    table_name = parsed_sql.get('from') if parsed_sql else None
                    display_mysql_table(result, is_show_operation, execution_time, is_execute_mode, silent, query_columns, table_name)
            else:
                for item in result:
                    print(item)
        else:
            if not is_execute_mode and not silent:
                print(f"Empty set ({execution_time:.2f} sec)")
                print()
    else:
        # Handle non-query results (INSERT, UPDATE, DELETE)
        if not is_execute_mode:
            if isinstance(result, dict):
                if 'inserted_id' in result:
                    print(f"Query OK, 1 row affected ({execution_time:.2f} sec)")
                    print()
                elif 'matched_count' in result:
                    print(f"Query OK, {result.get('modified_count', 0)} rows affected ({execution_time:.2f} sec)")
                    if result.get('matched_count', 0) > result.get('modified_count', 0):
                        print(f"Rows matched: {result['matched_count']}  Changed: {result['modified_count']}  Warnings: 0")
                    print()
                elif 'deleted_count' in result:
                    print(f"Query OK, {result.get('deleted_count', 0)} rows affected ({execution_time:.2f} sec)")
                    print()
                else:
                    print(f"Query OK ({execution_time:.2f} sec)")
                    print()
            else:
                print(f"Query OK ({execution_time:.2f} sec)")
                print()

def display_tab_format(results, query_columns=None):
    """Display results in tab-separated format (for piped output, matches MariaDB)"""
    if not results:
        return
    
    # Determine column order - same logic as table format
    if query_columns and query_columns != ['*']:
        columns = []
        for col in query_columns:
            if isinstance(col, dict):
                if 'column' in col:
                    columns.append(col['column'])
                elif 'function' in col:
                    if 'original_call' in col:
                        columns.append(col['original_call'])
                    else:
                        func_name = col['function']
                        args_str = col.get('args_str', '')
                        if args_str:
                            columns.append(f"{func_name}({args_str})")
                        else:
                            columns.append(func_name)
            else:
                # Handle string columns (including aliases like "1 as test")
                col_str = str(col)
                
                # Check if this is an alias expression (e.g., "1 as test")
                if ' as ' in col_str.lower():
                    # Extract the alias part (case-insensitive)
                    col_lower = col_str.lower()
                    as_pos = col_lower.rfind(' as ')
                    if as_pos != -1:
                        alias_part = col_str[as_pos + 4:].strip()  # +4 for " as "
                        columns.append(alias_part)
                    else:
                        columns.append(col_str)
                else:
                    columns.append(col_str)
        columns = [col for col in columns if any(col in doc for doc in results)]
    else:
        # Auto-detect columns, prioritize schema order
        all_columns = set()
        for doc in results:
            all_columns.update(doc.keys())
        columns = list(all_columns)
    
    # Print header (column names)
    print('\t'.join(columns))
    
    # Print data rows
    for doc in results:
        row_values = []
        for col in columns:
            value = doc.get(col, '')
            # Format value similar to format_value but simpler for tab output
            if value is None:
                row_values.append('NULL')
            else:
                row_values.append(str(value))
        print('\t'.join(row_values))

def display_mysql_table(results, is_show_operation=False, execution_time=0.0, is_execute_mode=False, silent=False, query_columns=None, table_name=None):
    """Display results in MySQL/MariaDB table format"""
    ensure_utils_imported()  # Ensure utils are loaded
    
    if not results:
        return
    
    # Check if output should be tab-formatted (for piped input, matches MariaDB behavior)
    is_piped = silent
    
    if is_piped:
        # Tab-separated format for piped output (matches MariaDB behavior)
        display_tab_format(results, query_columns)
        return
    
    # If query_columns is provided (from SELECT statement), use that order
    if query_columns and query_columns != ['*']:
        # Use the exact column order from the SQL query
        columns = []
        for col in query_columns:
            if isinstance(col, dict):
                if 'column' in col:
                    columns.append(col['column'])
                elif 'function' in col:
                    # For function calls, use the original call or generate from parts
                    if 'original_call' in col:
                        # Use the exact original function call for the header
                        columns.append(col['original_call'])
                    else:
                        # Fallback: reconstruct from function name and args
                        func_name = col['function']
                        args_str = col.get('args_str', '')
                        if args_str:
                            columns.append(f"{func_name}({args_str})")
                        else:
                            columns.append(f"{func_name}()")
                else:
                    columns.append(str(col))
            else:
                # Handle string columns (including aliases like "1 as test")
                col_str = str(col)
                
                # Check if this is an alias expression (e.g., "1 as test")
                if ' as ' in col_str.lower():
                    # Extract the alias part (case-insensitive)
                    col_lower = col_str.lower()
                    as_pos = col_lower.rfind(' as ')
                    if as_pos != -1:
                        alias_part = col_str[as_pos + 4:].strip()  # +4 for " as "
                        columns.append(alias_part)
                    else:
                        columns.append(col_str)
                else:
                    # Handle qualified column names (table.column -> column)
                    if isinstance(col, str) and '.' in col:
                        col = col.split('.')[-1]
                    columns.append(col_str)
        # Only include columns that actually exist in the results
        columns = [col for col in columns if any(col in doc for doc in results)]
    else:
        # For SELECT * or when no specific columns, try to use schema order as fallback
        all_columns = set()
        for doc in results:
            for key in doc.keys():
                if key != '_id':  # Exclude MongoDB's _id
                    all_columns.add(key)
        
        # Try to get proper column order from schema
        columns = list(all_columns)
        
        # If we know the table name from the query, use its schema
        if table_name:
            schema_cols = get_table_columns(table_name)
            if schema_cols and all(col in schema_cols for col in all_columns):
                # Order columns according to schema
                columns = [col for col in schema_cols if col in all_columns]
            else:
                # If no schema match, use alphabetical order
                columns = sorted(all_columns)
        else:
            # Fallback: try to match against known schemas
            possible_tables = ['customers', 'products', 'orders', 'orderdetails', 'payments', 'employees', 'offices', 'productlines']
            # Find the table that matches our columns best
            for table in possible_tables:
                schema_cols = get_table_columns(table)
                if schema_cols and all(col in schema_cols for col in all_columns):
                    # Order columns according to schema
                    columns = [col for col in schema_cols if col in all_columns]
                    break
            
            # If no schema match, use alphabetical order (fallback)
            if not any(col in get_table_columns(table) for table in possible_tables for col in all_columns):
                columns = sorted(all_columns)
    
    # Calculate column widths
    col_widths = {}
    for col in columns:
        # Start with column name width
        col_widths[col] = len(str(col))
        # Check all values for this column
        for doc in results:
            value = format_value(col, doc.get(col))
            if len(value) > col_widths[col]:
                col_widths[col] = len(value)
        # Minimum width of 4
        col_widths[col] = max(col_widths[col], 4)
    
    # Print top border
    print('+' + '+'.join('-' * (col_widths[col] + 2) for col in columns) + '+')
    
    # Print header
    header_parts = []
    for col in columns:
        header_parts.append(f" {str(col).ljust(col_widths[col])} ")
    print('|' + '|'.join(header_parts) + '|')
    
    # Print separator
    print('+' + '+'.join('-' * (col_widths[col] + 2) for col in columns) + '+')
    
    # Print data rows
    for doc in results:
        row_parts = []
        for col in columns:
            value = format_value(col, doc.get(col))
            if is_numeric_column(col, doc.get(col)):
                # Right-align numeric columns
                row_parts.append(f" {value.rjust(col_widths[col])} ")
            else:
                # Left-align text columns
                row_parts.append(f" {value.ljust(col_widths[col])} ")
        print('|' + '|'.join(row_parts) + '|')
    
    # Print bottom border
    print('+' + '+'.join('-' * (col_widths[col] + 2) for col in columns) + '+')
    
    # Print row count (but not for SHOW operations, execute mode, or silent mode)
    if not is_show_operation and not is_execute_mode and not silent:
        row_count = len(results)
        if row_count == 1:
            print(f"{row_count} row in set ({execution_time:.2f} sec)")
        else:
            print(f"{row_count} rows in set ({execution_time:.2f} sec)")
        print()

def display_mysql_vertical(results, execution_time=0.0, is_execute_mode=False, silent=False):
    """Display results in MySQL/MariaDB vertical format (like \\G)"""
    if not results:
        return
    
    for i, doc in enumerate(results, 1):
        print(f"*************************** {i}. row ***************************")
        
        # Get all unique columns and find max column name width
        columns = list(doc.keys())
        max_col_width = max(len(str(col)) for col in columns) if columns else 0
        
        for col in columns:
            value = doc.get(col)
            if value is None:
                display_value = 'NULL'
            else:
                display_value = str(value)
            print(f"{str(col).rjust(max_col_width)}: {display_value}")
    
    # Print row count for vertical format (but not in execute mode or silent mode)
    if not is_execute_mode and not silent:
        row_count = len(results)
        if row_count == 1:
            print(f"{row_count} row in set ({execution_time:.2f} sec)")
        else:
            print(f"{row_count} rows in set ({execution_time:.2f} sec)")
        print()

if __name__ == '__main__':
    main()
