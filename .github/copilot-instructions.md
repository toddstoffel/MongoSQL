# Copilot Development Reminders

## CRITICAL - READ FIRST EVERY TIME

### 0. KNOWLEDGE BASE INITIALIZATION
- **ALWAYS** start each session by reviewing `KB/REFERENCE_LINKS.md` for up-to-date documentation links
- **REFRESH** memory with MariaDB, MongoDB, and SQL parsing resources from the knowledge base
- **CHECK** reserved words documentation at: https://mariadb.com/docs/server/reference/sql-structure/sql-language-structure/reserved-words
- **REFERENCE** MongoDB operators at: https://docs.mongodb.com/manual/reference/operator/aggregation/
- **USE** the `src/reserved_words/` module for proper identifier handling and escaping
- **CONSULT** KB files for function mappings, compatibility matrices, and implementation patterns

### 0.5. TRANSLATION-ONLY ARCHITECTURE - CRITICAL
- **NO QUERY PROCESSING** in Python client - this is ONLY a translation service
- **ALL DATA PROCESSING** must occur in MongoDB using aggregation pipelines, queries, and operators
- **TRANSLATE TO MONGODB OPERATIONS** - convert SQL to MongoDB queries that MongoDB executes
- **NEVER** execute subqueries, functions, or data processing in Python
- **EXAMPLE**: Subqueries → `$lookup` stages, Functions → `$expr` operations, JOINs → `$lookup` pipelines
- **SUCCESS EXAMPLE**: DERIVED subqueries → complex `$lookup` with `$group` subpipelines + `$unwind` + `$project`
- The client translates SQL syntax to MongoDB syntax - MongoDB does all the work

### 1. NO REGEX PARSING - USE TOKENS ONLY
- **NEVER** use regex (`import re`, `re.match`, `re.search`, etc.) for SQL parsing
- **ALWAYS** use sqlparse tokens for all SQL parsing operations
- Token-based parsing is more reliable, handles edge cases, and follows project architecture
- If you see regex in existing code, replace it with token-based parsing

### 2. TESTING PROTOCOL - CRITICAL
- **ALWAYS** test functionality through the `./mongosql` CLI tool
- **NEVER** test submodules directly (parser, translator, etc.) - this defeats the project purpose
- **USE** `./mongosql database -e "SQL_QUERY"` for all testing and validation
- **EXAMPLE**: `./mongosql classicmodels -e "SELECT * FROM customers LIMIT 5"`
- The CLI provides the complete integration testing that validates the entire pipeline
- Direct submodule testing can hide integration issues and doesn't reflect real usage

### 3. ENVIRONMENT & CONNECTION SETUP
- **ALWAYS** check and use the `.env` file for MongoDB connection settings
- **NEVER** use hardcoded localhost values
- Load environment variables with `load_dotenv()` before connecting
- Check `.env` file contents before making any MongoDB connections
- Use `MongoDBClient(host=os.getenv('MONGO_HOST'), username=os.getenv('MONGO_USERNAME'), password=os.getenv('MONGO_PASSWORD'), database='classicmodels')`
- Check if MongoDB is running if connection fails

### 4. FILE EDITING BEST PRACTICES
- **ALWAYS** include 3-5 lines of context before and after when using `replace_string_in_file`
- Read the file first to understand the exact context
- Never use placeholder comments like `...existing code...`
- Match whitespace and indentation exactly

### 5. DEBUGGING WORKFLOW
1. Check `KB/REFERENCE_LINKS.md` for latest documentation links
2. Review `src/reserved_words/` module for identifier handling
3. Check `.env` file exists and has correct MongoDB settings
4. Load environment variables with `load_dotenv()`
5. Verify MongoDB connection works
6. **Test through `./mongosql` CLI only - complete integration testing**
7. Use token-based parsing only (NO REGEX)
8. Check actual error messages, don't assume

### 6. COMMON MISTAKES TO AVOID
- ❌ Using regex for SQL parsing (use sqlparse tokens instead)
- ❌ Using localhost hardcoded values
- ❌ Not loading .env file
- ❌ Not including enough context in file edits
- ❌ Assuming MongoDB is running without checking
- ❌ Not reading the full error message carefully
- ❌ **TESTING SUBMODULES DIRECTLY INSTEAD OF USING `./mongosql` CLI**

### 7. QA TESTING GUIDELINES - CRITICAL
- **ONLY** test SQL queries that execute successfully in MariaDB
- **NEVER** add test cases that fail in MariaDB - we test functionality, not error message comparison
- **VALIDATE** all test queries against MariaDB before adding to QA suite
- **EXAMPLE OF INVALID TEST**: `SELECT ... WHERE col IN (SELECT ... LIMIT 3)` - MariaDB error 1235
- **FOCUS** on comparing successful results between MariaDB and our translator
- **USE** `python QA/mariadb_comparison_qa.py --category <category>` for targeted testing (case insensitive)
- QA testing should prove our translator produces equivalent results to MariaDB for valid SQL
- **ACHIEVEMENT**: All test categories now pass (100% success across 69 tests)

### 8. CURRENT PROJECT STATUS
- MongoSQL translator with **100% MariaDB compatibility (69/69 tests passing)** 🎉
- **COMPLETE SUBQUERY SUPPORT**: All 5 subquery patterns fully implemented and tested
  - SCALAR subqueries: Single value returns with aggregation pipeline integration
  - IN/EXISTS subqueries: Table-based and correlated subquery support
  - ROW subqueries: Multi-column tuple matching with `$and` conditions
  - DERIVED subqueries: Complex table expressions with GROUP BY and field mapping
  - All subquery types: 5/5 working (100% success)
- All major modules complete: ORDER BY, JOINs, GROUP BY, Reserved Words, Conditional Functions, **SUBQUERIES**
- Conditional functions: CASE WHEN, IF, COALESCE, NULLIF implemented (4/4 working)
- Reserved words module in `src/reserved_words/` for MariaDB compatibility
- Token-based parsing architecture throughout project
- **PERFECT COMPATIBILITY ACHIEVED** - No remaining failing tests