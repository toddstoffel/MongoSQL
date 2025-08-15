"""
Database schema definitions for maintaining proper column order and formatting
"""

# Define table schemas with proper column order matching MariaDB/MySQL
TABLE_SCHEMAS = {
    'customers': [
        'customerNumber',
        'customerName', 
        'contactLastName',
        'contactFirstName',
        'phone',
        'addressLine1',
        'addressLine2', 
        'city',
        'state',
        'postalCode',
        'country',
        'salesRepEmployeeNumber',
        'creditLimit'
    ],
    'products': [
        'productCode',
        'productName',
        'productLine', 
        'productScale',
        'productVendor',
        'productDescription',
        'quantityInStock',
        'buyPrice',
        'MSRP'
    ],
    'orders': [
        'orderNumber',
        'orderDate',
        'requiredDate',
        'shippedDate',
        'status',
        'comments',
        'customerNumber'
    ],
    'orderdetails': [
        'orderNumber',
        'productCode',
        'quantityOrdered',
        'priceEach',
        'orderLineNumber'
    ],
    'payments': [
        'customerNumber',
        'checkNumber',
        'paymentDate',
        'amount'
    ],
    'employees': [
        'employeeNumber',
        'lastName',
        'firstName',
        'extension',
        'email',
        'officeCode',
        'reportsTo',
        'jobTitle'
    ],
    'offices': [
        'officeCode',
        'city',
        'phone',
        'addressLine1',
        'addressLine2',
        'state',
        'country',
        'postalCode',
        'territory'
    ],
    'productlines': [
        'productLine',
        'textDescription',
        'htmlDescription',
        'image'
    ]
}

# Data type formatting rules
DATA_TYPE_FORMATTERS = {
    'creditLimit': lambda x: f"{float(x):.2f}" if x is not None else 'NULL',
    'buyPrice': lambda x: f"{float(x):.2f}" if x is not None else 'NULL', 
    'MSRP': lambda x: f"{float(x):.2f}" if x is not None else 'NULL',
    'priceEach': lambda x: f"{float(x):.2f}" if x is not None else 'NULL',
    'amount': lambda x: f"{float(x):.2f}" if x is not None else 'NULL',
}

# Numeric columns that should be right-aligned
NUMERIC_COLUMNS = {
    'customerNumber', 'salesRepEmployeeNumber', 'creditLimit',
    'productCode', 'quantityInStock', 'buyPrice', 'MSRP',
    'orderNumber', 'quantityOrdered', 'priceEach', 'orderLineNumber',
    'employeeNumber', 'reportsTo', 'amount'
}

def get_table_columns(table_name):
    """Get the proper column order for a table"""
    return TABLE_SCHEMAS.get(table_name, [])

def format_value(column_name, value):
    """Format a value according to its data type"""
    if value is None:
        return ''
    
    # Apply specific formatters
    if column_name in DATA_TYPE_FORMATTERS:
        return DATA_TYPE_FORMATTERS[column_name](value)
    
    return str(value)

def is_numeric_column(column_name, value=None):
    """Check if a column should be right-aligned (numeric)"""
    # Check if it's a predefined numeric column
    if column_name in NUMERIC_COLUMNS:
        return True
    
    # If we have a value, check if it's numeric
    if value is not None:
        try:
            # Try to convert to number
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
    
    return False
