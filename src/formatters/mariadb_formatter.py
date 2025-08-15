"""
MariaDB-compatible output formatting for MongoSQL

This module provides MariaDB-compatible output formatting for different execution modes:
- Execute mode (-e): Table format for success, query echo + error for failures
- Interactive mode: Table format with timing info
- Piped input mode: Tab-separated format
"""

import sys
from typing import Any, List, Dict, Optional

# Field type mapping for MariaDB precision compatibility
# This helps determine the correct precision for aggregate functions
FIELD_TYPE_MAP = {
    'classicmodels': {
        # decimal(10,2) fields
        'creditLimit': 'decimal',
        'buyPrice': 'decimal', 
        'MSRP': 'decimal',
        'amount': 'decimal',
        'priceEach': 'decimal',
        # int fields  
        'customerNumber': 'int',
        'orderNumber': 'int',
        'quantityInStock': 'int',
        'quantityOrdered': 'int',
        'orderLineNumber': 'int',
        'salesRepEmployeeNumber': 'int',
        'employeeNumber': 'int'
    }
}

def get_field_type(field_name: str, database: str = 'classicmodels') -> str:
    """Get the MariaDB field type for precision formatting"""
    return FIELD_TYPE_MAP.get(database, {}).get(field_name, 'unknown')

def format_value(value: Any, column_name: str = None, database: str = 'classicmodels') -> str:
    """Format a value for display with MariaDB-compatible precision"""
    if value is None:
        return 'NULL'
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, (int, float)):
        # Apply MariaDB-compatible precision for aggregate functions
        if column_name:
            # Extract field name from aggregate function
            field_name = None
            if '(' in column_name and ')' in column_name:
                # Extract field name from AVG(creditLimit), SUM(buyPrice), etc.
                start = column_name.find('(') + 1
                end = column_name.find(')')
                field_name = column_name[start:end]
            
            if field_name:
                field_type = get_field_type(field_name, database)
                
                # AVG functions
                if column_name.upper().startswith('AVG('):
                    if field_type == 'decimal':
                        # decimal fields: 6 decimal places
                        return f"{value:.6f}".rstrip('0').rstrip('.')
                    elif field_type == 'int':
                        # int fields: 4 decimal places  
                        return f"{value:.4f}".rstrip('0').rstrip('.')
                    else:
                        # Default: 6 decimal places
                        return f"{value:.6f}".rstrip('0').rstrip('.')
                
                # SUM functions
                elif column_name.upper().startswith('SUM('):
                    if field_type == 'decimal':
                        # decimal fields: preserve .00 format
                        return f"{value:.2f}"
                    elif field_type == 'int':
                        # int fields: no decimal places
                        return str(int(value))
                    else:
                        # Default behavior
                        return str(value)
                
                # MIN/MAX functions
                elif column_name.upper().startswith(('MIN(', 'MAX(')):
                    if field_type == 'decimal':
                        # decimal fields: preserve .00 format
                        return f"{value:.2f}"
                    elif field_type == 'int':
                        # int fields: no decimal places
                        return str(int(value))
                    else:
                        # Default behavior
                        return str(value)
                
                # Mathematical functions like GREATEST, LEAST
                elif column_name.upper().startswith(('GREATEST(', 'LEAST(')):
                    # For GREATEST/LEAST with integer inputs, return integer format
                    if isinstance(value, float) and value.is_integer():
                        return str(int(value))
                    else:
                        return str(value)
        
        return str(value)
    else:
        return str(value)


class MariaDBFormatter:
    """Handles MariaDB-compatible output formatting"""
    
    def __init__(self):
        self.mode = None
        self.is_execute_mode = False
        self.is_piped_input = False
        self.is_interactive = False
        
    def set_mode(self, is_execute_mode: bool = False, is_piped_input: bool = False, is_interactive: bool = False):
        """Set the output mode"""
        self.is_execute_mode = is_execute_mode
        self.is_piped_input = is_piped_input
        self.is_interactive = is_interactive
        
    def format_success_output(self, result: Any, mql_query: Dict, execution_time: float, 
                            parsed_sql: Optional[Dict] = None, vertical_format: bool = False) -> None:
        """Format successful query output in MariaDB-compatible format"""
        
        # Handle USE database result
        if mql_query.get('operation') == 'use_database' and isinstance(result, str):
            if not self.is_piped_input:
                print(result)
            return
        
        # Handle COUNT results
        if mql_query.get('operation') == 'count' and isinstance(result, int):
            count_result = [{'COUNT(*)': result}]
            self._display_table_data(count_result, parsed_sql, execution_time, vertical_format)
            return
        
        if isinstance(result, list):
            if result:
                # Display as MySQL-style table
                if isinstance(result[0], dict):
                    is_show_operation = mql_query.get('operation', '').startswith('show_')
                    if vertical_format and not is_show_operation:
                        self._display_vertical_format(result, execution_time)
                    else:
                        self._display_table_data(result, parsed_sql, execution_time, vertical_format, is_show_operation)
                else:
                    for item in result:
                        print(item)
            else:
                if not self.is_execute_mode and not self.is_piped_input:
                    print(f"Empty set ({execution_time:.2f} sec)")
                    print()
        else:
            # Handle non-query results (INSERT, UPDATE, DELETE)
            if not self.is_execute_mode:
                self._format_modification_result(result, execution_time)
    
    def format_error_output(self, error_msg: str, sql_query: str = None) -> None:
        """Format error output in MariaDB-compatible format"""
        
        # In execute mode, echo the query before showing error (like MariaDB)
        if self.is_execute_mode and sql_query:
            print("-" * 14)
            print(sql_query)
            print("-" * 14)
            print()
        
        # Format the error message
        if error_msg.startswith("ERROR"):
            # Already formatted as MySQL/MariaDB error - add line number for execute mode
            if self.is_execute_mode and "1046 (3D000)" in error_msg:
                # Add "at line 1" for no database selected error in execute mode
                error_msg = error_msg.replace("No database selected", "No database selected\n")
                error_msg = error_msg.replace(": No database selected\n", " at line 1: No database selected")
            print(error_msg, file=sys.stderr)
        else:
            # Generic error, add ERROR prefix
            print(f"ERROR: {error_msg}", file=sys.stderr)
    
    def _display_table_data(self, results: List[Dict], parsed_sql: Optional[Dict], 
                          execution_time: float, vertical_format: bool = False, 
                          is_show_operation: bool = False) -> None:
        """Display table data in appropriate format based on mode"""
        
        # Determine output format based on mode
        if self.is_piped_input:
            # Tab-separated format for piped input (matches MariaDB behavior)
            self._display_tab_format(results, parsed_sql)
        else:
            # Table format for execute mode and interactive mode
            self._display_mysql_table(results, parsed_sql, execution_time, is_show_operation)
    
    def _display_tab_format(self, results: List[Dict], parsed_sql: Optional[Dict]) -> None:
        """Display results in tab-separated format (for piped output, matches MariaDB)"""
        if not results:
            return
        
        # Get column order
        columns = self._get_column_order(results, parsed_sql)
        
        # Print header (column names)
        print('\t'.join(columns))
        
        # Print data rows
        for doc in results:
            row_values = []
            for col in columns:
                value = doc.get(col, '')
                # Use format_value with column name for proper aggregate precision
                formatted_value = format_value(value, col)
                row_values.append(formatted_value)
            print('\t'.join(row_values))
    
    def _display_mysql_table(self, results: List[Dict], parsed_sql: Optional[Dict], 
                           execution_time: float, is_show_operation: bool = False) -> None:
        """Display results in MySQL/MariaDB table format with borders"""
        if not results:
            return
        
        # Get column order
        columns = self._get_column_order(results, parsed_sql)
        
        if not columns:
            return
        
        # Calculate column widths
        col_widths = {}
        for col in columns:
            col_widths[col] = len(col)  # Start with header width
        
        # Check data widths
        for doc in results:
            for col in columns:
                value = doc.get(col, '')
                formatted_value = format_value(value, col)
                col_widths[col] = max(col_widths[col], len(formatted_value))
        
        # Print table
        self._print_table_border(columns, col_widths)
        self._print_table_header(columns, col_widths)
        self._print_table_border(columns, col_widths)
        
        for doc in results:
            self._print_table_row(doc, columns, col_widths)
        
        self._print_table_border(columns, col_widths)
        
        # Print summary (only in interactive mode, not execute mode)
        if not self.is_execute_mode:
            row_count = len(results)
            row_text = "row" if row_count == 1 else "rows"
            print(f"{row_count} {row_text} in set ({execution_time:.2f} sec)")
            print()
    
    def _get_column_order(self, results: List[Dict], parsed_sql: Optional[Dict]) -> List[str]:
        """Get the proper column order based on the query"""
        query_columns = parsed_sql.get('columns', []) if parsed_sql else []
        
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
                        # Handle qualified column names (table.column -> column)
                        if isinstance(col, str) and '.' in col:
                            col = col.split('.')[-1]
                        columns.append(col_str)
            
            # Only include columns that actually exist in the results
            columns = [col for col in columns if any(col in doc for doc in results)]
        else:
            # Auto-detect columns
            all_columns = set()
            for doc in results:
                for key in doc.keys():
                    if key != '_id':  # Exclude MongoDB's _id
                        all_columns.add(key)
            columns = list(all_columns)
        
        return columns
    
    def _print_table_border(self, columns: List[str], col_widths: Dict[str, int]) -> None:
        """Print table border line"""
        border_parts = []
        for col in columns:
            border_parts.append('+' + '-' * (col_widths[col] + 2))
        border_parts.append('+')
        print(''.join(border_parts))
    
    def _print_table_header(self, columns: List[str], col_widths: Dict[str, int]) -> None:
        """Print table header"""
        header_parts = []
        for col in columns:
            header_parts.append(f"| {col:<{col_widths[col]}} ")
        header_parts.append('|')
        print(''.join(header_parts))
    
    def _print_table_row(self, doc: Dict, columns: List[str], col_widths: Dict[str, int]) -> None:
        """Print a single table row"""
        row_parts = []
        for col in columns:
            value = doc.get(col, '')
            formatted_value = format_value(value, col)
            
            # Right-align numbers, left-align everything else
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                row_parts.append(f"| {formatted_value:>{col_widths[col]}} ")
            else:
                row_parts.append(f"| {formatted_value:<{col_widths[col]}} ")
        row_parts.append('|')
        print(''.join(row_parts))
    
    def _display_vertical_format(self, results: List[Dict], execution_time: float) -> None:
        """Display results in vertical format (\\G)"""
        for i, doc in enumerate(results, 1):
            print(f"*************************** {i}. row ***************************")
            for key, value in doc.items():
                if key != '_id':  # Exclude MongoDB's _id
                    formatted_value = format_value(value, key)
                    print(f"{key}: {formatted_value}")
        
        if not self.is_execute_mode:
            row_count = len(results)
            row_text = "row" if row_count == 1 else "rows"
            print(f"{row_count} {row_text} in set ({execution_time:.2f} sec)")
            print()
    
    def _format_modification_result(self, result: Any, execution_time: float) -> None:
        """Format INSERT/UPDATE/DELETE results"""
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
