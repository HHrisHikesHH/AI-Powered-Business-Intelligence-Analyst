"""
Enhanced query complexity classification service.
Uses query understanding data for more accurate complexity estimation.
"""
from loguru import logger
from typing import Dict, Any, Optional

# Import QueryComplexity locally to avoid circular import
from enum import Enum

class QueryComplexity(str, Enum):
    """Query complexity levels for model routing."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


# Model pricing (per 1M tokens) - approximate for cost simulation
MODEL_COSTS = {
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "openai/gpt-oss-120b": {"input": 0.15, "output": 0.60},
}


class ComplexityClassifier:
    """
    Enhanced complexity classifier that uses query understanding data
    for more accurate model routing.
    """
    
    MODEL_COSTS = MODEL_COSTS  # Reference to module-level constant
    
    @staticmethod
    def classify_from_understanding(query_understanding: Dict[str, Any]) -> QueryComplexity:
        """
        Classify query complexity based on query understanding data.
        
        Args:
            query_understanding: Query understanding output from QueryUnderstandingAgent
        
        Returns:
            QueryComplexity level
        """
        tables = query_understanding.get("tables", [])
        columns = query_understanding.get("columns", [])
        aggregations = query_understanding.get("aggregations", [])
        group_by = query_understanding.get("group_by", [])
        filters = query_understanding.get("filters", [])
        order_by = query_understanding.get("order_by")
        
        # Complexity scoring
        complexity_score = 0
        
        # Table count (more tables = more complex)
        table_count = len(tables)
        if table_count == 1:
            complexity_score += 0
        elif table_count == 2:
            complexity_score += 1
        elif table_count == 3:
            complexity_score += 2
        else:
            complexity_score += 4  # 4+ tables = complex
        
        # Aggregations (multiple aggregations = more complex)
        aggregation_count = len(aggregations)
        if aggregation_count == 0:
            complexity_score += 0
        elif aggregation_count == 1:
            complexity_score += 0.5
        elif aggregation_count == 2:
            complexity_score += 1
        else:
            complexity_score += 2
        
        # GROUP BY (adds complexity)
        if group_by:
            complexity_score += 1.5
        
        # Complex filters (date ranges, multiple conditions)
        if filters:
            filter_count = len(filters)
            if filter_count > 2:
                complexity_score += 1
            # Check for date/time filters (more complex)
            filter_text = str(filters).lower()
            if any(term in filter_text for term in ["date", "time", "year", "month", "between"]):
                complexity_score += 0.5
        
        # ORDER BY (simple, but adds slight complexity)
        if order_by:
            complexity_score += 0.3
        
        # Column count (more columns = slightly more complex)
        if len(columns) > 5:
            complexity_score += 0.5
        
        # Classification thresholds
        if complexity_score >= 4:
            return QueryComplexity.COMPLEX
        elif complexity_score >= 1.5:
            return QueryComplexity.MEDIUM
        else:
            return QueryComplexity.SIMPLE
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count for a text string.
        Rough approximation: 1 token ≈ 4 characters for English text.
        
        Args:
            text: Text to estimate tokens for
        
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
    
    @staticmethod
    def calculate_cost(
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Calculate estimated cost for LLM call.
        
        Args:
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        
        Returns:
            Estimated cost in USD
        """
        if model not in MODEL_COSTS:
            # Default to medium model pricing
            model = "llama-3.3-70b-versatile"
        
        costs = MODEL_COSTS[model]
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        
        return input_cost + output_cost


complexity_classifier = ComplexityClassifier()

