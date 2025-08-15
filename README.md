# MongoSQL - SQL to MongoDB Query Language Translator

A command-line client that translates MariaDB/MySQL syntax to MongoDB Query Language (MQL) and executes queries against MongoDB databases with **85.1% compatibility** across comprehensive test suites.

## Features

- Interactive CLI similar to MySQL client
- Translates SQL SELECT, INSERT, UPDATE, DELETE statements to MongoDB operations
- **Comprehensive function mapping** - 47+ MariaDB/MySQL functions supported
- **Advanced JOIN support** - INNER, LEFT, RIGHT, and multi-table JOINs
- **Complete ORDER BY functionality** with proper collation matching
- **Full DISTINCT operations** support
- Connects to MongoDB using PyMongo with connection pooling
- **Collation-aware sorting** to match MariaDB's `utf8mb4_unicode_ci` behavior
- Rich terminal output with MariaDB-compatible formatting
- Batch mode support
- Environment-based configuration
- **Modular architecture** with dedicated modules for JOINs, ORDER BY, and functions

## Compatibility Status

**Current Test Results (85.1% success rate):**
- ✅ **DATETIME functions**: 22/22 (100.0%) - Complete date/time function support
- ✅ **STRING functions**: 10/10 (100.0%) - Full string manipulation support  
- ✅ **MATH functions**: 10/10 (100.0%) - Complete mathematical operations
- ✅ **AGGREGATE functions**: 5/5 (100.0%) - All aggregate functions working
- ✅ **JOINS**: 4/4 (100.0%) - Complete JOIN functionality
- ✅ **ORDER BY**: 3/3 (100.0%) - Full sorting with proper collation
- ✅ **DISTINCT**: 3/3 (100.0%) - All DISTINCT operations supported
- 🔄 **GROUP BY**: 0/3 (0.0%) - Planned for future development
- 🔄 **CONDITIONAL**: 0/4 (0.0%) - IF, CASE, COALESCE functions in development
- 🔄 **SUBQUERIES**: 0/3 (0.0%) - Complex subquery support planned

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd MongoSQL
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure MongoDB connection:
```bash
cp .env.example .env
# Edit .env with your MongoDB connection details
```

## Important: Collation Compatibility

**Critical Discovery**: For accurate comparison between MariaDB and MongoDB results, both systems must use compatible collation rules:

- **MariaDB**: Uses `utf8mb4_unicode_ci` (case-insensitive, Unicode-aware)
- **MongoDB**: Configured with equivalent collation settings:
  ```javascript
  {
    locale: 'en',
    caseLevel: false,     // Case-insensitive like MariaDB
    strength: 1,          // Primary level only (ignore case/accents)
    numericOrdering: false
  }
  ```

This ensures ORDER BY and comparison operations return identical results between both database systems.

## Usage

### Interactive Mode (Default)

```bash
python mongosql.py
```

Or with connection parameters:

```bash
python mongosql.py --host localhost --port 27017 --database mydb --username myuser -p
```

### Execute Single Statement

```bash
python -m src.cli.main classicmodels -e "SELECT * FROM users WHERE age > 25"
```

### Batch Mode

```bash
cat queries.sql | python -m src.cli.main classicmodels --batch
```

## Advanced Features

### JOIN Support
```sql
-- INNER JOIN
SELECT c.customerName, o.orderDate 
FROM customers c 
INNER JOIN orders o ON c.customerNumber = o.customerNumber;

-- LEFT JOIN with multiple tables
SELECT c.customerName, o.orderDate, od.quantityOrdered
FROM customers c
LEFT JOIN orders o ON c.customerNumber = o.customerNumber
LEFT JOIN orderdetails od ON o.orderNumber = od.orderNumber;
```

### ORDER BY with Collation
```sql
-- Case-insensitive sorting matching MariaDB behavior
SELECT customerName FROM customers ORDER BY customerName ASC LIMIT 10;
-- Returns: Alpha Cognac, American Souvenirs Inc, Amica Models & Co., ANG Resellers...
```

### DISTINCT Operations
```sql
-- Single and multi-column DISTINCT
SELECT DISTINCT country FROM customers;
SELECT DISTINCT city, country FROM customers;
```

## SQL to MQL Translation Examples

### SELECT Statements

```sql
-- SQL
SELECT name, age FROM users WHERE age > 25 ORDER BY name LIMIT 10;

-- Translates to MongoDB
db.users.find({"age": {"$gt": 25}}, {"name": 1, "age": 1}).sort({"name": 1}).limit(10)
```

### INSERT Statements

```sql
-- SQL
INSERT INTO users (name, age, email) VALUES ('John', 30, 'john@example.com');

-- Translates to MongoDB
db.users.insertOne({"name": "John", "age": 30, "email": "john@example.com"})
```

### UPDATE Statements

```sql
-- SQL
UPDATE users SET age = 31 WHERE name = 'John';

-- Translates to MongoDB
db.users.updateMany({"name": "John"}, {"$set": {"age": 31}})
```

### DELETE Statements

```sql
-- SQL
DELETE FROM users WHERE age < 18;

-- Translates to MongoDB
db.users.deleteMany({"age": {"$lt": 18}})
```

## Supported SQL Functions

The translator supports **47+ MariaDB/MySQL functions** with comprehensive mapping to MongoDB equivalents:

### String Functions (10/10 - 100% supported)
- `CONCAT()` → `$concat`
- `SUBSTRING()` → `$substr` 
- `LENGTH()` → `$strLenCP`
- `UPPER()`, `LOWER()` → `$toUpper`, `$toLower`
- `TRIM()`, `LTRIM()`, `RTRIM()` → `$trim`, `$ltrim`, `$rtrim`
- `REPLACE()` → `$replaceAll`
- `LEFT()`, `RIGHT()` → `$substr` variations
- `REVERSE()` → Custom implementation

### Mathematical Functions (10/10 - 100% supported)
- `ABS()` → `$abs`
- `CEIL()`, `FLOOR()` → `$ceil`, `$floor`
- `ROUND()` → `$round`
- `POWER()`, `SQRT()` → `$pow`, `$sqrt`
- `SIN()`, `COS()` → `$sin`, `$cos`
- `LOG()` → `$ln`
- `GREATEST()` → `$max`

### Date/Time Functions (22/22 - 100% supported)
- `NOW()`, `CURDATE()`, `CURTIME()` → `$$NOW` and variants
- `YEAR()`, `MONTH()`, `DAY()` → `$year`, `$month`, `$dayOfMonth`
- `HOUR()`, `MINUTE()`, `SECOND()` → `$hour`, `$minute`, `$second`
- `DATE_FORMAT()` → `$dateToString`
- `MAKEDATE()`, `MAKETIME()` → Custom implementations
- `TIMESTAMPADD()`, `ADDTIME()`, `SUBTIME()` → Date arithmetic
- `EXTRACT()`, `TO_DAYS()` → Temporal extractions

### Aggregate Functions (5/5 - 100% supported)
- `COUNT()` → `$sum: 1`
- `SUM()`, `AVG()`, `MIN()`, `MAX()` → `$sum`, `$avg`, `$min`, `$max`

### Advanced Operations (100% supported)
- **JOINs**: INNER, LEFT, RIGHT, multi-table joins
- **ORDER BY**: Single and multi-field sorting with proper collation
- **DISTINCT**: Single and multi-column distinct operations
- **LIMIT/OFFSET**: Result pagination

## CLI Commands

Inside the interactive shell:

- `help` - Show available commands
- `show collections` - List all collections in current database
- `use <database>` - Switch to different database
- `quit` or `exit` - Exit the client

## Configuration

Environment variables (`.env` file):

```env
# MongoDB Configuration
MONGO_HOST=cluster0.7gb72xv.mongodb.net
MONGO_USERNAME=username
MONGO_PASSWORD=password
MONGO_AUTH_DATABASE=admin
MONGO_DATABASE=classicmodels
MONGO_PORT=27017

# MongoDB Connection Options  
MONGO_RETRY_WRITES=true
MONGO_WRITE_CONCERN=majority
MONGO_APP_NAME=MongoSQL
MONGODB_TIMEOUT=5000
MONGODB_SSL=false

# MariaDB Configuration (for QA comparison testing)
MARIADB_HOST=your-mariadb-host
MARIADB_USERNAME=username
MARIADB_PASSWORD=password
MARIADB_DATABASE=classicmodels
```

## Command Line Options

- `--host` - MongoDB host (default: localhost)
- `--port` - MongoDB port (default: 27017)
- `--database`, `-d` - Database name
- `--username`, `-u` - Username for authentication
- `--password`, `-p` - Prompt for password
- `--execute`, `-e` - Execute statement and exit
- `--batch` - Run in batch mode (non-interactive)

## Project Structure

```
src/
├── cli/
│   └── main.py              # CLI interface and main entry point
├── database/
│   └── mongodb_client.py    # MongoDB connection with collation support
├── parsers/
│   ├── token_sql_parser.py  # Advanced SQL statement parsing
│   └── where_parser.py      # WHERE clause parsing
├── translators/
│   ├── sql_to_mql.py        # Main SQL to MQL translation logic
│   └── where_translator.py  # WHERE clause translation
├── mappers/
│   ├── function_mapper.py   # Function mapping coordination
│   ├── string_functions.py  # String function mappings
│   ├── math_functions.py    # Mathematical function mappings
│   ├── datetime_functions.py # Date/time function mappings
│   └── aggregate_functions.py # Aggregate function mappings
├── joins/
│   ├── join_parser.py       # JOIN clause parsing
│   ├── join_translator.py   # JOIN translation to aggregation
│   ├── join_optimizer.py    # JOIN query optimization
│   └── join_types.py        # JOIN type definitions
├── orderby/
│   ├── orderby_parser.py    # ORDER BY clause parsing
│   ├── orderby_translator.py # ORDER BY to $sort translation
│   └── orderby_types.py     # ORDER BY type definitions
├── formatters/
│   ├── result_formatter.py  # Generic result formatting
│   └── mariadb_formatter.py # MariaDB-compatible output
└── utils/
    ├── helpers.py           # Utility functions
    └── schema.py            # Database schema utilities

QA/
└── mariadb_comparison_qa.py # Comprehensive test suite (67 tests)

KB/
├── MONGODB_FUNCTION_MAPPING.md # Complete function mapping reference
├── MISSING_FUNCTIONS.md        # Planned function implementations
└── mariadb.md                  # MariaDB compatibility notes
```

## Error Handling

The translator provides helpful error messages for:
- Connection issues
- Invalid SQL syntax
- Unsupported operations
- MongoDB operation failures

## Limitations and Roadmap

### Currently Working (85.1% compatibility)
- ✅ All basic SQL operations (SELECT, INSERT, UPDATE, DELETE)
- ✅ Comprehensive function library (47+ functions)
- ✅ Complete JOIN support (INNER, LEFT, RIGHT, multi-table)
- ✅ Full ORDER BY with proper collation matching
- ✅ All DISTINCT operations
- ✅ All aggregate functions

### In Development
- 🔄 **GROUP BY operations** - Planned for next release
- 🔄 **Conditional functions** (IF, CASE, COALESCE) - Function mapping needed
- 🔄 **Complex subqueries** - Advanced query nesting support

### MongoDB-Specific Considerations
- **Document-based nature**: Complex JOINs are converted to aggregation pipelines
- **Collation importance**: Proper collation configuration required for sorting compatibility
- **Schema flexibility**: MongoDB's schemaless nature handled gracefully
- **Performance optimization**: Queries optimized for MongoDB's execution model

### Known Differences
- **Collation**: Requires explicit configuration for MariaDB compatibility
- **NULL handling**: MongoDB's null semantics may differ slightly from SQL
- **Data types**: Automatic type conversion between SQL and BSON types

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

[Add your license information here]
