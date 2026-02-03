"""
Token tracking service for LLM calls.
Tracks token usage and calculates costs for optimization.
"""
from loguru import logger
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

# Removed lazy import - using direct imports in methods instead


class TokenUsage:
    """Represents token usage for a single LLM call."""
    
    def __init__(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        prompt: Optional[str] = None,
        response: Optional[str] = None
    ):
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens
        # Calculate cost using direct import to avoid circular dependency
        from app.services.complexity_classifier import ComplexityClassifier
        self.cost = ComplexityClassifier.calculate_cost(model, input_tokens, output_tokens)
        self.timestamp = datetime.utcnow().isoformat()
        self.prompt = prompt
        self.response = response
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost": self.cost,
            "timestamp": self.timestamp
        }


class TokenTracker:
    """
    Service for tracking token usage across LLM calls.
    Provides cost tracking and optimization insights.
    """
    
    def __init__(self):
        self.usage_history: List[TokenUsage] = []
        self.query_tokens: Dict[str, List[TokenUsage]] = {}  # query_id -> [TokenUsage]
    
    def track_llm_call(
        self,
        model: str,
        prompt: str,
        response: str,
        query_id: Optional[str] = None
    ) -> TokenUsage:
        """
        Track a single LLM call.
        
        Args:
            model: Model used
            prompt: Input prompt
            response: LLM response
            query_id: Optional query ID for grouping
        
        Returns:
            TokenUsage object
        """
        from app.services.complexity_classifier import ComplexityClassifier
        input_tokens = ComplexityClassifier.estimate_tokens(prompt)
        output_tokens = ComplexityClassifier.estimate_tokens(response)
        
        usage = TokenUsage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            prompt=prompt[:200] if prompt else None,  # Store first 200 chars
            response=response[:200] if response else None
        )
        
        self.usage_history.append(usage)
        
        if query_id:
            if query_id not in self.query_tokens:
                self.query_tokens[query_id] = []
            self.query_tokens[query_id].append(usage)
        
        logger.debug(
            f"Tracked LLM call: {model}, "
            f"tokens: {usage.total_tokens} (in: {input_tokens}, out: {output_tokens}), "
            f"cost: ${usage.cost:.6f}"
        )
        
        return usage
    
    def get_query_cost(self, query_id: str) -> float:
        """Get total cost for a query."""
        if query_id not in self.query_tokens:
            return 0.0
        return sum(usage.cost for usage in self.query_tokens[query_id])
    
    def get_query_tokens(self, query_id: str) -> Dict[str, int]:
        """Get token breakdown for a query."""
        if query_id not in self.query_tokens:
            return {"input": 0, "output": 0, "total": 0}
        
        total_input = sum(u.input_tokens for u in self.query_tokens[query_id])
        total_output = sum(u.output_tokens for u in self.query_tokens[query_id])
        
        return {
            "input": total_input,
            "output": total_output,
            "total": total_input + total_output
        }
    
    def get_total_cost(self) -> float:
        """Get total cost across all tracked calls."""
        return sum(usage.cost for usage in self.usage_history)
    
    def get_total_tokens(self) -> Dict[str, int]:
        """Get total token usage."""
        total_input = sum(u.input_tokens for u in self.usage_history)
        total_output = sum(u.output_tokens for u in self.usage_history)
        
        return {
            "input": total_input,
            "output": total_output,
            "total": total_input + total_output
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        total_cost = self.get_total_cost()
        total_tokens = self.get_total_tokens()
        
        # Model breakdown
        model_usage = {}
        for usage in self.usage_history:
            if usage.model not in model_usage:
                model_usage[usage.model] = {
                    "calls": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            model_usage[usage.model]["calls"] += 1
            model_usage[usage.model]["tokens"] += usage.total_tokens
            model_usage[usage.model]["cost"] += usage.cost
        
        return {
            "total_calls": len(self.usage_history),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "average_cost_per_call": total_cost / len(self.usage_history) if self.usage_history else 0,
            "model_breakdown": model_usage
        }
    
    def clear(self):
        """Clear tracking history."""
        self.usage_history.clear()
        self.query_tokens.clear()
        logger.info("Token tracking history cleared")


# Global token tracker instance
token_tracker = TokenTracker()

