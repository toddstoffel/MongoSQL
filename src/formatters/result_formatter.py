"""
Result formatting module for SQL2MQL client
Handles proper column ordering and display formatting to match MariaDB/MySQL output
"""
from typing import List, Dict, Any, Optional
from utils.schema import get_table_columns, format_value, is_numeric_column


class ResultFormatter:
    """Formats query results to match MariaDB/MySQL client output"""
    
    def __init__(self):
        pass
    
    def format_table_results(self, results: List[Dict[str, Any]], 
                           query_columns: Optional[List[str]] = None,
                           table_name: Optional[str] = None) -> None:
        """
        Format and display results in MySQL/MariaDB table format
        
        Args:
            results: List of result documents from MongoDB
            query_columns: Ordered list of columns as specified in SQL query
            table_name: Name of the table being queried (for schema reference)
        """
        if not results:
            return
        
        # Determine column order
        columns = self._determine_column_order(results, query_columns, table_name)
        
        # Calculate column widths
        col_widths = self._calculate_column_widths(results, columns)
        
        # Display the table
        self._print_table(results, columns, col_widths)
    
    def _determine_column_order(self, results: List[Dict[str, Any]], 
                               query_columns: Optional[List[str]] = None,
                               table_name: Optional[str] = None) -> List[str]:
        """
        Determine the proper column order for display
        
        Priority:
        1. Explicit query column order (SELECT col1, col2, ...)
        2. Schema-based ordering for the table
        3. Alphabetical fallback
        """
        # Get all available columns from results
        all_columns = set()
        for doc in results:
            for key in doc.keys():
                if key != '_id':  # Exclude MongoDB's _id
                    all_columns.add(key)
        
        # Priority 1: Use query-specified column order
        if query_columns:
            # Filter to only include columns that exist in results
            ordered_columns = []
            for col in query_columns:
                if col in all_columns:
                    ordered_columns.append(col)
            
            # Add any remaining columns that weren't in the query
            for col in all_columns:
                if col not in ordered_columns:
                    ordered_columns.append(col)
                    
            return ordered_columns
        
        # Priority 2: Use schema-based ordering
        if table_name:
            schema_cols = get_table_columns(table_name)
            if schema_cols:
                ordered_columns = []
                # Add columns in schema order
                for col in schema_cols:
                    if col in all_columns:
                        ordered_columns.append(col)
                
                # Add any remaining columns not in schema
                for col in all_columns:
                    if col not in ordered_columns:
                        ordered_columns.append(col)
                        
                return ordered_columns
        
        # Priority 3: Alphabetical fallback
        return sorted(all_columns)
    
    def _calculate_column_widths(self, results: List[Dict[str, Any]], 
                                columns: List[str]) -> Dict[str, int]:
        """Calculate the width needed for each column"""
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
        
        return col_widths
    
    def _print_table(self, results: List[Dict[str, Any]], 
                    columns: List[str], col_widths: Dict[str, int]) -> None:
        """Print the formatted table"""
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


def format_count_result(count: int) -> None:
    """Format and display COUNT() result"""
    print('+----------+')
    print('| COUNT(*) |')
    print('+----------+')
    print(f'| {str(count).rjust(8)} |')
    print('+----------+')


def format_vertical_result(results: List[Dict[str, Any]], 
                          query_columns: Optional[List[str]] = None) -> None:
    """Format results in vertical format (like \\G in MySQL)"""
    if not results:
        return
    
    formatter = ResultFormatter()
    
    for i, doc in enumerate(results, 1):
        print(f"*************************** {i}. row ***************************")
        
        # Determine column order
        columns = formatter._determine_column_order([doc], query_columns)
        
        # Print each column
        for col in columns:
            if col != '_id':  # Skip MongoDB's internal ID
                value = format_value(col, doc.get(col))
                print(f"{col}: {value}")
        
        if i < len(results):
            print()
