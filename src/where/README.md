# WHERE Clause Module

This module handles parsing and translation of SQL WHERE clauses to MongoDB match filters.

## Components

### where_parser.py
- Token-based parsing of WHERE clauses
- Handles complex conditions with AND/OR operators
- Supports comparison operators, LIKE patterns, IN clauses, NULL checks

### where_translator.py
- Translates parsed WHERE conditions to MongoDB match filters
- Converts SQL operators to MongoDB query operators
- Handles SQL LIKE patterns to MongoDB regex conversion

### where_types.py
- Type definitions for WHERE clause structures
- Defines WhereCondition, CompoundWhereCondition, and WhereClause
- Enumerates WhereOperator and LogicalOperator types

## Usage

```python
from src.where import WhereParser, WhereTranslator

parser = WhereParser()
translator = WhereTranslator()

# Parse WHERE clause
where_clause = parser.parse_where(tokens)

# Translate to MongoDB
mongo_filter = translator.translate_where(where_clause)
```

## Supported Operations

- Comparison operators: `=`, `!=`, `<`, `<=`, `>`, `>=`
- Pattern matching: `LIKE`, `NOT LIKE`
- Set membership: `IN`, `NOT IN`
- Null checks: `IS NULL`, `IS NOT NULL`
- Range queries: `BETWEEN`, `NOT BETWEEN`
- Logical operators: `AND`, `OR`, `NOT`
