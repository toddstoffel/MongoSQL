# MariaDB Subqueries: Types and Execution Order

## Summary

MariaDB subqueries are nested SQL queries within other SQL statements that can reside in the WHERE clause, FROM clause, or SELECT clause. A subquery, additionally known as an inner question or nested query, is a query nested within every other SQL statement. MariaDB provides several optimization strategies including subquery materialization, semi-join optimizations, and subquery cache for correlated subqueries.

## Types of Subqueries

### 1. Scalar Subqueries

Scalar subqueries must return a single value and are commonly used in the SELECT clause with aggregate functions such as SUM, COUNT, MIN, MAX, or AVG. The trick to placing a subquery in the SELECT clause is that the subquery must return a single value.

**Example:**
```sql
SELECT customer_name, 
       (SELECT AVG(order_amount) FROM orders WHERE customer_id = customers.id) AS avg_order
FROM customers;
```

### 2. Row Subqueries

A row subquery returns a single row of data. These are used when you need to compare multiple columns against a single row result.

**Example:**
```sql
SELECT * FROM employees 
WHERE (department_id, salary) = (SELECT department_id, MAX(salary) 
                                FROM employees 
                                WHERE department = 'Engineering');
```

### 3. Table Subqueries (Derived Tables)

Subqueries in the FROM clause are commonly called derived tables. If a subquery is used in this way, you must also use an AS clause to name the result of the subquery.

**Example:**
```sql
SELECT sites.site_name, subquery1.total_size 
FROM sites, 
     (SELECT site_name, SUM(file_size) AS total_size 
      FROM pages 
      GROUP BY site_name) subquery1 
WHERE subquery1.site_name = sites.site_name;
```

### 4. Correlated Subqueries

Correlated subqueries depend on values from the outer query, making them dynamic and highly effective for solving complex database problems. The goal of the subquery cache is to optimize the evaluation of correlated subqueries by storing results together with correlation parameters.

**Example:**
```sql
SELECT customer_name 
FROM customers c1 
WHERE EXISTS (SELECT 1 FROM orders o 
              WHERE o.customer_id = c1.customer_id 
              AND o.order_date > '2024-01-01');
```

### 5. Subqueries with IN/EXISTS/ANY/ALL

#### IN Subqueries
IN subqueries allow you to find values that match any value returned by the subquery.

```sql
SELECT site_id, site_name 
FROM sites 
WHERE site_id IN (SELECT site_id FROM pages WHERE file_size > 89);
```

#### EXISTS Subqueries
MariaDB 5.3 introduced EXISTS-to-IN optimization, converting EXISTS subqueries into IN subqueries when possible to use advanced IN optimizations.

#### ALL Subqueries
Subqueries using the ALL keyword will return true if the comparison returns true for each row returned by the subquery, or the subquery returns no rows.

```sql
SELECT * FROM table1 
WHERE column1 > ALL (SELECT column1 FROM table2);
```

## Execution Order and Optimization Strategies

### Basic Execution Flow

1. **Outer Query Initialization**: The outer query begins processing
2. **Subquery Evaluation**: Depending on the type:
   - **Non-correlated**: Executed once before the outer query
   - **Correlated**: Executed for each row of the outer query
3. **Result Integration**: Subquery results are used by the outer query

### MariaDB Optimization Strategies

#### 1. Subquery Materialization
The basic idea of subquery materialization is to execute the subquery and store its result in an internal temporary table indexed on all its columns. If the size of the temporary table is less than the tmp_table_size system variable, the table is a hash-indexed in-memory HEAP table.

#### 2. Semi-join Optimizations
MariaDB has a set of optimizations specifically targeted at semi-join subqueries. A subquery can quite often, but not in all cases, be rewritten as a JOIN.

#### 3. EXISTS-to-IN Conversion
MariaDB converts EXISTS subqueries into IN subqueries when the correlation is trivial, allowing the use of materialization strategy. The optimization is controlled by the exists_to_in flag in optimizer_switch and has been ON by default since MariaDB 10.0.12.

#### 4. Subquery Cache
The subquery cache optimizes correlated subqueries by storing results together with correlation parameters in a cache and avoiding re-execution when the result is already cached. Every subquery cache creates a temporary table where the results and all parameters are stored with a unique index over all parameters.

### Performance Considerations

#### Subquery vs JOIN Performance
Subqueries that can be rewritten as a LEFT JOIN are sometimes more efficient. However, there are some scenarios which call for subqueries rather than joins: When you want duplicates, but not false duplicates.

#### Optimization Limitations
Due to some technical limitations in the MariaDB server, there are few cases when the server cannot apply materialization optimization, such as when BLOB fields are involved.

### Execution Order Examples

#### Non-Correlated Subquery Execution
```sql
SELECT * FROM customers 
WHERE customer_id IN (SELECT customer_id FROM orders WHERE total > 1000);
```

**Execution Order:**
1. Execute inner subquery: `SELECT customer_id FROM orders WHERE total > 1000`
2. Materialize results if beneficial
3. Execute outer query using IN optimization against materialized results

#### Correlated Subquery Execution
```sql
SELECT * FROM customers c 
WHERE EXISTS (SELECT 1 FROM orders o 
              WHERE o.customer_id = c.customer_id);
```

**Execution Order:**
1. Start outer query scan of customers table
2. For each customer row, execute subquery with current customer_id
3. Use subquery cache if the same parameter combination was seen before
4. Return row if EXISTS condition is met

## Configuration Parameters

### Key Variables
- **optimizer_switch**: Controls various optimization strategies including `subquery_cache`, `exists_to_in`
- **tmp_table_size**: Influences size of in-memory temporary tables for materialization
- **max_heap_table_size**: Works with tmp_table_size to determine memory limits

### Monitoring Subquery Performance
MariaDB provides status variables for monitoring subquery cache performance: Subquery_cache_hit and Subquery_cache_miss.

## References

1. [Subqueries | MariaDB Documentation](https://mariadb.com/kb/en/subqueries/)
2. [Subqueries in MariaDB: A Comprehensive Guide](https://runebook.dev/en/articles/mariadb/subqueries-in-a-from-clause/index)
3. [MariaDB: Subqueries](https://www.techonthenet.com/mariadb/subqueries.php)
4. [MariaDB Subqueries - GeeksforGeeks](https://www.geeksforgeeks.org/mariadb/mariadb-subqueries/)
5. [Non-semi-join Subquery Optimizations - MariaDB Knowledge Base](https://mariadb.com/kb/en/non-semi-join-subquery-optimizations/)
6. [Subquery Cache | MariaDB Documentation](https://mariadb.com/kb/en/subquery-cache/)
7. [EXISTS-to-IN Optimization - MariaDB Knowledge Base](https://mariadb.com/kb/en/exists-to-in-optimization/)
8. [Subqueries and JOINs | MariaDB Documentation](https://mariadb.com/kb/en/subqueries-and-joins/)
9. [Subqueries in a FROM Clause (Derived Tables) | MariaDB Documentation](https://mariadb.com/kb/en/subqueries-in-a-from-clause-derived-tables/)
10. [Subqueries and ALL | MariaDB Documentation](https://mariadb.com/docs/server/reference/sql-statements/data-manipulation/selecting-data/joins-subqueries/subqueries/subqueries-and-all)