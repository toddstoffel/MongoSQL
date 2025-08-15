# QA - Quality Assurance Testing Framework

Comprehensive testing framework achieving **85.1% compatibility** between MariaDB and MongoDB SQL translation across 67 test cases in 10 functional categories.

## Test Results Summary

**Current Status (August 14, 2025):**
- **Total Tests**: 67 across 10 categories
- **Success Rate**: 85.1% (57/67 tests passing)
- **Perfect Categories**: 6/10 categories with 100% success

### Category Performance
| Category | Tests | Success Rate | Status |
|----------|-------|--------------|---------|
| **DATETIME** | 22 | 100.0% | ✅ Complete |
| **STRING** | 10 | 100.0% | ✅ Complete |
| **MATH** | 10 | 100.0% | ✅ Complete |
| **AGGREGATE** | 5 | 100.0% | ✅ Complete |
| **JOINS** | 4 | 100.0% | ✅ Complete |
| **ORDER BY** | 3 | 100.0% | ✅ Complete |
| **DISTINCT** | 3 | 100.0% | ✅ Complete |
| **GROUP BY** | 3 | 0.0% | 🔄 In Development |
| **CONDITIONAL** | 4 | 0.0% | 🔄 Planned |
| **SUBQUERIES** | 3 | 0.0% | 🔄 Planned |

## Critical Discovery: Collation Compatibility

**⚠️ Important**: For accurate MariaDB-MongoDB comparison, both systems must use compatible collation:

- **MariaDB**: `utf8mb4_unicode_ci` (case-insensitive Unicode)
- **MongoDB**: Equivalent collation applied automatically:
  ```javascript
  {
    locale: 'en',
    caseLevel: false,     // Case-insensitive
    strength: 1,          // Primary comparison only
    numericOrdering: false
  }
  ```

This ensures ORDER BY operations return identical results between database systems.

## Scripts

### `mariadb_comparison_qa.py`
Production-ready comprehensive testing framework with enhanced features.

**Enhanced Features:**
- **10 test categories** covering all major SQL operations
- **Collation-aware testing** for accurate comparisons
- **Timezone handling** for datetime functions (3 timezone differences noted)
- **Advanced error categorization** (failures vs system errors)
- **Detailed progress reporting** with emojis and colored output
- **Statistical analysis** with success rates per category

**Usage:**
```bash
# Run complete test suite (recommended)
python QA/mariadb_comparison_qa.py

# Test specific categories
python QA/mariadb_comparison_qa.py --category datetime
python QA/mariadb_comparison_qa.py --category orderby

# Test individual functions
python QA/mariadb_comparison_qa.py --function "CONCAT"
python QA/mariadb_comparison_qa.py --function "ORDER_BY_ASC"

# Verbose output for debugging
python QA/mariadb_comparison_qa.py --verbose

# Export results
python QA/mariadb_comparison_qa.py --export-results
```

**Test Categories:**
- `datetime` - 22 date/time functions (NOW, DATE_FORMAT, EXTRACT, MAKEDATE, etc.)
- `string` - 10 string functions (CONCAT, UPPER, SUBSTRING, TRIM, etc.)
- `math` - 10 mathematical functions (ABS, ROUND, SIN, COS, SQRT, etc.)
- `aggregate` - 5 aggregate functions (COUNT, AVG, SUM, MIN, MAX)
- `joins` - 4 JOIN operations (INNER, LEFT, RIGHT, multi-table)
- `orderby` - 3 ORDER BY operations (ASC, DESC, multi-field)
- `distinct` - 3 DISTINCT operations (single, multi-column, with numbers)
- `groupby` - 3 GROUP BY operations (COUNT, AVG, HAVING)
- `conditional` - 4 conditional functions (IF, CASE, COALESCE, NULLIF)
- `subqueries` - 3 subquery types (WHERE, IN, EXISTS)

## Test Architecture

### Database Setup
- **MariaDB**: Reference implementation using `classicmodels` database
- **MongoDB**: Target implementation with matching collation settings
- **Environment**: Uses `.env` configuration for both database connections

### Result Comparison
1. **Exact Match**: Values must be identical (strings, numbers)
2. **Timezone Tolerance**: Datetime functions allow timezone differences
3. **Format Consistency**: Table output parsing handles MariaDB formatting
4. **Error Handling**: Distinguishes between translation errors and system failures

### Quality Metrics
- **Pass Rate**: Percentage of tests with exact matches
- **Timezone Differences**: Noted but counted as passes for datetime functions
- **System Errors**: Database connectivity or parsing issues
- **Translation Failures**: Logic errors in SQL-to-MongoDB conversion
## Configuration

### Environment Variables
```env
# MongoDB Configuration (target system)
MONGO_HOST=cluster0.example.mongodb.net
MONGO_USERNAME=username
MONGO_PASSWORD=password
MONGO_DATABASE=classicmodels
MONGO_AUTH_DATABASE=admin

# MariaDB Configuration (reference system)
MARIADB_HOST=your-mariadb-host
MARIADB_USERNAME=username
MARIADB_PASSWORD=password
MARIADB_DATABASE=classicmodels
```

### Database Requirements
- Both databases must contain identical `classicmodels` sample data
- MariaDB using `utf8mb4_unicode_ci` collation
- MongoDB configured with equivalent collation (handled automatically)

## Extending the Test Suite

### Adding New Test Cases
```python
def _get_new_category_tests(self):
    return [
        ("SELECT NEW_FUNCTION('test')", "NEW_FUNCTION"),
        ("SELECT ANOTHER_FUNC(123)", "ANOTHER_FUNC"),
    ]
```

### Adding New Categories
1. Create `_get_category_tests()` method
2. Add category to `_get_all_tests()` method
3. Update category list in argument parser

### Test Case Format
- **SQL Query**: Valid MariaDB/MySQL SQL statement
- **Test Name**: Descriptive identifier for the test
- **Expected Behavior**: Both systems should return identical results

## Troubleshooting

### Common Issues
1. **Database Connection**: Verify `.env` configuration
2. **Collation Differences**: Ensure MongoDB collation is properly configured
3. **Timezone Variations**: Datetime functions may show timezone differences (acceptable)
4. **Table Parsing**: MariaDB output formatting may require adjustment

### Debug Mode
```bash
# Verbose output with detailed error information
python QA/mariadb_comparison_qa.py --verbose

# Test single function for focused debugging
python QA/mariadb_comparison_qa.py --function "PROBLEMATIC_FUNCTION" --verbose
```

## Test Results Archive

Results are automatically exported with timestamps:
- **Format**: `qa_results_YYYYMMDD_HHMMSS.csv`
- **Content**: Test name, MariaDB result, MongoDB result, status, error details
- **Usage**: Historical tracking and regression analysis

## Continuous Integration

### CI/CD Integration
```bash
# Exit code 0 = all critical tests pass
# Exit code 1 = critical failures detected
python QA/mariadb_comparison_qa.py --ci-mode
```

### Performance Monitoring
- Track success rate trends over time
- Monitor regression in previously passing tests
- Validate new feature implementations

## Development Workflow

### Before Code Changes
1. Run baseline test suite: `python QA/mariadb_comparison_qa.py`
2. Note current success rate (85.1% as of August 14, 2025)

### After Implementation
1. Run targeted category tests
2. Verify no regression in existing functionality
3. Update documentation with new capabilities

### Release Validation
1. Full test suite execution
2. Export and archive results
3. Update README with current statistics

---

**Maintainer**: MongoSQL Translation Project Team  
**Last Updated**: August 14, 2025  
**Test Suite Version**: 2.0 (67 tests, 10 categories)  
**Current Baseline**: 85.1% compatibility
