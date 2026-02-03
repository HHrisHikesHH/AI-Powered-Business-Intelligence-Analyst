"""
Fallback strategies for different error types.
Provides intelligent recovery mechanisms for common failure modes.
"""
from typing import Dict, Any, Optional, List
from loguru import logger
from app.services.error_handler import ErrorCategory, RetryStrategy
from app.agents.analysis import AnalysisAgent


class FallbackStrategies:
    """Provides fallback strategies for different error scenarios."""
    
    def __init__(self, analysis_agent: Optional[AnalysisAgent] = None):
        self.analysis_agent = analysis_agent or AnalysisAgent()
    
    async def handle_syntax_error(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str,
        previous_sql: str,
        error_message: str
    ) -> Dict[str, Any]:
        """
        Handle syntax errors by requesting SQL correction.
        
        Args:
            query_understanding: Query understanding output
            natural_language_query: Original query
            previous_sql: SQL that failed
            error_message: Syntax error message
        
        Returns:
            Strategy information for retry
        """
        logger.info("Handling syntax error with self-correction")
        return {
            "strategy": RetryStrategy.SELF_CORRECT_SQL.value,
            "action": "Re-invoke SQL agent with error message and request correction",
            "retryable": True,
            "max_retries": 3
        }
    
    async def handle_schema_error(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str,
        previous_sql: str,
        error_message: str
    ) -> Dict[str, Any]:
        """
        Handle schema errors (missing table/column) by augmenting context.
        
        Args:
            query_understanding: Query understanding output
            natural_language_query: Original query
            previous_sql: SQL that failed
            error_message: Schema error message
        
        Returns:
            Strategy information for retry
        """
        logger.info("Handling schema error with context augmentation")
        return {
            "strategy": RetryStrategy.AUGMENT_SCHEMA_CONTEXT.value,
            "action": "Augment context with correct schema and retry",
            "retryable": True,
            "max_retries": 3
        }
    
    async def handle_empty_results(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str,
        sql: str,
        results: List[Dict]
    ) -> Dict[str, Any]:
        """
        Handle empty results by checking if query intent was misunderstood.
        
        Args:
            query_understanding: Query understanding output
            natural_language_query: Original query
            sql: Executed SQL
            results: Empty results
        
        Returns:
            Strategy information with suggestions
        """
        logger.info("Handling empty results - checking intent mismatch")
        
        try:
            # Ask Analysis Agent if query intent was likely misunderstood
            analysis = await self.analysis_agent.analyze_results(
                query_understanding=query_understanding,
                natural_language_query=natural_language_query,
                sql=sql,
                results=results
            )
            
            recommendations = analysis.get("recommendations", [])
            anomalies = analysis.get("anomalies", [])
            
            return {
                "strategy": RetryStrategy.CHECK_INTENT.value,
                "action": "Query returned zero results - may indicate intent mismatch",
                "retryable": True,
                "suggestions": recommendations,
                "anomalies": anomalies,
                "max_retries": 1  # Only one retry for empty results
            }
        except Exception as e:
            logger.warning(f"Error analyzing empty results: {e}")
            return {
                "strategy": RetryStrategy.CHECK_INTENT.value,
                "action": "Query returned zero results",
                "retryable": False,
                "suggestions": [
                    "Review the query filters - they may be too restrictive",
                    "Verify that the data exists in the database for the specified criteria"
                ]
            }
    
    async def handle_timeout_error(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str,
        sql: str,
        timeout_seconds: int
    ) -> Dict[str, Any]:
        """
        Handle timeout errors by suggesting query optimization.
        
        Args:
            query_understanding: Query understanding output
            natural_language_query: Original query
            sql: SQL that timed out
            timeout_seconds: Timeout value
        
        Returns:
            Strategy information with optimization suggestions
        """
        logger.info(f"Handling timeout error (>{timeout_seconds}s)")
        
        suggestions = [
            "Consider adding indexes on frequently queried columns",
            "Reduce date range or filter scope",
            "Add LIMIT clause to reduce result set size",
            "Break complex query into smaller sub-queries"
        ]
        
        return {
            "strategy": RetryStrategy.OPTIMIZE_QUERY.value,
            "action": f"Query exceeded timeout of {timeout_seconds}s",
            "retryable": True,
            "suggestions": suggestions,
            "max_retries": 2
        }
    
    async def handle_permission_error(
        self,
        error_message: str
    ) -> Dict[str, Any]:
        """
        Handle permission errors (non-retryable).
        
        Args:
            error_message: Permission error message
        
        Returns:
            Strategy information
        """
        logger.error("Permission error detected - non-retryable")
        return {
            "strategy": RetryStrategy.NO_RETRY.value,
            "action": "Permission denied - check database user permissions",
            "retryable": False,
            "suggestions": [
                "Verify database user has SELECT permissions on required tables",
                "Check table-level and column-level permissions"
            ]
        }
    
    async def get_fallback_strategy(
        self,
        error_category: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get appropriate fallback strategy based on error category.
        
        Args:
            error_category: Error category from ErrorHandler
            context: Context dictionary with query info, SQL, results, etc.
        
        Returns:
            Strategy information
        """
        query_understanding = context.get("query_understanding", {})
        natural_language_query = context.get("natural_language_query", "")
        previous_sql = context.get("sql", "")
        error_message = context.get("error_message", "")
        results = context.get("results", [])
        timeout_seconds = context.get("timeout_seconds", 30)
        
        if error_category == ErrorCategory.SYNTAX_ERROR.value:
            return await self.handle_syntax_error(
                query_understanding, natural_language_query, previous_sql, error_message
            )
        elif error_category == ErrorCategory.SCHEMA_ERROR.value:
            return await self.handle_schema_error(
                query_understanding, natural_language_query, previous_sql, error_message
            )
        elif error_category == ErrorCategory.EMPTY_RESULTS.value:
            return await self.handle_empty_results(
                query_understanding, natural_language_query, previous_sql, results
            )
        elif error_category == ErrorCategory.TIMEOUT_ERROR.value:
            return await self.handle_timeout_error(
                query_understanding, natural_language_query, previous_sql, timeout_seconds
            )
        elif error_category == ErrorCategory.PERMISSION_ERROR.value:
            return await self.handle_permission_error(error_message)
        else:
            # Default strategy
            return {
                "strategy": RetryStrategy.RETRY.value,
                "action": "Retry with exponential backoff",
                "retryable": True,
                "max_retries": 3
            }

