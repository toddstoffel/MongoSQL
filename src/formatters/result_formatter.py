"""
Result formatting module for MongoSQL client
Handles database-agnostic column ordering and display formatting
"""
from typing import List, Dict, Any, Optional


class ResultFormatter:
    """Formats query results in a database-agnostic way"""

    def __init__(self):
        pass

    def format_value(self, column_name, value):
        """Generic value formatting without hardcoded schemas"""
        if value is None:
            return ''

        # Apply MariaDB-compatible precision for statistical functions
        if isinstance(value, (int, float)) and ('STDDEV' in column_name.upper() or 'VAR_' in column_name.upper()):
            # Round to 6 decimal places to match MariaDB precision
            try:
                formatted = f"{float(value):.6f}".rstrip('0').rstrip('.')
                return formatted
            except:
                pass

        # Format numeric values consistently
        if isinstance(value, float):
            # For monetary values, use 2 decimal places if they look like money
            if any(keyword in column_name.lower() for keyword in ['price', 'cost', 'amount', 'credit', 'limit']):
                return f"{value:.2f}"
            # For other floats, remove unnecessary decimals
            if value == int(value):
                return str(int(value))
            return str(value)

        return str(value)

    def is_numeric_column(self, column_name, value=None):
        """Check if a column should be right-aligned (numeric) - generic detection"""
        # Check if the value itself is numeric
        if value is not None:
            try:
                if isinstance(value, (int, float)):
                    return True
                elif isinstance(value, str):
                    # Check if string represents a number
                    if value.replace('.', '').replace('-', '').isdigit():
                        return True
                    try:
                        float(value)
                        return True
                    except ValueError:
                        pass
            except:
                pass

        # Check column name patterns that suggest numeric data
        numeric_patterns = ['number', 'id', 'code', 'quantity', 'price', 'amount', 'limit', 'count']
        column_lower = column_name.lower()
        return any(pattern in column_lower for pattern in numeric_patterns)

    def format_table_results(self, results: List[Dict[str, Any]],
                           query_columns: Optional[List[str]] = None,
                           table_name: Optional[str] = None) -> None:
        """
        Format and display results in a database-agnostic table format

        Args:
            results: List of result documents from MongoDB
            query_columns: Explicitly selected columns from query (for ordering)
            table_name: Name of the table (no longer used for hardcoded schemas)

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

        # Priority 2: Use natural ordering - ID fields first, then alphabetical
        ordered_columns = list(all_columns)

        # Simple heuristic ordering without hardcoded schemas
        id_columns = [col for col in ordered_columns if col.lower().endswith('number') or col.lower().endswith('id') or col.lower() == 'id']
        name_columns = [col for col in ordered_columns if 'name' in col.lower()]
        other_columns = [col for col in ordered_columns if col not in id_columns and col not in name_columns]

        # Order: ID columns first, then name columns, then others alphabetically
        ordered_columns = sorted(id_columns) + sorted(name_columns) + sorted(other_columns)

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
                value = self.format_value(col, doc.get(col))
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
                value = self.format_value(col, doc.get(col))
                if self.is_numeric_column(col, doc.get(col)):
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
                value = formatter.format_value(col, doc.get(col))
                print(f"{col}: {value}")

        if i < len(results):
            print()
