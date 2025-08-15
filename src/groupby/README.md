# GROUP BY Module

Modular implementation of GROUP BY functionality for SQL to MongoDB translation.

## Architecture

The GROUP BY module follows the same modular pattern as ORDER BY and JOINs:

### Components

- **groupby_types.py** - Type definitions and data structures
- **groupby_parser.py** - Parsing GROUP BY clauses from SQL tokens  
- **groupby_translator.py** - Translation to MongoDB aggregation pipelines

### Types

- **GroupByField** - Represents a single GROUP BY field
- **AggregateFunction** - Represents aggregate functions (COUNT, SUM, etc.)
- **GroupByStructure** - Complete GROUP BY operation structure

## Usage

```python
from src.groupby import GroupByParser, GroupByTranslator

parser = GroupByParser()
translator = GroupByTranslator()

# Parse GROUP BY structure from parsed SQL
group_by_structure = parser.parse_group_by_structure(parsed_sql)

# Translate to MongoDB aggregation pipeline
mql_query = translator.translate(group_by_structure, parsed_sql)
```

## Supported Features

- Single and multiple field grouping
- Aggregate functions: COUNT, SUM, AVG, MIN, MAX
- HAVING clause support
- Integration with ORDER BY and LIMIT
- Proper alias handling for aggregate functions

## MongoDB Translation

GROUP BY operations are translated to MongoDB aggregation pipelines:

```sql
SELECT country, COUNT(*) as customer_count 
FROM customers 
GROUP BY country 
HAVING COUNT(*) > 5
ORDER BY country
```

Becomes:

```javascript
[
  { "$group": { 
      "_id": "$country", 
      "customer_count": { "$sum": 1 },
      "country": { "$first": "$country" }
  }},
  { "$match": { "customer_count": { "$gt": 5 } }},
  { "$sort": { "country": 1 }}
]
```
