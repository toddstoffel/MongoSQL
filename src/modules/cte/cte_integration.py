"""
CTE Integration Module

This module provides CTE preprocessing capabilities that can be integrated
into the existing query processing pipeline without modifying core files.
"""

from .cte_preprocessor import CTEPreprocessor


class CTEIntegrator:
    """Integrates CTE preprocessing with existing query pipeline"""

    def __init__(self):
        """Initialize CTE integrator"""
        self.preprocessor = CTEPreprocessor()

    def can_handle(self, sql: str) -> bool:
        """Check if this integrator can handle the SQL query"""
        return self.preprocessor.needs_preprocessing(sql)

    def preprocess_sql(self, sql: str) -> str:
        """Preprocess SQL to make it compatible with existing infrastructure"""
        return self.preprocessor.preprocess(sql)

    def is_basic_cte(self, sql: str) -> bool:
        """Check if this is a basic CTE that existing system can handle"""
        return (
            sql.upper().strip().startswith("WITH")
            and not self.preprocessor.has_multiple_ctes(sql)
            and not self.preprocessor.has_recursive_cte(sql)
        )


# Global instance for easy integration
cte_integrator = CTEIntegrator()


def preprocess_cte_if_needed(sql: str) -> str:
    """
    Main function for CTE preprocessing

    This function can be called from the CLI or other entry points
    to preprocess CTE queries before they reach the core parser.
    """
    if cte_integrator.can_handle(sql):
        return cte_integrator.preprocess_sql(sql)
    return sql


def needs_cte_preprocessing(sql: str) -> bool:
    """Check if SQL needs CTE preprocessing"""
    return cte_integrator.can_handle(sql)


def is_cte_query(sql: str) -> bool:
    """Check if SQL is any kind of CTE query"""
    return sql.upper().strip().startswith("WITH")
