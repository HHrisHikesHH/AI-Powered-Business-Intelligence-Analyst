"""
Error handling and categorization service.
Provides comprehensive error logging, categorization, and retry strategies.
"""
from enum import Enum
from typing import Dict, Optional, List, Any
from loguru import logger
from datetime import datetime
import json
import traceback
import re


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    SYNTAX_ERROR = "syntax_error"
    SCHEMA_ERROR = "schema_error"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT_ERROR = "timeout_error"
    EXECUTION_ERROR = "execution_error"
    VALIDATION_ERROR = "validation_error"
    LLM_ERROR = "llm_error"
    EMPTY_RESULTS = "empty_results"
    UNEXPECTED_RESULTS = "unexpected_results"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetryStrategy(str, Enum):
    """Retry strategies for error recovery."""
    SELF_CORRECT_SQL = "self_correct_sql"
    AUGMENT_SCHEMA_CONTEXT = "augment_schema_context"
    OPTIMIZE_QUERY = "optimize_query"
    RETRY_EXECUTION = "retry_execution"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    CHECK_INTENT = "check_intent"


class ErrorHandler:
    """Handles error categorization, logging, and retry strategies."""
    
    def __init__(self):
        self.error_log: List[Dict[str, Any]] = []
    
    def categorize_error(self, error: Exception, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Categorize an error and determine retry strategy.
        
        Args:
            error: Exception that occurred
            context: Additional context (SQL, query, step, etc.)
        
        Returns:
            Dictionary with error categorization and retry information
        """
        raw_error_str = str(error)
        error_str = raw_error_str.lower()
        error_type = type(error).__name__
        
        # Determine category
        category = ErrorCategory.UNKNOWN_ERROR
        severity = ErrorSeverity.MEDIUM
        retryable = False
        retry_strategy = None
        user_message: Optional[str] = None
        
        # Syntax errors
        if any(keyword in error_str for keyword in ["syntax", "parse", "invalid sql", "malformed"]):
            category = ErrorCategory.SYNTAX_ERROR
            severity = ErrorSeverity.MEDIUM
            retryable = True
            retry_strategy = RetryStrategy.SELF_CORRECT_SQL
        
        # Schema errors (missing table/column)
        elif any(keyword in error_str for keyword in ["does not exist", "relation", "column", "table"]):
            category = ErrorCategory.SCHEMA_ERROR
            severity = ErrorSeverity.MEDIUM
            retryable = True
            retry_strategy = RetryStrategy.AUGMENT_SCHEMA_CONTEXT
            # Try to extract a missing column name for a clearer user-facing message
            col_match = re.search(r'column \"([^\"]+)\" does not exist', error_str)
            if col_match:
                missing_col = col_match.group(1)
                user_message = (
                    f"The query references column '{missing_col}', which does not exist in the current "
                    "database schema. This question cannot be answered given the available data."
                )
            else:
                user_message = (
                    "The query references a table or column that does not exist in the current database "
                    "schema. This question cannot be answered given the available data."
                )
        
        # Permission errors
        elif any(keyword in error_str for keyword in ["permission", "access denied", "unauthorized"]):
            category = ErrorCategory.PERMISSION_ERROR
            severity = ErrorSeverity.HIGH
            retryable = False
        
        # Timeout errors
        elif any(keyword in error_str for keyword in ["timeout", "timed out", "exceeded"]):
            category = ErrorCategory.TIMEOUT_ERROR
            severity = ErrorSeverity.MEDIUM
            retryable = True
            retry_strategy = RetryStrategy.OPTIMIZE_QUERY
        
        # Execution errors
        elif any(keyword in error_str for keyword in ["execution", "failed to execute", "database error"]):
            category = ErrorCategory.EXECUTION_ERROR
            severity = ErrorSeverity.MEDIUM
            retryable = True
            retry_strategy = RetryStrategy.RETRY_EXECUTION
        
        # Validation errors
        elif any(keyword in error_str for keyword in ["validation", "invalid", "not allowed"]):
            category = ErrorCategory.VALIDATION_ERROR
            severity = ErrorSeverity.MEDIUM
            retryable = True
            retry_strategy = RetryStrategy.SELF_CORRECT_SQL
        
        # LLM errors
        elif any(keyword in error_str for keyword in ["llm", "api", "model", "groq", "rate limit"]):
            category = ErrorCategory.LLM_ERROR
            severity = ErrorSeverity.MEDIUM
            retryable = True
            retry_strategy = RetryStrategy.RETRY_WITH_BACKOFF
        
        # Empty results (not really an error, but needs handling)
        elif "empty" in error_str or "no results" in error_str:
            category = ErrorCategory.EMPTY_RESULTS
            severity = ErrorSeverity.LOW
            retryable = True
            retry_strategy = RetryStrategy.CHECK_INTENT
        
        # Network errors
        elif any(keyword in error_str for keyword in ["connection", "network", "unreachable", "refused"]):
            category = ErrorCategory.NETWORK_ERROR
            severity = ErrorSeverity.HIGH
            retryable = True
            retry_strategy = RetryStrategy.RETRY_WITH_BACKOFF
        
        error_info = {
            "category": category.value,
            "severity": severity.value,
            "error_type": error_type,
            "error_message": raw_error_str,
            # Prefer a simplified, user-friendly message when available
            "user_message": user_message or raw_error_str,
            "retryable": retryable,
            "retry_strategy": retry_strategy.value if retry_strategy else None,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
            "traceback": traceback.format_exc()
        }
        
        # Log error
        self.log_error(error_info)
        
        return error_info
    
    def log_error(self, error_info: Dict[str, Any]):
        """
        Log error with comprehensive details.
        
        Args:
            error_info: Error information dictionary
        """
        category = error_info["category"]
        severity = error_info["severity"]
        error_msg = error_info["error_message"]
        
        # Add to error log
        self.error_log.append(error_info)
        
        # Log based on severity
        if severity == ErrorSeverity.CRITICAL.value:
            logger.critical(
                f"[{category}] {error_msg}",
                extra={
                    "error_category": category,
                    "error_severity": severity,
                    "retryable": error_info.get("retryable", False),
                    "context": error_info.get("context", {})
                }
            )
        elif severity == ErrorSeverity.HIGH.value:
            logger.error(
                f"[{category}] {error_msg}",
                extra={
                    "error_category": category,
                    "error_severity": severity,
                    "retryable": error_info.get("retryable", False),
                    "context": error_info.get("context", {})
                }
            )
        elif severity == ErrorSeverity.MEDIUM.value:
            logger.warning(
                f"[{category}] {error_msg}",
                extra={
                    "error_category": category,
                    "error_severity": severity,
                    "retryable": error_info.get("retryable", False),
                    "context": error_info.get("context", {})
                }
            )
        else:
            logger.info(
                f"[{category}] {error_msg}",
                extra={
                    "error_category": category,
                    "error_severity": severity,
                    "retryable": error_info.get("retryable", False),
                    "context": error_info.get("context", {})
                }
            )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get statistics about errors encountered."""
        if not self.error_log:
            return {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {},
                "retryable_count": 0
            }
        
        by_category = {}
        by_severity = {}
        retryable_count = 0
        
        for error in self.error_log:
            category = error["category"]
            severity = error["severity"]
            
            by_category[category] = by_category.get(category, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            if error.get("retryable", False):
                retryable_count += 1
        
        return {
            "total_errors": len(self.error_log),
            "by_category": by_category,
            "by_severity": by_severity,
            "retryable_count": retryable_count,
            "retryable_percentage": (retryable_count / len(self.error_log) * 100) if self.error_log else 0
        }
    
    def clear_log(self):
        """Clear the error log."""
        self.error_log.clear()


# Global error handler instance
error_handler = ErrorHandler()

