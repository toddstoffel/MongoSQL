# Reference Links & Resources

**Created:** August 14, 2025  
**Purpose:** Comprehensive list of external resources used during MongoSQL development  
**Maintainer:** SQL to MongoDB Translation Project Team  

## Primary Documentation Sources

### MariaDB Official Documentation
- **[MariaDB Built-in Functions](https://mariadb.com/kb/en/built-in-functions/)** - Primary source for MariaDB 11.8 LTS function catalog
- **[MariaDB Date & Time Functions](https://mariadb.com/kb/en/date-time-functions/)** - Comprehensive datetime function reference
- **[MariaDB String Functions](https://mariadb.com/kb/en/string-functions/)** - String manipulation function documentation
- **[MariaDB Mathematical Functions](https://mariadb.com/kb/en/numeric-functions/)** - Mathematical and numeric function reference
- **[MariaDB Aggregate Functions](https://mariadb.com/kb/en/aggregate-functions/)** - Aggregation function documentation
- **[MariaDB Control Flow Functions](https://mariadb.com/kb/en/control-flow-functions/)** - Conditional logic function reference
- **[MariaDB SQL Statements Reference](https://mariadb.com/docs/server/reference/sql-statements)** - Complete SQL statement syntax and usage reference

### MariaDB Source Code
- **[MariaDB Server Repository](https://github.com/MariaDB/server)** - Official MariaDB server source code for function implementation reference

### MongoDB Official Documentation
- **[MongoDB Aggregation Pipeline Operators](https://docs.mongodb.com/manual/reference/operator/aggregation/)** - Primary translation target reference
- **[MongoDB Date Operators](https://docs.mongodb.com/manual/reference/operator/aggregation/#date-expression-operators)** - Date manipulation in MongoDB
- **[MongoDB String Operators](https://docs.mongodb.com/manual/reference/operator/aggregation/#string-expression-operators)** - String processing operators
- **[MongoDB Mathematical Operators](https://docs.mongodb.com/manual/reference/operator/aggregation/#arithmetic-expression-operators)** - Mathematical operations
- **[MongoDB Conditional Operators](https://docs.mongodb.com/manual/reference/operator/aggregation/#conditional-expression-operators)** - Control flow in aggregation
- **[MongoDB $dateAdd Operator](https://docs.mongodb.com/manual/reference/operator/aggregation/dateAdd/)** - Date arithmetic operations
- **[MongoDB $dateFromString](https://docs.mongodb.com/manual/reference/operator/aggregation/dateFromString/)** - Date parsing from strings
- **[MongoDB $dateToString](https://docs.mongodb.com/manual/reference/operator/aggregation/dateToString/)** - Date formatting operations

### MongoDB Source Code
- **[MongoDB Server Repository](https://github.com/mongodb/mongo)** - Official MongoDB server source code for aggregation operator implementation reference

## SQL Parsing & Language Processing

### Python SQL Parsing Libraries
- **[sqlparse Documentation](https://sqlparse.readthedocs.io/en/latest/)** - SQL parsing library used for token-based parsing
- **[sqlparse GitHub Repository](https://github.com/andialbrecht/sqlparse)** - Source code and examples
- **[Python AST Module](https://docs.python.org/3/library/ast.html)** - Abstract syntax tree processing (considered but not used)

### SQL Standard References
- **[SQL:2016 Standard Overview](https://en.wikipedia.org/wiki/SQL:2016)** - Modern SQL standard reference
- **[MySQL 8.0 Reference Manual](https://dev.mysql.com/doc/refman/8.0/en/)** - MySQL compatibility reference
- **[ISO/IEC 9075 SQL Standard](https://www.iso.org/standard/63555.html)** - Official SQL standard specification

## Development Tools & Libraries

### Python Libraries Used
- **[PyMongo Documentation](https://pymongo.readthedocs.io/en/stable/)** - MongoDB Python driver
- **[Rich Library](https://rich.readthedocs.io/en/stable/)** - Terminal formatting and tables
- **[Click Framework](https://click.palletsprojects.com/)** - Command-line interface framework
- **[Python-dotenv](https://pypi.org/project/python-dotenv/)** - Environment variable management
- **[Regex101](https://regex101.com/)** - Regular expression testing and development

### Database Tools
- **[MongoDB Compass](https://www.mongodb.com/products/compass)** - MongoDB GUI for query testing
- **[MariaDB Client](https://mariadb.com/kb/en/mariadb-client/)** - Command-line MariaDB client for comparison testing

## Function Implementation Research

### Date/Time Function Implementation
- **[MongoDB Date Operations Best Practices](https://docs.mongodb.com/manual/tutorial/model-time-data/)** - Temporal data modeling
- **[ISO 8601 Date Format](https://en.wikipedia.org/wiki/ISO_8601)** - International date format standard
- **[Unix Timestamp Conversion](https://en.wikipedia.org/wiki/Unix_time)** - Epoch time calculations
- **[MariaDB INTERVAL Syntax](https://mariadb.com/kb/en/date-arithmetic/)** - Date arithmetic syntax reference

### String Function Mapping
- **[Unicode Standard](https://unicode.org/standard/standard.html)** - Character encoding reference
- **[Regular Expression Syntax](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_Expressions)** - Regex pattern reference
- **[MariaDB Character Sets](https://mariadb.com/kb/en/character-sets/)** - Character encoding in MariaDB

### Mathematical Function Implementation
- **[IEEE 754 Floating Point](https://en.wikipedia.org/wiki/IEEE_754)** - Floating point arithmetic standard
- **[Mathematical Functions in Programming](https://en.wikipedia.org/wiki/Mathematical_function)** - Function theory reference
- **[Trigonometric Functions](https://en.wikipedia.org/wiki/Trigonometric_functions)** - Mathematical function definitions

## Performance & Optimization

### Query Optimization Resources
- **[MongoDB Query Optimization](https://docs.mongodb.com/manual/core/query-optimization/)** - Query performance tuning
- **[MongoDB Aggregation Performance](https://docs.mongodb.com/manual/core/aggregation-pipeline-optimization/)** - Pipeline optimization techniques
- **[MariaDB Query Optimization](https://mariadb.com/kb/en/query-optimizations/)** - SQL query performance reference

### Python Performance
- **[Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)** - General Python optimization
- **[Profiling Python Code](https://docs.python.org/3/library/profile.html)** - Performance analysis tools
- **[Memory Management in Python](https://docs.python.org/3/c-api/memory.html)** - Memory optimization reference

## Testing & Quality Assurance

### Testing Frameworks
- **[pytest Documentation](https://docs.pytest.org/en/stable/)** - Python testing framework
- **[unittest Module](https://docs.python.org/3/library/unittest.html)** - Built-in testing framework
- **[MariaDB Test Suite](https://mariadb.com/kb/en/mysql-test/)** - Database testing methodology

### Code Quality Tools
- **[Black Code Formatter](https://black.readthedocs.io/en/stable/)** - Python code formatting
- **[pylint](https://pylint.pycqa.org/en/latest/)** - Code analysis tool
- **[mypy](https://mypy.readthedocs.io/en/stable/)** - Static type checking

## Architecture & Design Patterns

### Software Architecture
- **[Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)** - Architectural design principles
- **[Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)** - Port and adapter pattern
- **[Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)** - DDD principles

### Design Patterns
- **[Singleton Pattern](https://refactoring.guru/design-patterns/singleton)** - Used for function mappers
- **[Strategy Pattern](https://refactoring.guru/design-patterns/strategy)** - Function mapping strategy
- **[Factory Pattern](https://refactoring.guru/design-patterns/factory-method)** - Parser factory implementation

## Database Theory & Translation

### Query Translation Research
- **[Database Query Translation](https://en.wikipedia.org/wiki/Query_translation)** - Theoretical foundation
- **[SQL to NoSQL Migration](https://docs.mongodb.com/manual/reference/sql-comparison/)** - MongoDB's SQL comparison guide
- **[Relational to Document Model](https://docs.mongodb.com/manual/core/data-modeling-introduction/)** - Data model conversion

### Function Mapping Theory
- **[Function Equivalence](https://en.wikipedia.org/wiki/Functional_equivalence)** - Mathematical equivalence concepts
- **[Type System Conversion](https://en.wikipedia.org/wiki/Type_conversion)** - Data type mapping theory
- **[Semantic Preservation](https://en.wikipedia.org/wiki/Semantics)** - Meaning preservation in translation

## Community Resources & Forums

### Development Communities
- **[Stack Overflow - MongoDB](https://stackoverflow.com/questions/tagged/mongodb)** - Community Q&A for MongoDB
- **[Stack Overflow - MariaDB](https://stackoverflow.com/questions/tagged/mariadb)** - Community Q&A for MariaDB
- **[MongoDB Community Forums](https://community.mongodb.com/)** - Official MongoDB community
- **[MariaDB Community](https://mariadb.com/kb/en/mariadb-community/)** - MariaDB community resources

### Code Examples & Tutorials
- **[MongoDB University](https://university.mongodb.com/)** - Official MongoDB training
- **[Real Python](https://realpython.com/)** - Python development tutorials
- **[Python Package Index (PyPI)](https://pypi.org/)** - Python package repository

## Standards & Specifications

### Data Standards
- **[JSON Standard (RFC 7159)](https://tools.ietf.org/html/rfc7159)** - JSON format specification
- **[BSON Specification](http://bsonspec.org/)** - MongoDB's binary JSON format
- **[CSV Format (RFC 4180)](https://tools.ietf.org/html/rfc4180)** - Comma-separated values format

### Protocol Standards
- **[HTTP/1.1 (RFC 2616)](https://tools.ietf.org/html/rfc2616)** - Web protocol reference
- **[MongoDB Wire Protocol](https://docs.mongodb.com/manual/reference/mongodb-wire-protocol/)** - MongoDB communication protocol

## License & Legal References

### Open Source Licenses
- **[MIT License](https://opensource.org/licenses/MIT)** - Common open source license
- **[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)** - Apache software license
- **[MongoDB License](https://www.mongodb.com/licensing/server-side-public-license)** - MongoDB SSPL license

---

## Usage Guidelines

### How to Use These References
1. **Primary Documentation** - Start with official docs for authoritative information
2. **Implementation Examples** - Use community resources for practical examples
3. **Standards Compliance** - Reference specifications for compatibility requirements
4. **Performance Optimization** - Consult optimization guides for efficiency improvements

### Contribution Guidelines
When adding new references:
1. Verify the source is authoritative and current
2. Include a brief description of the resource's relevance
3. Organize by category for easy navigation
4. Update the modification date at the top of this document

### Maintenance Schedule
- **Weekly Review** - Check for broken links during active development
- **Monthly Update** - Add new resources discovered during implementation
- **Quarterly Audit** - Remove outdated or superseded references
- **Version Updates** - Update documentation links when new versions are released

---

**Last Updated:** August 14, 2025  
**Next Review:** August 21, 2025  
**Document Version:** 1.0
