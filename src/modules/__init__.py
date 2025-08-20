"""
SQL Clause Modules

This package contains specialized modules for parsing and translating
different SQL clauses and operations.

Each module follows the pattern:
- {module}_parser.py: Token-based parsing
- {module}_translator.py: MongoDB translation
- {module}_types.py: Type definitions

Phase 1 Modules (Core SQL):
- conditional: IF, CASE, COALESCE, NULLIF functions
- where: WHERE clause operations
- joins: JOIN operations
- groupby: GROUP BY operations
- orderby: ORDER BY operations
- subqueries: All subquery patterns
- reserved_words: MariaDB reserved word handling

Phase 2 Modules (Modern Extensions):
- regexp: REGEXP/RLIKE infix operations
- extended_string: Advanced string functions
- enhanced_aggregate: Statistical and bitwise aggregates
- json: JSON manipulation functions

Phase 3 Modules (Enterprise Extensions):
- cte: Common Table Expression preprocessing
"""

# Phase 1 Core Modules
from . import conditional
from . import where
from . import joins
from . import groupby
from . import orderby
from . import subqueries
from . import reserved_words

# Phase 2 Modern Extensions
from . import regexp
from . import extended_string
from . import enhanced_aggregate
from . import json

# Phase 3 Enterprise Extensions
from . import cte
from . import encryption

__all__ = [
    # Phase 1 Core
    "conditional",
    "where",
    "joins",
    "groupby",
    "orderby",
    "subqueries",
    "reserved_words",
    # Phase 2 Modern
    "regexp",
    "extended_string",
    "enhanced_aggregate",
    "json",
    # Phase 3 Enterprise
    "cte",
    "encryption",
]
