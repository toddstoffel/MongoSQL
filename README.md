# SQL2MQL - SQL to MongoDB Query Language Translator

A command-line client that translates MariaDB/MySQL syntax to MongoDB Query Language (MQL) and executes queries against MongoDB databases.

## Features

- Interactive CLI similar to MySQL client
- Translates SQL SELECT, INSERT, UPDATE, DELETE statements to MongoDB operations
- Maps MariaDB/MySQL functions to MongoDB equivalents
- Connects to MongoDB using PyMongo
- Rich terminal output with syntax highlighting
- Batch mode support
- Environment-based configuration

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Translator
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

## Usage

### Interactive Mode (Default)

```bash
python sql2mql.py
```

Or with connection parameters:

```bash
python sql2mql.py --host localhost --port 27017 --database mydb --username myuser -p
```

### Execute Single Statement

```bash
python sql2mql.py -e "SELECT * FROM users WHERE age > 25"
```

### Batch Mode

```bash
cat queries.sql | python sql2mql.py --batch
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

The translator supports a comprehensive mapping of MariaDB/MySQL functions to MongoDB equivalents:

### String Functions
- `CONCAT()` → `$concat`
- `SUBSTRING()` → `$substr`
- `LENGTH()` → `$strLenCP`
- `UPPER()` → `$toUpper`
- `LOWER()` → `$toLower`
- `TRIM()`, `LTRIM()`, `RTRIM()` → `$trim`, `$ltrim`, `$rtrim`
- `REPLACE()` → `$replaceAll`

### Numeric Functions
- `ABS()` → `$abs`
- `CEIL()`, `FLOOR()` → `$ceil`, `$floor`
- `ROUND()` → `$round`
- `POWER()`, `SQRT()` → `$pow`, `$sqrt`
- `MOD()` → `$mod`
- Trigonometric functions: `SIN()`, `COS()`, `TAN()`, etc.

### Date/Time Functions
- `NOW()` → `$$NOW`
- `YEAR()`, `MONTH()`, `DAY()` → `$year`, `$month`, `$dayOfMonth`
- `DATE_ADD()`, `DATE_SUB()` → `$dateAdd`, `$dateSubtract`
- `DATE_FORMAT()` → `$dateToString`

### Aggregate Functions
- `COUNT()` → `$sum`
- `SUM()`, `AVG()`, `MIN()`, `MAX()` → `$sum`, `$avg`, `$min`, `$max`

### Conditional Functions
- `IF()` → `$cond`
- `IFNULL()` → `$ifNull`
- `COALESCE()` → `$ifNull`

## CLI Commands

Inside the interactive shell:

- `help` - Show available commands
- `show collections` - List all collections in current database
- `use <database>` - Switch to different database
- `quit` or `exit` - Exit the client

## Configuration

Environment variables (`.env` file):

```
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=mydb
MONGODB_USERNAME=myuser
MONGODB_PASSWORD=mypassword
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
│   └── mongodb_client.py    # MongoDB connection and query execution
├── parsers/
│   └── sql_parser.py        # SQL statement parsing
├── translators/
│   └── sql_to_mql.py        # SQL to MQL translation logic
├── mappers/
│   └── function_mapper.py   # Function mapping (MariaDB → MongoDB)
└── utils/
    └── helpers.py           # Utility functions
```

## Error Handling

The translator provides helpful error messages for:
- Connection issues
- Invalid SQL syntax
- Unsupported operations
- MongoDB operation failures

## Limitations

- Complex JOINs are not supported (MongoDB is document-based)
- Some advanced SQL features may require manual translation
- Subqueries support is limited
- Transaction support follows MongoDB's transaction model

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

[Add your license information here]
