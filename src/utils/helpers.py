"""
Utility functions for the MongoSQL translator
"""

import re
from typing import Any, Dict, List, Optional, Union


def process_function_argument(arg: Any) -> Any:
    """Process function argument, converting field references to MongoDB syntax"""
    if isinstance(arg, dict) and "type" in arg:
        if arg["type"] == "literal":
            # It's a quoted string literal, return the value as-is
            return arg["value"]
        elif arg["type"] == "field_reference":
            # It's an unquoted field reference, convert to MongoDB field syntax
            return f"${arg['value']}"

    # For backward compatibility and other types (numbers, None, etc.)
    return arg


def format_mongodb_query(query: Dict[str, Any]) -> str:
    """Format MongoDB query for display"""
    operation = query.get("operation", "unknown")
    collection = query.get("collection", "collection")

    if operation == "find":
        filter_doc = query.get("filter", {})
        projection = query.get("projection")

        result = f"db.{collection}.find({_format_dict(filter_doc)}"
        if projection:
            result += f", {_format_dict(projection)}"
        result += ")"

        if query.get("sort"):
            sort_dict = dict(query["sort"])
            result += f".sort({_format_dict(sort_dict)})"

        if query.get("skip"):
            result += f".skip({query['skip']})"

        if query.get("limit"):
            result += f".limit({query['limit']})"

        return result

    elif operation == "insert_one":
        document = query.get("document", {})
        return f"db.{collection}.insertOne({_format_dict(document)})"

    elif operation == "insert_many":
        documents = query.get("documents", [])
        return f"db.{collection}.insertMany({_format_list(documents)})"

    elif operation in ["update_one", "update_many"]:
        filter_doc = query.get("filter", {})
        update_doc = query.get("update", {})
        method = "updateOne" if operation == "update_one" else "updateMany"
        return f"db.{collection}.{method}({_format_dict(filter_doc)}, {_format_dict(update_doc)})"

    elif operation in ["delete_one", "delete_many"]:
        filter_doc = query.get("filter", {})
        method = "deleteOne" if operation == "delete_one" else "deleteMany"
        return f"db.{collection}.{method}({_format_dict(filter_doc)})"

    elif operation == "aggregate":
        pipeline = query.get("pipeline", [])
        return f"db.{collection}.aggregate({_format_list(pipeline)})"

    else:
        return str(query)


def _format_dict(d: Dict[str, Any]) -> str:
    """Format dictionary for MongoDB query display"""
    if not d:
        return "{}"

    items = []
    for key, value in d.items():
        formatted_value = _format_value(value)
        items.append(f'"{key}": {formatted_value}')

    return "{" + ", ".join(items) + "}"


def _format_list(lst: List[Any]) -> str:
    """Format list for MongoDB query display"""
    if not lst:
        return "[]"

    items = [_format_value(item) for item in lst]
    return "[" + ", ".join(items) + "]"


def _format_value(value: Any) -> str:
    """Format value for MongoDB query display"""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, dict):
        return _format_dict(value)
    elif isinstance(value, list):
        return _format_list(value)
    else:
        return str(value)


def validate_connection_params(host: str, port: int, database: str) -> List[str]:
    """Validate MongoDB connection parameters"""
    errors = []

    if not host or not host.strip():
        errors.append("Host is required")

    if not isinstance(port, int) or port <= 0 or port > 65535:
        errors.append("Port must be a valid integer between 1 and 65535")

    if not database or not database.strip():
        errors.append("Database name is required")
    elif not is_valid_mongodb_name(database):
        errors.append("Database name contains invalid characters")

    return errors


def is_valid_mongodb_name(name: str) -> bool:
    """Check if a name is valid for MongoDB collection/database"""
    if not name:
        return False

    # MongoDB names cannot contain certain characters
    invalid_chars = ["/", "\\", ".", '"', "*", "<", ">", ":", "|", "?"]
    for char in invalid_chars:
        if char in name:
            return False

    # Cannot start with space or certain characters
    if name.startswith(" ") or name.startswith("system."):
        return False

    return True


def escape_regex_chars(text: str) -> str:
    """Escape special regex characters for MongoDB regex queries"""
    # Escape special regex characters except for % and _ which are SQL wildcards
    special_chars = [
        ".",
        "^",
        "$",
        "*",
        "+",
        "?",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        "|",
        "\\",
    ]

    for char in special_chars:
        text = text.replace(char, "\\" + char)

    return text


def sql_like_to_regex(pattern: str) -> str:
    """Convert SQL LIKE pattern to MongoDB regex pattern"""
    # Escape special regex characters first
    escaped = escape_regex_chars(pattern)

    # Convert SQL wildcards to regex
    # % matches any sequence of characters
    escaped = escaped.replace("%", ".*")

    # _ matches any single character
    escaped = escaped.replace("_", ".")

    return escaped


def parse_sql_value(value: str) -> Any:
    """Parse SQL value string to appropriate Python type"""
    if not value:
        return None

    value = value.strip()

    # Handle NULL
    if value.upper() == "NULL":
        return None

    # Handle boolean
    if value.upper() in ["TRUE", "FALSE"]:
        return value.upper() == "TRUE"

    # Handle quoted strings
    if (value.startswith("'") and value.endswith("'")) or (
        value.startswith('"') and value.endswith('"')
    ):
        return value[1:-1]

    # Handle numbers
    try:
        if "." in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        pass

    # Return as string
    return value


def build_aggregation_pipeline(select_parts: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build MongoDB aggregation pipeline from SELECT components"""
    pipeline = []

    # Add $match stage for WHERE clause
    if select_parts.get("where"):
        match_stage = {"$match": select_parts["where"]}
        pipeline.append(match_stage)

    # Add $group stage for GROUP BY
    if select_parts.get("group_by"):
        group_stage = {"$group": {"_id": {}}}

        # Handle GROUP BY fields
        for field in select_parts["group_by"]:
            group_stage["$group"]["_id"][field] = f"${field}"

        # Handle aggregate functions in SELECT
        for col in select_parts.get("columns", []):
            if isinstance(col, dict) and col.get("function"):
                func_name = col["function"].upper()
                field_name = col.get("field", "_count")

                if func_name == "COUNT":
                    group_stage["$group"][field_name] = {"$sum": 1}
                elif func_name in ["SUM", "AVG", "MIN", "MAX"]:
                    mongo_func = f"${func_name.lower()}"
                    target_field = col.get("target_field", field_name)
                    group_stage["$group"][field_name] = {mongo_func: f"${target_field}"}

        pipeline.append(group_stage)

    # Add $sort stage for ORDER BY
    if select_parts.get("order_by"):
        sort_dict = {}
        for order_item in select_parts["order_by"]:
            direction = 1 if order_item["direction"] == "ASC" else -1
            sort_dict[order_item["field"]] = direction

        pipeline.append({"$sort": sort_dict})

    # Add $skip stage for OFFSET
    if select_parts.get("skip"):
        pipeline.append({"$skip": select_parts["skip"]})

    # Add $limit stage for LIMIT
    if select_parts.get("limit"):
        pipeline.append({"$limit": select_parts["limit"]})

    # Add $project stage for column selection
    if select_parts.get("projection"):
        pipeline.append({"$project": select_parts["projection"]})

    return pipeline


def get_mongodb_error_message(error: Exception) -> str:
    """Extract meaningful error message from MongoDB exception"""
    error_str = str(error)

    # Common MongoDB error patterns
    if "Authentication failed" in error_str:
        return "Authentication failed. Please check your username and password."
    elif "connection refused" in error_str.lower():
        return "Connection refused. Please check if MongoDB is running and accessible."
    elif "timeout" in error_str.lower():
        return "Connection timeout. Please check your network connection and MongoDB server."
    elif "name resolution" in error_str.lower():
        return "Cannot resolve hostname. Please check the MongoDB host address."
    elif "collection" in error_str.lower() and "not found" in error_str.lower():
        return "Collection not found. Please check the collection name."
    elif "database" in error_str.lower() and "not found" in error_str.lower():
        return "Database not found. Please check the database name."
    else:
        return f"MongoDB error: {error_str}"
