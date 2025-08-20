# MongoSQL Translator - Comprehensive Development Guide & Knowledge Base

**Created:** August 18, 2025  
**Project:** SQL to MongoDB Translator  
**Repository:** MongoSQL  
**Status:** Phase 1 Complete (100% MariaDB Compatibility), Phase 2 In Development  

---

## 🚨 CRITICAL - READ FIRST EVERY TIME

### 0. PROJECT OVERVIEW & CURRENT STATUS
MongoSQL is a comprehensive SQL-to-MongoDB translation engine that converts MariaDB SQL queries into MongoDB aggregation pipelines. The project has achieved **100% MariaDB compatibility** with 69/69 tests passing, covering all core SQL operations including complex subqueries, JOINs, and advanced function mappings.

**Current Achievement Status:**
- ✅ **Phase 1 Complete**: 100% core SQL compatibility (69/69 tests)
- 🚧 **Phase 2 Active**: Modern application extensions (JSON, REGEXP, Enhanced Aggregates)
- 📋 **110+ Functions Implemented** across all major categories
- 🏗️ **Modular Architecture** with token-based parsing and extensible design

**COMPLETE SUBQUERY SUPPORT**: All 5 subquery patterns fully implemented and tested
- SCALAR subqueries: Single value returns with aggregation pipeline integration
- IN/EXISTS subqueries: Table-based and correlated subquery support
- ROW subqueries: Multi-column tuple matching with `$and` conditions
- DERIVED subqueries: Complex table expressions with GROUP BY and field mapping
- All subquery types: 5/5 working (100% success)

### 0.5. TRANSLATION-ONLY ARCHITECTURE - CRITICAL
- **NO DATA PROCESSING IN CLIENT** - The Python client is ONLY a translator, never a processor
- **ALL DATA PROCESSING** must occur in MongoDB using aggregation pipelines, queries, and operators
- **TRANSLATE TO MONGODB OPERATIONS** - convert SQL to MongoDB queries that MongoDB executes
- **NEVER** execute subqueries, functions, calculations, or data processing in Python
- **NO CLIENT-SIDE CALCULATIONS** - No math, string manipulation, date arithmetic, or expression evaluation in Python
- **NO JAVASCRIPT FUNCTIONS** - Never use MongoDB `$function` operator with JavaScript code
- **NO EXPRESSION EVALUATION** - Client must not evaluate MongoDB expressions, only generate them
- **EXAMPLE**: Subqueries → `$lookup` stages, Functions → `$expr` operations, JOINs → `$lookup` pipelines
- **SUCCESS EXAMPLE**: DERIVED subqueries → complex `$lookup` with `$group` subpipelines + `$unwind` + `$project`
- **ABSOLUTE RULE**: The client translates SQL syntax to MongoDB syntax - MongoDB does ALL the work

### 0.6. MODULAR ARCHITECTURE - CRITICAL
- **MODULES MUST WORK TOGETHER** - Never build modules in isolation that only handle simple cases
- **EXPECT ALL SQL CONSTRUCTS** - Every module must handle ORDER BY, WHERE, LIMIT, GROUP BY, HAVING, etc.
- **NO CORE MODULE MODIFICATIONS** - Never modify `src/core/translator.py`, `src/core/parser.py` for new features
- **BACKWARDS COMPATIBILITY** - New functionality must not break existing Phase 1 functionality
- **COMPREHENSIVE DESIGN** - JOIN must work with ORDER BY, WHERE with subqueries, functions with aggregation
- **EXTENSION ONLY** - Add new functionality through modules/plugins, never by changing core code
- **INTEGRATION TESTING** - Test complex combinations of SQL constructs, not just isolated features

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
- **CLI FLAGS**: Only `-e` (execute query) is available - NO `--debug`, `--verbose`, or other flags
- **DEBUGGING**: Use `python QA/mariadb_comparison_qa.py --function FUNC_NAME --verbose` for detailed output
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
1. Check reference documentation links (see Documentation Links section below)
2. Review `src/reserved_words/` module for identifier handling
3. Check `.env` file exists and has correct MongoDB settings
4. Load environment variables with `load_dotenv()`
5. Verify MongoDB connection works
6. **Test through `./mongosql` CLI only - complete integration testing**
7. **For detailed debugging**: Use `python QA/mariadb_comparison_qa.py --function FUNC_NAME --verbose`
8. Use token-based parsing only (NO REGEX)
9. Check actual error messages, don't assume

### 6. CLI LIMITATIONS - IMPORTANT
- **MongoSQL CLI**: Only supports `./mongosql database -e "SQL_QUERY"` format
- **NO DEBUG FLAGS**: `--debug`, `--verbose`, `--help` are NOT available on `./mongosql`
- **DEBUGGING**: Use the QA testing framework with `--verbose` for detailed output
- **TESTING**: Use `python QA/mariadb_comparison_qa.py` for comprehensive testing and debugging

### 7. QA TESTING GUIDELINES - CRITICAL
- **ONLY** test SQL queries that execute successfully in MariaDB
- **NEVER** add test cases that fail in MariaDB - we test functionality, not error message comparison
- **VALIDATE** all test queries against MariaDB before adding to QA suite
- **EXAMPLE OF INVALID TEST**: `SELECT ... WHERE col IN (SELECT ... LIMIT 3)` - MariaDB error 1235
- **FOCUS** on comparing successful results between MariaDB and our translator
- **USE** `python QA/mariadb_comparison_qa.py --category <category>` for targeted testing (case insensitive)
- QA testing should prove our translator produces equivalent results to MariaDB for valid SQL
- **ACHIEVEMENT**: All test categories now pass (100% success across 69 tests)

### 7.5. DETERMINISTIC ORDERING - CRITICAL FOR COMPATIBILITY
- **MONGODB vs MARIADB ORDERING**: MongoDB returns documents in arbitrary order, MariaDB has consistent default order (InnoDB storage order)
- **ALWAYS USE EXPLICIT ORDER BY**: Never rely on implicit ordering for test comparisons
- **NULL HANDLING**: Different systems may sort NULL values differently (NULLS FIRST vs NULLS LAST)
- **MULTI-FIELD ORDERING**: Ensure ORDER BY clauses are deterministic enough to produce identical results
- **RIGHT/LEFT JOIN CONSIDERATIONS**: JOIN results may include NULL values that affect ordering
- **TESTING REQUIREMENT**: Both systems must return identical ordered results for valid comparison
- **DEBUGGING TIP**: If results differ, first verify both systems use same ORDER BY with deterministic fields
- **EXAMPLE ISSUE**: `ORDER BY c.customerNumber` in RIGHT JOIN may have NULL customerNumbers with different sort behavior

### 8. COMMON MISTAKES TO AVOID
- ❌ Using regex for SQL parsing (use sqlparse tokens instead)
- ❌ Using localhost hardcoded values
- ❌ Not loading .env file
- ❌ Not including enough context in file edits
- ❌ Assuming MongoDB is running without checking
- ❌ Not reading the full error message carefully
- ❌ **TESTING SUBMODULES DIRECTLY INSTEAD OF USING `./mongosql` CLI**
- ❌ **USING NON-EXISTENT CLI FLAGS** like `--debug`, `--verbose` on `./mongosql`
- ❌ **BUILDING MODULES IN ISOLATION** - Every module must handle all SQL constructs (ORDER BY, WHERE, LIMIT, etc.)
- ❌ **MODIFYING CORE MODULES** - Never change `src/core/translator.py` or `src/core/parser.py` for new features
- ❌ **CREATING CIRCULAR IMPORTS** - Never import `FunctionMapper` from modules

---

## 📚 REFERENCE DOCUMENTATION LINKS

### MariaDB Official Documentation
- **[MariaDB Built-in Functions](https://mariadb.com/kb/en/built-in-functions/)** - Primary function catalog for MariaDB 11.8 LTS
- **[MariaDB Reserved Words](https://mariadb.com/docs/server/reference/sql-structure/sql-language-structure/reserved-words)** - Critical for identifier handling and escaping
- **[MariaDB Date & Time Functions](https://mariadb.com/kb/en/date-time-functions/)** - Comprehensive datetime function reference
- **[MariaDB String Functions](https://mariadb.com/kb/en/string-functions/)** - String manipulation documentation
- **[MariaDB Mathematical Functions](https://mariadb.com/kb/en/numeric-functions/)** - Mathematical function reference
- **[MariaDB Aggregate Functions](https://mariadb.com/kb/en/aggregate-functions/)** - Aggregation function documentation
- **[MariaDB Control Flow Functions](https://mariadb.com/kb/en/control-flow-functions/)** - Conditional logic functions

### MongoDB Official Documentation
- **[MongoDB Aggregation Pipeline Operators](https://docs.mongodb.com/manual/reference/operator/aggregation/)** - Primary translation target reference
- **[MongoDB Date Operators](https://docs.mongodb.com/manual/reference/operator/aggregation/#date-expression-operators)** - Date manipulation in MongoDB
- **[MongoDB String Operators](https://docs.mongodb.com/manual/reference/operator/aggregation/#string-expression-operators)** - String processing operators
- **[MongoDB Mathematical Operators](https://docs.mongodb.com/manual/reference/operator/aggregation/#arithmetic-expression-operators)** - Mathematical operations
- **[MongoDB Conditional Operators](https://docs.mongodb.com/manual/reference/operator/aggregation/#conditional-expression-operators)** - Control flow in aggregation

### SQL Parsing & Language Processing
- **[sqlparse Documentation](https://sqlparse.readthedocs.io/en/latest/)** - SQL parsing library used for token-based parsing
- **[MySQL 8.4 Keywords and Reserved Words](https://dev.mysql.com/doc/refman/8.4/en/keywords.html)** - Comprehensive reserved word documentation

---

## 🔄 FUNCTION MAPPING ANALYSIS

### MariaDB to MongoDB Function Translation Patterns

#### ✅ Direct Mapping (Simple 1:1 translation)
```javascript
// Date/Time Functions
'NOW': { $literal: new Date() }
'YEAR': { $year: "$dateField" }
'MONTH': { $month: "$dateField" }

// Mathematical Functions  
'ABS': { $abs: "$field" }
'ROUND': { $round: ["$field", precision] }
'CEIL': { $ceil: "$field" }

// String Functions
'UPPER': { $toUpper: "$field" }
'LOWER': { $toLower: "$field" }
'LENGTH': { $strLenBytes: "$field" }

// Aggregate Functions
'COUNT': { $sum: 1 }
'SUM': { $sum: "$field" }
'AVG': { $avg: "$field" }
'MAX': { $max: "$field" }
'MIN': { $min: "$field" }
```

#### 🔧 Complex Mapping (Multiple operators/expressions)
```javascript
// Date Formatting
'DATE_FORMAT': {
  $dateToString: {
    format: convertMariaDBFormat(formatString),
    date: "$dateField"
  }
}

// String Functions with Multiple Operations
'SUBSTRING': {
  $substr: ["$field", startPos - 1, length]
}

// Mathematical Functions
'POWER': { $pow: ["$base", "$exponent"] }

// Conditional Functions
'IF': {
  $cond: {
    if: condition,
    then: thenValue,
    else: elseValue
  }
}

// Statistical Functions with Precision Control
'STDDEV_POP': {
  $round: [{ $stdDevPop: "$field" }, 6]
}
```

#### 🚫 No Direct Equivalent (Custom implementation required)
```javascript
// Functions requiring custom logic
'REGEXP_REPLACE': // Requires multiple $replaceAll operations
'FORMAT_BYTES': // Requires custom calculation pipeline
'SOUNDEX': // Requires phonetic algorithm implementation
```

### Function Categories by Implementation Status

| Category | Implemented | Total | Status |
|----------|------------|-------|--------|
| Date/Time Functions | 22+ | 45+ | ✅ Core Complete |
| String Functions | 19+ | 40+ | ✅ Core Complete, 🚧 Extended In Progress |
| Math Functions | 20+ | 30+ | ✅ Complete |
| Aggregate Functions | 9+ | 12+ | ✅ Core Complete, 🚧 Enhanced In Progress |
| Conditional Functions | 4 | 6 | ✅ Complete |
| JSON Functions | 0 | 30+ | 📋 Phase 2 Planned |
| Window Functions | 0 | 16+ | 📋 Phase 3 Planned |

---

## 🔍 SUBQUERY IMPLEMENTATION PATTERNS

### Subquery Types and MongoDB Translation

#### 1. Scalar Subqueries (Single Value)
**Pattern**: Return single value, often with aggregation
```sql
SELECT customer_name, 
       (SELECT AVG(order_amount) FROM orders WHERE customer_id = customers.id) AS avg_order
FROM customers;
```
**MongoDB Translation**: `$lookup` with aggregation pipeline

#### 2. IN/EXISTS Subqueries  
**Pattern**: Check existence or membership
```sql
SELECT * FROM customers 
WHERE customer_id IN (SELECT customer_id FROM orders WHERE order_date > '2024-01-01');
```
**MongoDB Translation**: `$lookup` with result filtering

#### 3. Row Subqueries (Multi-column comparison)
**Pattern**: Compare multiple columns against single row
```sql
SELECT * FROM employees 
WHERE (department_id, salary) = (SELECT department_id, MAX(salary) FROM employees WHERE department = 'Engineering');
```
**MongoDB Translation**: `$lookup` with `$and` conditions

#### 4. Derived Subqueries (Table expressions)
**Pattern**: Subquery in FROM clause creating virtual table
```sql
SELECT sites.site_name, subquery1.total_size 
FROM sites, (SELECT site_name, SUM(file_size) AS total_size FROM pages GROUP BY site_name) subquery1 
WHERE subquery1.site_name = sites.site_name;
```
**MongoDB Translation**: Complex `$lookup` with grouped subpipelines

#### 5. Correlated Subqueries
**Pattern**: Inner query depends on outer query values
```sql
SELECT customer_name FROM customers c1 
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c1.customer_id);
```
**MongoDB Translation**: `$lookup` with `$match` on correlation fields

---

## 📊 QA TESTING FRAMEWORK

### Phase-Based Testing Structure

#### Phase 1: Core SQL Features ✅ COMPLETE
**Command**: `python QA/mariadb_comparison_qa.py --phase 1`
- **Categories**: 10 (datetime, string, math, aggregate, joins, groupby, orderby, distinct, conditional, subqueries)
- **Tests**: 69 total
- **Success Rate**: 100% (with 3 timezone differences)
- **Status**: Production ready

#### Phase 2: Modern Application Extensions 🚧 IN DEVELOPMENT
**Command**: `python QA/mariadb_comparison_qa.py --phase 2`
- **Categories**: 3 (json, extended_string, enhanced_aggregate)
- **Tests**: 31 total  
- **Success Rate**: ~30% (improving as modules are completed)
- **Status**: Active development

### Testing Guidelines
- **ONLY** test SQL queries that execute successfully in MariaDB
- **NEVER** add test cases that fail in MariaDB - we test functionality, not error handling
- **VALIDATE** all test queries against MariaDB before adding to QA suite
- **FOCUS** on comparing successful results between MariaDB and our translator
- **DETERMINISTIC ORDERING**: Always use explicit ORDER BY for result comparison

### Category-Specific Testing
```bash
# Test specific categories
python QA/mariadb_comparison_qa.py --category datetime
python QA/mariadb_comparison_qa.py --category subqueries
python QA/mariadb_comparison_qa.py --category enhanced_aggregate

# Verbose debugging
python QA/mariadb_comparison_qa.py --category datetime --verbose
```

---

## 🚀 DEVELOPMENT ROADMAP

### Phase 1: Core SQL Features ✅ COMPLETE
**Achievement**: 100% MariaDB compatibility (69/69 tests)
- Complete SQL operation support (SELECT, JOIN, WHERE, GROUP BY, ORDER BY)
- All major function categories (Date/Time, String, Math, Aggregate, Conditional)
- Comprehensive subquery implementation (all 5 patterns)
- Production-ready translator with full test coverage

### Phase 2: Modern Application Extensions 🚧 ACTIVE
**Target**: Enhanced functionality for modern web applications

#### 2.1 JSON Functions (HIGH PRIORITY)
**Status**: Ready for implementation - tests defined
- **JSON_EXTRACT** - Extract data from JSON documents
- **JSON_OBJECT** - Create JSON objects from key-value pairs  
- **JSON_ARRAY** - Create JSON arrays from values
- **JSON_UNQUOTE** - Remove quotes from JSON values
- **JSON_KEYS** - Extract keys from JSON objects
- **JSON_LENGTH** - Get JSON array/object length
- **JSON_MERGE** - Merge multiple JSON documents

#### 2.2 Extended String Functions 🚧 IN PROGRESS
**Status**: REGEXP module 100% complete, others in development
- **REGEXP Functions** - Pattern matching (✅ Complete)
- **CONCAT_WS** - Concatenate with separator
- **FORMAT** - Number formatting with locale support  
- **SOUNDEX** - Phonetic matching algorithm
- **HEX/UNHEX** - Hexadecimal conversion functions

#### 2.3 Enhanced Aggregate Functions 🚧 IN PROGRESS
**Status**: Architecture complete, precision issues being resolved
- **GROUP_CONCAT** - String aggregation with separators
- **STDDEV_POP/STDDEV_SAMP** - Statistical standard deviation
- **VAR_POP/VAR_SAMP** - Statistical variance
- **BIT_AND/BIT_OR/BIT_XOR** - Bitwise aggregate operations

### Phase 3: Enterprise Extensions 📋 PLANNED
**Target**: Enterprise-grade database features
- **Window Functions** - Advanced analytical functions
- **Common Table Expressions (CTEs)** - Recursive queries
- **Full-Text Search** - Advanced text search capabilities
- **Geospatial Functions** - Location-based queries
- **Encryption Functions** - Data security operations

---

## 📁 PROJECT STRUCTURE

```
src/
├── core/                    # Core translation engine (DO NOT MODIFY)
│   ├── parser.py           # SQL parsing with sqlparse tokens
│   └── translator.py       # Main translation logic
├── database/               # MongoDB client and connection handling
├── functions/              # Basic function mappings
│   ├── function_mapper.py  # Central function mapping coordinator
│   ├── datetime_functions.py
│   ├── string_functions.py
│   ├── math_functions.py
│   └── aggregate_functions.py
├── modules/                # Extended functionality modules
│   ├── conditional/        # IF, CASE, COALESCE, NULLIF
│   ├── groupby/           # GROUP BY operations
│   ├── joins/             # JOIN operations  
│   ├── orderby/           # ORDER BY operations
│   ├── subqueries/        # All subquery patterns
│   ├── where/             # WHERE clause handling
│   ├── json/              # JSON functions (Phase 2)
│   ├── regexp/            # Regular expression functions (Phase 2)
│   ├── extended_string/   # Extended string functions (Phase 2)
│   └── enhanced_aggregate/ # Enhanced aggregate functions (Phase 2)
├── formatters/            # Result formatting for display
└── utils/                 # Helper utilities and schema validation

QA/
└── mariadb_comparison_qa.py # Comprehensive testing framework
```

---

## 💡 IMPLEMENTATION PATTERNS

### Adding New Functions
1. **Identify Category**: Determine if function belongs to existing or new category
2. **Create Function Mapper**: Add to appropriate `*_functions.py` file
3. **Add to Function Mapper**: Update `function_mapper.py` to include new category
4. **Create Tests**: Add comprehensive test cases to QA framework
5. **Test Integration**: Verify through `./mongosql` CLI tool
6. **Document**: Update function mapping documentation

### Creating New Modules
1. **Module Structure**: Follow established patterns (types, parser, translator, function_mapper)
2. **Integration**: Ensure module works with all SQL constructs (ORDER BY, WHERE, etc.)
3. **Testing**: Create comprehensive test cases covering edge cases
4. **Documentation**: Document module architecture and usage patterns
5. **Avoid Circular Imports**: Never import `FunctionMapper` from modules

### MongoDB Pipeline Patterns
```javascript
// Basic aggregation pipeline structure
[
  { $match: whereConditions },      // Filter documents
  { $lookup: joinDefinitions },     // Join collections
  { $unwind: arrayFields },         // Flatten arrays
  { $group: aggregateOperations },  // Group and aggregate
  { $project: fieldSelection },     // Select/transform fields
  { $sort: orderSpecification },    // Sort results
  { $limit: resultLimit }           // Limit results
]
```

---

## 🐛 PRECISION AND COMPATIBILITY ISSUES

### Common Precision Problems
- **MongoDB vs MariaDB Precision**: MongoDB may return full precision; use `$round` for MariaDB compatibility
- **Statistical Functions**: STDDEV_POP, VAR_POP require precision control to match MariaDB's 6-decimal format
- **Function Mapping**: Enhanced functions may need complex expressions instead of simple operators

### Debugging Precision Issues
1. **Test Function Mapping**: Verify function mapper returns correct MongoDB expressions
2. **Check Pipeline Generation**: Ensure `$round` expressions are properly included
3. **MongoDB Expression Evaluation**: Verify complex expressions in aggregation pipelines are being processed
4. **Avoid Circular Imports**: Function mapper integration can break due to circular dependencies

### Compatibility Considerations
- **Ordering Differences**: Always use explicit ORDER BY for deterministic results
- **NULL Handling**: Different systems may sort NULL values differently
- **Data Type Handling**: Ensure consistent data type handling between systems

---

## 🎓 CONCLUSION

This comprehensive guide represents the complete development intelligence for the MongoSQL translation project. The project has successfully achieved 100% MariaDB compatibility for core SQL operations and is actively developing modern extensions for contemporary application needs.

The modular architecture, comprehensive testing framework, and detailed function mapping analysis provide a solid foundation for continued development and enterprise deployment. The translation-only approach ensures high performance and scalability by leveraging MongoDB's native aggregation capabilities.

**Key Success Factors:**
1. **Token-based parsing** for reliable SQL interpretation
2. **Modular architecture** for maintainable and extensible code
3. **Comprehensive testing** ensuring MariaDB compatibility
4. **Translation-only approach** for optimal performance
5. **Detailed documentation** for sustainable development

The project serves as a production-ready bridge between SQL-based applications and MongoDB's NoSQL capabilities, enabling organizations to leverage MongoDB's scalability while maintaining familiar SQL interfaces.