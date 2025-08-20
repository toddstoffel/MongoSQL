"""
CTE (Common Table Expression) Module

This module provides comprehensive support for preprocessing Common Table
Expressions in SQL queries to make them compatible with existing MongoDB
translation infrastructure.

Components:
- CTEPreprocessor: Preprocessing for complex CTEs
- CTEIntegrator: Integration with existing infrastructure

Usage:
    from src.modules.cte import preprocess_cte_if_needed, needs_cte_preprocessing

    # For preprocessing integration
    if needs_cte_preprocessing(sql):
        sql = preprocess_cte_if_needed(sql)
"""

from .cte_preprocessor import CTEPreprocessor
from .cte_integration import (
    CTEIntegrator,
    preprocess_cte_if_needed,
    needs_cte_preprocessing,
    is_cte_query,
)

__all__ = [
    "CTEPreprocessor",
    "CTEIntegrator",
    "preprocess_cte_if_needed",
    "needs_cte_preprocessing",
    "is_cte_query",
]
