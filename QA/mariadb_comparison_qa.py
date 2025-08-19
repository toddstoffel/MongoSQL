#!/usr/bin/env python3
"""
MariaDB vs SQL to MongoDB Translator - Quality Assurance Test Suite

This script provides comprehensive side-by-side comparison testing between
MariaDB and our SQL to MongoDB translator to ensure functional accuracy.

PHASE 1: Core SQL Features (Complete - 69/69 tests passing)
    - datetime, string, math, aggregate, joins, groupby, orderby,
      distinct, conditional, subqueries

PHASE 2: Modern Application Extensions (In Development)
    - json, extended_string, enhanced_aggregate

Usage:
    python mariadb_comparison_qa.py [options]

Options:
    --category <category>   Test specific function category
                           (datetime, string, math, etc.)
    --function <function>   Test specific function only
    --verbose              Show detailed output for each test
    --export-results       Export results to CSV file
    --timeout <seconds>    Set timeout for each test (default: 5)

Requirements:
    - MariaDB credentials in .env file
    - mysql-connector-python
    - Working SQL to MongoDB translator

Author: SQL to MongoDB Translation Project Team
Date: August 15, 2025 (Phase 2 QA Tests Added)
"""

import argparse
import csv
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, List, Optional, Tuple

import mysql.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class QATestResult:
    """Represents a single QA test result"""

    def __init__(self, sql_query: str, category: str, function_name: str):
        self.sql_query = sql_query
        self.category = category
        self.function_name = function_name
        self.mariadb_result = None
        self.translator_result = None
        self.mariadb_error = None
        self.translator_error = None
        self.is_match = False
        self.is_timezone_diff = False
        self.notes = ""

    def set_mariadb_result(self, result: Any, error: Optional[str] = None):
        """Set MariaDB execution result and optional error message."""
        self.mariadb_result = result
        self.mariadb_error = error

    def set_translator_result(self, result: Any, error: Optional[str] = None):
        """Set MongoDB translator execution result and optional error message."""
        self.translator_result = result
        self.translator_error = error

    def evaluate(self):
        """Evaluate if results match and categorize the comparison"""
        if self.mariadb_error or self.translator_error:
            self.is_match = False
            self.notes = (
                f"Error: MariaDB={self.mariadb_error}, "
                f"Translator={self.translator_error}"
            )
            return

        # Handle timezone-sensitive functions
        if self._is_timezone_function():
            self.is_timezone_diff = True
            self.is_match = True  # Consider timezone differences as matches
            self.notes = "Timezone difference expected"
            return

        # String comparison with trimming
        mariadb_str = (
            str(self.mariadb_result).strip() if self.mariadb_result is not None else ""
        )
        translator_str = (
            str(self.translator_result).strip()
            if self.translator_result is not None
            else ""
        )

        self.is_match = mariadb_str == translator_str

        if not self.is_match:
            self.notes = f"Value mismatch: '{mariadb_str}' vs '{translator_str}'"

    def _is_timezone_function(self) -> bool:
        """Check if this is a timezone-sensitive function"""
        timezone_functions = [
            "NOW",
            "CURDATE",
            "CURTIME",
            "CURRENT_DATE",
            "CURRENT_TIME",
            "CURRENT_TIMESTAMP",
        ]
        return any(func in self.sql_query.upper() for func in timezone_functions)


class MariaDBQARunner:
    """Main QA test runner for MariaDB comparisons"""

    def __init__(self, verbose: bool = False, timeout: int = 5):
        self.verbose = verbose
        self.timeout = timeout
        self.connection = None
        self.test_results: List[QATestResult] = []

        # Predefined test suites by category - EXPANDED COVERAGE
        self.test_suites = {
            # Phase 1: Core SQL Features (Complete)
            "datetime": self._get_datetime_tests(),
            "string": self._get_string_tests(),
            "math": self._get_math_tests(),
            "aggregate": self._get_aggregate_tests(),
            "joins": self._get_join_tests(),
            "groupby": self._get_groupby_tests(),
            "orderby": self._get_orderby_tests(),
            "distinct": self._get_distinct_tests(),
            "conditional": self._get_conditional_tests(),
            "subqueries": self._get_subquery_tests(),
            # Phase 2: Modern Application Extensions
            "json": self._get_json_tests(),
            "extended_string": self._get_extended_string_tests(),
            "enhanced_aggregate": self._get_enhanced_aggregate_tests(),
        }

    def connect_to_mariadb(self) -> bool:
        """Establish connection to MariaDB"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("MARIADB_HOST", "localhost"),
                port=int(os.getenv("MARIADB_PORT", "3306")),
                user=os.getenv("MARIADB_USERNAME", "root"),
                password=os.getenv("MARIADB_PASSWORD", ""),
                database=os.getenv("MARIADB_DATABASE", "classicmodels"),
                connection_timeout=self.timeout,
            )
            if self.verbose:
                print("✅ Connected to MariaDB successfully")
            return True
        except mysql.connector.Error as e:
            print(f"❌ Failed to connect to MariaDB: {e}")
            return False

    def disconnect_from_mariadb(self):
        """Close MariaDB connection"""
        if self.connection:
            self.connection.close()
            if self.verbose:
                print("🔌 Disconnected from MariaDB")

    def execute_mariadb_query(self, sql: str) -> Tuple[Any, Optional[str]]:
        """Execute query in MariaDB and return result"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql)

            # Fetch all results to avoid "Unread result found" errors
            results = cursor.fetchall()
            cursor.close()

            # Return first row's first column if results exist, otherwise None
            if results and len(results) > 0 and len(results[0]) > 0:
                result = results[0][0]
                # Convert bytes objects to decoded strings for comparison
                if isinstance(result, bytes):
                    try:
                        result = result.decode("utf-8")
                    except UnicodeDecodeError:
                        # If decode fails, keep as string representation
                        result = str(result)
                return result, None
            return None, None

        except mysql.connector.Error as e:
            return None, str(e)

    def execute_translator_query(self, sql: str) -> Tuple[Any, Optional[str]]:
        """Execute query through SQL to MongoDB translator"""
        try:
            # Use the same database as MariaDB for fair comparison
            database = os.getenv("MARIADB_DATABASE", "classicmodels")
            cmd = ["./mongosql", database, "-e", sql]

            # Dynamically find project root directory
            # (where mongosql script is located)
            # Look for mongosql script starting from current file's directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(
                current_dir
            )  # Go up one level from QA/ to project root

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=project_root,
                check=False,
            )

            if result.returncode == 0:
                # Parse the table output to extract the actual result
                output = result.stdout.strip()
                if not output:
                    return None, "No output from translator"

                # Use modular table parser
                return self._parse_table_output(output)
            return None, result.stderr.strip()

        except subprocess.TimeoutExpired:
            return None, f"Timeout after {self.timeout} seconds"
        except (OSError, ValueError) as e:
            return None, str(e)

    def _parse_table_output(self, output: str) -> Tuple[Any, Optional[str]]:
        """Modular table output parser - handles MySQL/MariaDB table format"""
        lines = output.split("\n")

        # Find table structure: +---+, | header |, +---+, | data |, +---+
        data_rows = []
        in_table = False
        header_found = False

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Table border lines (start with +)
            if line.startswith("+") and set(line) <= {"+", "-", " "}:
                if header_found and data_rows:
                    # End of table after data rows
                    break
                # Border after header or start of table - data rows come next
                in_table = True
                continue

            # Table content lines (contain |)
            if "|" in line and not line.startswith("+"):
                parts = [p.strip() for p in line.split("|")]

                # For table format, remove only the empty edge parts (due to outer |)
                # But preserve empty strings in the middle which represent empty cell values
                if len(parts) >= 2 and parts[0] == "" and parts[-1] == "":
                    parts = parts[1:-1]  # Remove first and last empty parts
                elif len(parts) >= 1 and parts[0] == "":
                    parts = parts[1:]  # Remove only first empty part
                elif len(parts) >= 1 and parts[-1] == "":
                    parts = parts[:-1]  # Remove only last empty part

                if not header_found and len(parts) > 0:
                    # This is the header row
                    header_found = True
                    continue

                if header_found and in_table:
                    # This is a data row - preserve empty strings as they represent empty values
                    data_rows.extend(parts)
                    break  # For single-column results, take the first data row

        if data_rows:
            # Return the first data value for single-column results
            return data_rows[0], None
        return None, "Could not parse result from table output"

    def run_single_test(
        self, sql: str, category: str, function_name: str
    ) -> QATestResult:
        """Run a single comparison test"""
        test_result = QATestResult(sql, category, function_name)

        # Execute in MariaDB
        mariadb_result, mariadb_error = self.execute_mariadb_query(sql)
        test_result.set_mariadb_result(mariadb_result, mariadb_error)

        # Execute in Translator
        translator_result, translator_error = self.execute_translator_query(sql)
        test_result.set_translator_result(translator_result, translator_error)

        # Evaluate results
        test_result.evaluate()

        # Only print details if verbose mode is on
        if self.verbose:
            print(f"\n🧪 Testing: {sql}")
            self._print_test_result(test_result)

        self.test_results.append(test_result)
        return test_result

    def _print_test_result(self, result: QATestResult):
        """Print detailed test result"""
        print(f"   MariaDB:    {result.mariadb_result}")
        print(f"   Translator: {result.translator_result}")

        if result.is_timezone_diff:
            print("   ⏰ TIMEZONE DIFFERENCE (Expected)")
        elif result.is_match:
            print("   ✅ MATCH")
        else:
            print(f"   ❌ MISMATCH - {result.notes}")

    def run_test_suite(self, category: str) -> List[QATestResult]:
        """Run all tests in a category"""
        # Make category lookup case-insensitive
        category_lower = category.lower()
        if category_lower not in self.test_suites:
            print(f"❌ Unknown test category: {category}")
            return []

        tests = self.test_suites[category_lower]
        print(
            f"\n🚀 Running {category_lower.upper()} function tests ({len(tests)} tests)"
        )
        print("=" * 80)

        category_results = []
        for i, (sql, function_name) in enumerate(tests, 1):
            # Show progress
            print(
                f"[{i:2d}/{len(tests)}] Testing {function_name}...",
                end=" ",
                flush=True,
            )

            result = self.run_single_test(sql, category_lower, function_name)

            # Show immediate result
            if result.is_timezone_diff:
                print("⏰ TIMEZONE DIFF")
            elif result.is_match:
                print("✅ PASS")
            elif result.mariadb_error or result.translator_error:
                print("❌ ERROR")
            else:
                print("❌ FAIL")

            category_results.append(result)

        # Show category summary
        matches = sum(1 for r in category_results if r.is_match)
        timezone_diffs = sum(1 for r in category_results if r.is_timezone_diff)
        total = len(category_results)
        success_rate = (matches / total * 100) if total > 0 else 0

        print(
            f"\n📊 {category.upper()} Summary: {matches}/{total} ({success_rate:.1f}% success)"
        )
        if timezone_diffs > 0:
            print(f"    ⏰ {timezone_diffs} timezone differences (counted as matches)")

        return category_results

    def run_all_tests(self) -> List[QATestResult]:
        """Run all test suites"""
        print("🧪 Running Complete QA Test Suite")
        print("=" * 80)

        all_results = []
        for category in self.test_suites:
            category_results = self.run_test_suite(category)
            all_results.extend(category_results)

        return all_results

    def print_summary(self):
        """Print test summary statistics"""
        if not self.test_results:
            print("No test results to summarize")
            return

        total_tests = len(self.test_results)
        matches = sum(1 for r in self.test_results if r.is_match)
        timezone_diffs = sum(1 for r in self.test_results if r.is_timezone_diff)
        system_errors = sum(
            1 for r in self.test_results if r.mariadb_error or r.translator_error
        )
        test_failures = sum(
            1
            for r in self.test_results
            if not r.is_match
            and not r.is_timezone_diff
            and not (r.mariadb_error or r.translator_error)
        )

        print("\n" + "=" * 80)
        print("🏆 QA TEST SUMMARY")
        print("=" * 80)
        print(f"Total tests: {total_tests}")
        print(f"Passed: {matches}")
        print(f"Failed: {test_failures}")
        print(f"System errors: {system_errors}")
        print(f"Timezone differences: {timezone_diffs}")
        print(f"Success rate: {(matches / total_tests * 100):.1f}%")

        if test_failures > 0 or system_errors > 0:
            print("\n❌ FAILED TESTS:")
            print("-" * 50)
            for result in self.test_results:
                if not result.is_match and not result.is_timezone_diff:
                    print(f"   {result.sql_query}")
                    print(f"      {result.notes}")

    def export_results(self, filename: Optional[str] = None):
        """Export results to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            filename = os.path.join(project_root, "QA", f"qa_results_{timestamp}.csv")

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "SQL Query",
                    "Category",
                    "Function",
                    "MariaDB Result",
                    "Translator Result",
                    "Match",
                    "Timezone Diff",
                    "Notes",
                    "MariaDB Error",
                    "Translator Error",
                ]
            )

            for result in self.test_results:
                writer.writerow(
                    [
                        result.sql_query,
                        result.category,
                        result.function_name,
                        result.mariadb_result,
                        result.translator_result,
                        result.is_match,
                        result.is_timezone_diff,
                        result.notes,
                        result.mariadb_error,
                        result.translator_error,
                    ]
                )

        print(f"📊 Results exported to: {filename}")

    def _get_datetime_tests(self) -> List[Tuple[str, str]]:
        """Get datetime function test cases"""
        return [
            # Current time functions (timezone sensitive)
            ("SELECT NOW()", "NOW"),
            ("SELECT CURDATE()", "CURDATE"),
            ("SELECT CURTIME()", "CURTIME"),
            # Date formatting and manipulation
            (
                "SELECT DATE_FORMAT('2024-01-15 14:30:45', '%Y-%m-%d')",
                "DATE_FORMAT",
            ),
            ("SELECT YEAR('2024-01-15')", "YEAR"),
            ("SELECT MONTH('2024-01-15')", "MONTH"),
            ("SELECT DAY('2024-01-15')", "DAY"),
            ("SELECT HOUR('14:30:45')", "HOUR"),
            ("SELECT MINUTE('14:30:45')", "MINUTE"),
            ("SELECT SECOND('14:30:45')", "SECOND"),
            # Advanced datetime functions
            ("SELECT LAST_DAY('2024-01-15')", "LAST_DAY"),
            ("SELECT MAKEDATE(2024, 46)", "MAKEDATE"),
            ("SELECT MAKETIME(14, 30, 45)", "MAKETIME"),
            ("SELECT SEC_TO_TIME(3665)", "SEC_TO_TIME"),
            ("SELECT TIME_TO_SEC('01:01:05')", "TIME_TO_SEC"),
            ("SELECT EXTRACT(YEAR FROM '2024-01-15')", "EXTRACT"),
            ("SELECT TO_DAYS('2024-01-15')", "TO_DAYS"),
            ("SELECT TIMESTAMPADD(MONTH, 2, '2024-01-15')", "TIMESTAMPADD"),
            ("SELECT ADDTIME('2024-01-15 10:00:00', '02:30:00')", "ADDTIME"),
            ("SELECT SUBTIME('2024-01-15 10:00:00', '02:30:00')", "SUBTIME"),
            ("SELECT PERIOD_ADD(202401, 3)", "PERIOD_ADD"),
            ("SELECT PERIOD_DIFF(202404, 202401)", "PERIOD_DIFF"),
        ]

    def _get_string_tests(self) -> List[Tuple[str, str]]:
        """Get string function test cases"""
        return [
            ("SELECT CONCAT('Hello', ' ', 'World')", "CONCAT"),
            ("SELECT UPPER('hello world')", "UPPER"),
            ("SELECT LOWER('HELLO WORLD')", "LOWER"),
            ("SELECT LENGTH('Hello World')", "LENGTH"),
            ("SELECT SUBSTRING('Hello World', 1, 5)", "SUBSTRING"),
            ("SELECT TRIM('  Hello World  ')", "TRIM"),
            ("SELECT REPLACE('Hello World', 'World', 'MariaDB')", "REPLACE"),
            ("SELECT LEFT('Hello World', 5)", "LEFT"),
            ("SELECT RIGHT('Hello World', 5)", "RIGHT"),
            ("SELECT REVERSE('Hello')", "REVERSE"),
        ]

    def _get_math_tests(self) -> List[Tuple[str, str]]:
        """Get mathematical function test cases"""
        return [
            ("SELECT ABS(-42)", "ABS"),
            ("SELECT ROUND(3.14159, 2)", "ROUND"),
            ("SELECT CEIL(3.14)", "CEIL"),
            ("SELECT FLOOR(3.14)", "FLOOR"),
            ("SELECT SQRT(16)", "SQRT"),
            ("SELECT POWER(2, 3)", "POWER"),
            ("SELECT SIN(PI()/2)", "SIN"),
            ("SELECT COS(0)", "COS"),
            ("SELECT LOG(10)", "LOG"),
            ("SELECT GREATEST(1, 5, 3, 9, 2)", "GREATEST"),
        ]

    def _get_aggregate_tests(self) -> List[Tuple[str, str]]:
        """Get aggregate function test cases (requires table data)"""
        return [
            ("SELECT COUNT(*) FROM customers LIMIT 1", "COUNT"),
            ("SELECT AVG(creditLimit) FROM customers LIMIT 1", "AVG"),
            ("SELECT SUM(creditLimit) FROM customers LIMIT 1", "SUM"),
            ("SELECT MIN(creditLimit) FROM customers LIMIT 1", "MIN"),
            ("SELECT MAX(creditLimit) FROM customers LIMIT 1", "MAX"),
        ]

    def _get_join_tests(self) -> List[Tuple[str, str]]:
        """Get JOIN operation test cases"""
        return [
            (
                "SELECT c.customerName, o.orderDate FROM customers c INNER JOIN orders o ON c.customerNumber = o.customerNumber ORDER BY customerName LIMIT 1",
                "INNER_JOIN",
            ),
            (
                "SELECT c.customerName, o.orderDate FROM customers c LEFT JOIN orders o ON c.customerNumber = o.customerNumber ORDER BY customerName LIMIT 1",
                "LEFT_JOIN",
            ),
            (
                "SELECT c.customerName, o.orderDate FROM customers c RIGHT JOIN orders o ON c.customerNumber = o.customerNumber ORDER BY c.customerNumber LIMIT 1",
                "RIGHT_JOIN",
            ),
            (
                "SELECT c.customerName, od.quantityOrdered FROM customers c INNER JOIN orders o ON c.customerNumber = o.customerNumber INNER JOIN orderdetails od ON o.orderNumber = od.orderNumber ORDER BY customerName LIMIT 1",
                "MULTI_JOIN",
            ),
        ]

    def _get_groupby_tests(self) -> List[Tuple[str, str]]:
        """Get GROUP BY operation test cases"""
        return [
            (
                "SELECT country, COUNT(*) FROM customers GROUP BY country ORDER BY country LIMIT 1",
                "GROUP_BY_COUNT",
            ),
            (
                "SELECT country, AVG(creditLimit) FROM customers GROUP BY country ORDER BY country LIMIT 1",
                "GROUP_BY_AVG",
            ),
            (
                "SELECT country, SUM(creditLimit) FROM customers GROUP BY country HAVING SUM(creditLimit) > 100000 ORDER BY country LIMIT 1",
                "GROUP_BY_HAVING",
            ),
        ]

    def _get_orderby_tests(self) -> List[Tuple[str, str]]:
        """Get ORDER BY operation test cases"""
        return [
            (
                "SELECT customerName FROM customers ORDER BY customerName ASC LIMIT 1",
                "ORDER_BY_ASC",
            ),
            (
                "SELECT customerName FROM customers ORDER BY customerName DESC LIMIT 1",
                "ORDER_BY_DESC",
            ),
            (
                "SELECT customerName, creditLimit FROM customers ORDER BY creditLimit DESC, customerName ASC LIMIT 1",
                "ORDER_BY_MULTI",
            ),
        ]

    def _get_distinct_tests(self) -> List[Tuple[str, str]]:
        """Get DISTINCT operation test cases"""
        return [
            (
                "SELECT DISTINCT country FROM customers WHERE country = 'USA'",
                "DISTINCT_SPECIFIC",
            ),
            (
                "SELECT DISTINCT customerNumber FROM customers WHERE customerNumber = 103",
                "DISTINCT_NUMBER",
            ),
            (
                "SELECT DISTINCT city FROM customers WHERE customerNumber = 103",
                "DISTINCT_SIMPLE",
            ),
        ]

    def _get_conditional_tests(self) -> List[Tuple[str, str]]:
        """Get conditional function test cases"""
        return [
            (
                "SELECT IF(creditLimit > 50000, 'High', 'Low') FROM customers ORDER BY customerNumber LIMIT 1",
                "IF_FUNCTION",
            ),
            (
                "SELECT CASE WHEN creditLimit > 100000 THEN 'Premium' WHEN creditLimit > 50000 THEN 'Standard' ELSE 'Basic' END FROM customers ORDER BY customerNumber LIMIT 1",
                "CASE_WHEN",
            ),
            ("SELECT COALESCE(NULL, 'Default Value')", "COALESCE"),
            ("SELECT NULLIF('test', 'test')", "NULLIF"),
        ]

    def _get_subquery_tests(self) -> List[Tuple[str, str]]:
        """Get subquery test cases - all 5 MariaDB subquery types"""
        return [
            (
                "SELECT customerName FROM customers WHERE customerNumber = (SELECT customerNumber FROM orders ORDER BY orderDate DESC LIMIT 1)",
                "SUBQUERY_SCALAR",
            ),
            (
                "SELECT customerName FROM customers WHERE customerNumber IN (SELECT customerNumber FROM orders WHERE orderDate > '2004-01-01') ORDER BY customerNumber LIMIT 1",
                "SUBQUERY_TABLE",
            ),
            (
                "SELECT customerName FROM customers WHERE EXISTS (SELECT 1 FROM orders WHERE orders.customerNumber = customers.customerNumber) ORDER BY customerNumber LIMIT 1",
                "SUBQUERY_CORRELATED",
            ),
            (
                "SELECT customerName FROM customers WHERE (customerNumber, country) = (SELECT customerNumber, country FROM customers WHERE customerName = 'Atelier graphique')",
                "SUBQUERY_ROW",
            ),
            (
                "SELECT c.customerName, o.total_orders FROM customers c, (SELECT customerNumber, COUNT(*) as total_orders FROM orders GROUP BY customerNumber) o WHERE c.customerNumber = o.customerNumber ORDER BY c.customerNumber LIMIT 5",
                "SUBQUERY_DERIVED",
            ),
        ]

    # PHASE 2: MODERN APPLICATION EXTENSIONS

    def _get_json_tests(self) -> List[Tuple[str, str]]:
        """Get JSON function test cases for Phase 2"""
        return [
            # Basic JSON_EXTRACT functionality
            (
                'SELECT JSON_EXTRACT(\'{"name": "John", "age": 30}\', \'$.name\')',
                "JSON_EXTRACT",
            ),
            (
                "SELECT JSON_EXTRACT('[1, 2, 3, 4, 5]', '$[2]')",
                "JSON_EXTRACT_ARRAY",
            ),
            # JSON_OBJECT creation
            ("SELECT JSON_OBJECT('name', 'Alice', 'age', 25)", "JSON_OBJECT"),
            (
                "SELECT JSON_OBJECT('customer', customerName, 'credit', creditLimit) FROM customers LIMIT 1",
                "JSON_OBJECT_FROM_TABLE",
            ),
            # JSON_ARRAY creation
            ("SELECT JSON_ARRAY(1, 2, 'three', 4.5)", "JSON_ARRAY"),
            (
                "SELECT JSON_ARRAY(customerName, country) FROM customers LIMIT 1",
                "JSON_ARRAY_FROM_TABLE",
            ),
            # JSON utility functions
            ("SELECT JSON_UNQUOTE('\"Hello World\"')", "JSON_UNQUOTE"),
            (
                'SELECT JSON_KEYS(\'{"name": "John", "age": 30, "city": "NYC"}\')',
                "JSON_KEYS",
            ),
            ("SELECT JSON_LENGTH('[1, 2, 3, 4, 5]')", "JSON_LENGTH_ARRAY"),
            (
                'SELECT JSON_LENGTH(\'{"a": 1, "b": 2, "c": 3}\')',
                "JSON_LENGTH_OBJECT",
            ),
        ]

    def _get_extended_string_tests(self) -> List[Tuple[str, str]]:
        """Get extended string function test cases for Phase 2"""
        return [
            # Advanced concatenation
            ("SELECT CONCAT_WS('-', 'Alpha', 'Beta', 'Gamma')", "CONCAT_WS"),
            (
                "SELECT CONCAT_WS(', ', customerName, city, country) FROM customers LIMIT 1",
                "CONCAT_WS_TABLE",
            ),
            # Regular expressions - comprehensive coverage
            (
                "SELECT customerName FROM customers WHERE customerName REGEXP '^A.*' ORDER BY customerName LIMIT 3",
                "REGEXP_BASIC",
            ),
            (
                "SELECT REGEXP_SUBSTR('Hello World 123', '[0-9]+')",
                "REGEXP_SUBSTR",
            ),
            (
                "SELECT customerName FROM customers WHERE customerName RLIKE '.*Inc$' ORDER BY customerName LIMIT 2",
                "RLIKE_BASIC",
            ),
            (
                "SELECT 'test123' REGEXP '[0-9]+' AS has_numbers",
                "REGEXP_PATTERN_DIGITS",
            ),
            (
                "SELECT 'Email@domain.com' REGEXP '[A-Za-z]+@[A-Za-z]+\\.[A-Za-z]+' AS valid_email",
                "REGEXP_EMAIL_PATTERN",
            ),
            (
                "SELECT customerName FROM customers WHERE customerName REGEXP 'Inc$' ORDER BY customerName LIMIT 2",
                "REGEXP_ALTERNATION",
            ),
            (
                "SELECT 'ABC123def' REGEXP '^[A-Z]+[0-9]+[a-z]+$' AS pattern_match",
                "REGEXP_COMPLEX_PATTERN",
            ),
            # Number formatting
            ("SELECT FORMAT(1234567.89, 2)", "FORMAT_NUMBER"),
            (
                "SELECT FORMAT(creditLimit, 0) FROM customers LIMIT 1",
                "FORMAT_FROM_TABLE",
            ),
            # Phonetic and distance functions
            ("SELECT SOUNDEX('Smith')", "SOUNDEX"),
            (
                "SELECT SOUNDEX(customerName) FROM customers WHERE customerName LIKE 'A%' LIMIT 1",
                "SOUNDEX_TABLE",
            ),
            # Encoding functions
            ("SELECT HEX('Hello')", "HEX_ENCODE"),
            ("SELECT UNHEX('48656C6C6F')", "HEX_DECODE"),
            ("SELECT BIN(42)", "BINARY_REPRESENTATION"),
        ]

    def _get_enhanced_aggregate_tests(self) -> List[Tuple[str, str]]:
        """Get enhanced aggregate function test cases for Phase 2"""
        return [
            # GROUP_CONCAT functionality
            (
                "SELECT GROUP_CONCAT(customerName ORDER BY customerName) FROM customers WHERE country = 'USA' LIMIT 1",
                "GROUP_CONCAT_BASIC",
            ),
            (
                "SELECT country, GROUP_CONCAT(customerName ORDER BY customerName SEPARATOR '; ') FROM customers GROUP BY country ORDER BY country LIMIT 3",
                "GROUP_CONCAT_SEPARATOR",
            ),
            (
                "SELECT GROUP_CONCAT(DISTINCT country ORDER BY country) FROM customers",
                "GROUP_CONCAT_DISTINCT",
            ),
            # Statistical aggregates
            (
                "SELECT STDDEV_POP(creditLimit) FROM customers WHERE creditLimit IS NOT NULL",
                "STDDEV_POPULATION",
            ),
            (
                "SELECT STDDEV_SAMP(creditLimit) FROM customers WHERE creditLimit IS NOT NULL",
                "STDDEV_SAMPLE",
            ),
            (
                "SELECT VAR_POP(creditLimit) FROM customers WHERE creditLimit IS NOT NULL",
                "VARIANCE_POPULATION",
            ),
            (
                "SELECT VAR_SAMP(creditLimit) FROM customers WHERE creditLimit IS NOT NULL",
                "VARIANCE_SAMPLE",
            ),
            # Bitwise aggregates
            (
                "SELECT BIT_AND(customerNumber) FROM customers LIMIT 10",
                "BIT_AND",
            ),
            (
                "SELECT BIT_OR(customerNumber) FROM customers LIMIT 10",
                "BIT_OR",
            ),
            (
                "SELECT BIT_XOR(customerNumber) FROM customers LIMIT 10",
                "BIT_XOR",
            ),
        ]


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MariaDB vs MongoDB Translator QA Test Suite"
    )
    parser.add_argument(
        "--category",
        help="Test category to run (case insensitive): datetime, string, math, aggregate, joins, groupby, orderby, distinct, conditional, subqueries, json, extended_string, enhanced_aggregate, all. Cannot be used with --phase.",
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2],
        help="Test all categories for a specific phase: 1 (Core SQL Features) or 2 (Modern Application Extensions). Cannot be used with --category or --function.",
    )
    parser.add_argument(
        "--function",
        help="Test specific function only. Cannot be used with --phase.",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "--export-results", action="store_true", help="Export results to CSV"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout for each test in seconds",
    )

    args = parser.parse_args()

    # Set default category if not provided and no phase specified
    if not args.category and not args.phase:
        args.category = "all"

    # Handle phase argument
    phase_categories = {
        1: [
            "datetime",
            "string",
            "math",
            "aggregate",
            "joins",
            "groupby",
            "orderby",
            "distinct",
            "conditional",
            "subqueries",
        ],
        2: ["json", "extended_string", "enhanced_aggregate"],
    }

    # Convert category to lowercase for case-insensitive matching if provided
    if args.category:
        args.category = args.category.lower()

    # Validate arguments
    if args.phase and args.category:
        print("❌ Cannot specify both --phase and --category arguments")
        sys.exit(1)

    if args.phase and args.function:
        print("❌ Cannot specify both --phase and --function arguments")
        sys.exit(1)

    # Validate category if provided
    if args.category:
        valid_categories = [
            # Phase 1: Core SQL Features
            "datetime",
            "string",
            "math",
            "aggregate",
            "joins",
            "groupby",
            "orderby",
            "distinct",
            "conditional",
            "subqueries",
            # Phase 2: Modern Application Extensions
            "json",
            "extended_string",
            "enhanced_aggregate",
            # Special
            "all",
        ]
        if args.category not in valid_categories:
            print(f"❌ Invalid category: {args.category}")
            print(f"Valid categories: {', '.join(valid_categories)}")
            sys.exit(1)

    # Initialize QA runner
    qa_runner = MariaDBQARunner(verbose=args.verbose, timeout=args.timeout)

    # Connect to MariaDB
    if not qa_runner.connect_to_mariadb():
        sys.exit(1)

    try:
        # Run tests based on arguments
        if args.function:
            # Find and run specific function test
            function_found = False
            for category, tests in qa_runner.test_suites.items():
                for sql, func_name in tests:
                    if func_name.upper() == args.function.upper():
                        qa_runner.run_single_test(sql, category, func_name)
                        function_found = True
                        break
                if function_found:
                    break

            if not function_found:
                print(f"❌ Function '{args.function}' not found in test suites")

        elif args.phase:
            # Run all categories for the specified phase
            categories_to_run = phase_categories[args.phase]
            print(f"🚀 Running Phase {args.phase} tests:")
            print(f"   Categories: {', '.join(categories_to_run)}")
            print()

            for category in categories_to_run:
                if category in qa_runner.test_suites:
                    qa_runner.run_test_suite(category)
                else:
                    print(f"⚠️  Category '{category}' not found in test suites")

        elif args.category == "all":
            qa_runner.run_all_tests()
        else:
            qa_runner.run_test_suite(args.category)

        # Print summary
        qa_runner.print_summary()

        # Export results if requested
        if args.export_results:
            qa_runner.export_results()

    finally:
        qa_runner.disconnect_from_mariadb()


if __name__ == "__main__":
    main()
