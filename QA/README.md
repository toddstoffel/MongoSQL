# QA - Quality Assurance Testing Framework

This directory contains quality assurance tools and scripts for the SQL to MongoDB Translator project.

## Scripts

### `mariadb_comparison_qa.py`
Comprehensive side-by-side comparison testing between MariaDB and our SQL to MongoDB translator.

**Features:**
- Automated testing of multiple function categories
- Side-by-side result comparison
- Timezone-aware testing for time functions
- Detailed error reporting and analysis
- CSV export for test results
- Configurable test categories and individual function testing

**Usage:**
```bash
# Run all tests
python QA/mariadb_comparison_qa.py --verbose

# Test specific category
python QA/mariadb_comparison_qa.py --category datetime --verbose

# Test specific function
python QA/mariadb_comparison_qa.py --function "EXTRACT" --verbose

# Export results to CSV
python QA/mariadb_comparison_qa.py --category datetime --export-results

# Set custom timeout
python QA/mariadb_comparison_qa.py --timeout 10 --verbose
```

**Test Categories:**
- `datetime` - Date/time functions (NOW, DATE_FORMAT, EXTRACT, etc.)
- `string` - String manipulation functions (CONCAT, UPPER, SUBSTRING, etc.) 
- `math` - Mathematical functions (ABS, ROUND, SIN, COS, etc.)
- `aggregate` - Aggregate functions (COUNT, AVG, SUM, etc.)
- `all` - Run all test categories

**Requirements:**
- MariaDB credentials configured in `.env` file
- `mysql-connector-python` package installed
- Working SQL to MongoDB translator

**Output:**
- Console output with detailed test results
- Optional CSV export with timestamp
- Success rate statistics and error analysis

## Test Results

Test results are automatically exported to timestamped CSV files in this directory when using the `--export-results` flag.

File format: `qa_results_YYYYMMDD_HHMMSS.csv`

## Configuration

The QA framework uses the same MariaDB connection settings as the main application:
- `MARIADB_HOST`
- `MARIADB_USERNAME` 
- `MARIADB_PASSWORD`
- `MARIADB_DATABASE`
- `MARIADB_PORT`

## Extending Tests

To add new test cases:

1. Edit `mariadb_comparison_qa.py`
2. Add test cases to the appropriate `_get_*_tests()` method
3. Follow the format: `("SQL QUERY", "FUNCTION_NAME")`

Example:
```python
def _get_datetime_tests(self):
    return [
        ("SELECT NEW_FUNCTION('2024-01-15')", "NEW_FUNCTION"),
        # ... other tests
    ]
```

## Best Practices

1. **Run QA tests after any function implementation changes**
2. **Use verbose mode during development for detailed output**
3. **Export results for documentation and tracking**
4. **Test individual functions during development**
5. **Run full test suite before releases**

## Continuous Integration

This QA framework is designed to be integration-friendly:
- Exit codes indicate overall test success/failure
- CSV exports can be archived for historical analysis
- Configurable timeouts prevent hanging in CI environments
- Detailed error reporting for debugging

---

**Maintainer:** SQL to MongoDB Translation Project Team  
**Last Updated:** August 14, 2025
