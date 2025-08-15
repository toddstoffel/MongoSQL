# JOIN Module Architecture

The `src/joins/` module provides comprehensive support for SQL JOIN operations translated to MongoDB aggregation pipelines.

## Module Structure

```
src/joins/
├── __init__.py           # Module exports
├── join_types.py         # JOIN type definitions and handlers
├── join_parser.py        # Parse JOIN syntax from SQL
├── join_translator.py    # Translate JOINs to MongoDB aggregation
└── join_optimizer.py     # Optimize JOIN operations for MongoDB
```

## Supported JOIN Types

### ✅ Implemented
- **INNER JOIN** - Returns only matching records from both tables
- **LEFT JOIN** (LEFT OUTER JOIN) - Returns all records from left table, matching from right
- **CROSS JOIN** - Cartesian product of both tables

### 🚧 Planned
- **RIGHT JOIN** (RIGHT OUTER JOIN) - Returns all records from right table, matching from left
- **FULL OUTER JOIN** - Returns all records from both tables

## Architecture Overview

### 1. Join Types (`join_types.py`)
- **JoinType Enum**: Defines supported JOIN types
- **JoinCondition**: Represents individual JOIN conditions (table.col = table.col)
- **JoinOperation**: Complete JOIN operation with type, tables, and conditions
- **Handler Classes**: Type-specific MongoDB translation logic
  - `InnerJoinHandler`: $lookup + $match for non-empty arrays
  - `LeftJoinHandler`: $lookup + $unwind with preserveNullAndEmptyArrays
  - `CrossJoinHandler`: $lookup with empty pipeline

### 2. Join Parser (`join_parser.py`)
- **JoinParser Class**: Extracts JOIN information from SQL
- **Methods**:
  - `parse_joins_from_sql()`: Extract all JOINs from SQL statement
  - `_determine_join_type()`: Identify JOIN type from syntax
  - `_extract_table_info()`: Get table names and aliases
  - `_extract_join_conditions()`: Parse ON clause conditions

### 3. Join Translator (`join_translator.py`)
- **JoinTranslator Class**: Converts JOINs to MongoDB aggregation
- **Methods**:
  - `translate_joins_to_pipeline()`: Build aggregation pipeline stages
  - `create_projection_with_joins()`: Handle column selection across tables
  - `translate_join_query()`: Complete query translation

### 4. Join Optimizer (`join_optimizer.py`)
- **JoinOptimizer Class**: Performance optimization for JOIN operations
- **Methods**:
  - `optimize_join_order()`: Reorder JOINs for better performance
  - `add_early_filtering()`: Move WHERE conditions before JOINs when possible
  - `suggest_indexes()`: Recommend indexes for JOIN performance
  - `optimize_aggregation_pipeline()`: Pipeline-level optimizations

## MongoDB Translation Strategy

### INNER JOIN Example
```sql
SELECT * FROM orders o INNER JOIN customers c ON o.customer_id = c.customer_id
```

Translates to:
```javascript
db.orders.aggregate([
  {
    $lookup: {
      from: "customers",
      localField: "customer_id", 
      foreignField: "customer_id",
      as: "customers_joined"
    }
  },
  {
    $match: {
      "customers_joined": { $ne: [] }
    }
  },
  {
    $unwind: "$customers_joined"
  },
  {
    $project: {
      _id: 0,
      // ... field mappings
    }
  }
])
```

### LEFT JOIN Example
```sql
SELECT * FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id
```

Translates to:
```javascript
db.customers.aggregate([
  {
    $lookup: {
      from: "orders",
      localField: "customer_id",
      foreignField: "customer_id", 
      as: "orders_joined"
    }
  },
  {
    $unwind: {
      path: "$orders_joined",
      preserveNullAndEmptyArrays: true
    }
  },
  {
    $project: {
      _id: 0,
      // ... field mappings
    }
  }
])
```

## Integration Points

### Parser Integration
The JOIN parser updates the existing SQL parser by populating the `joins` field:
```python
# In sql_parser.py
from joins.join_parser import JoinParser

parser = JoinParser()
parsed_sql = parser.update_parsed_sql_with_joins(parsed_sql, sql)
```

### Translator Integration  
The main translator checks for JOINs and uses aggregation instead of find():
```python
# In sql_to_mql.py
from joins.join_translator import JoinTranslator

if parsed_sql.get('joins'):
    join_translator = JoinTranslator()
    return join_translator.translate_join_query(parsed_sql)
```

### CLI Integration
The CLI can provide JOIN-specific feedback and optimization suggestions:
```python
# In main.py
from joins.join_optimizer import JoinOptimizer

optimizer = JoinOptimizer()
suggestions = optimizer.suggest_indexes(joins, base_collection)
```

## Performance Considerations

### Index Recommendations
- **Local Field Indexes**: Index JOIN keys on the "left" collection
- **Foreign Field Indexes**: Index JOIN keys on the "right" collection  
- **Compound Indexes**: For multi-column JOIN conditions

### Optimization Strategies
1. **Early Filtering**: Move WHERE conditions before JOINs when possible
2. **JOIN Ordering**: Place INNER JOINs before LEFT JOINs to reduce dataset size
3. **Pipeline Combining**: Merge consecutive $match stages
4. **Result Size Estimation**: Warn about potentially expensive operations

## Usage Examples

### Basic INNER JOIN
```python
from joins import JoinParser, JoinTranslator

sql = "SELECT c.name, o.total FROM customers c INNER JOIN orders o ON c.id = o.customer_id"
parser = JoinParser()
translator = JoinTranslator()

joins = parser.parse_joins_from_sql(sql)
pipeline = translator.translate_joins_to_pipeline(joins, "customers")
```

### Optimized JOIN Query
```python
from joins import JoinOptimizer

optimizer = JoinOptimizer()
optimized_joins = optimizer.optimize_join_order(joins)
optimized_pipeline = optimizer.optimize_aggregation_pipeline(pipeline)
```

This modular architecture allows for:
- **Easy Extension**: New JOIN types can be added by creating new handlers
- **Performance Tuning**: Optimization strategies can be enhanced independently  
- **Testing**: Each component can be unit tested in isolation
- **Maintenance**: Clear separation of concerns makes debugging easier
