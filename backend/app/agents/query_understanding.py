"""
Query Understanding Agent.
Parses natural language queries and extracts intent, tables, columns, filters, etc.
Uses caching to improve performance.
"""
from loguru import logger
from app.core.llm_client import llm_service, QueryComplexity
from app.core.redis_client import cache_service
from app.agents.prompts import format_query_understanding_prompt
from typing import Dict, Any, Optional
import json
import hashlib


class QueryUnderstandingAgent:
    """Agent responsible for understanding natural language queries."""
    
    def __init__(self):
        self.llm = llm_service
    
    async def understand(self, query: str) -> Dict[str, Any]:
        """
        Understand a natural language query and extract structured information.
        
        Args:
            query: Natural language query string
        
        Returns:
            Dictionary with:
            - intent: Description of user intent
            - tables: List of required table names
            - columns: List of required column names
            - filters: List of filter conditions
            - aggregations: List of aggregation functions
            - group_by: List of columns for GROUP BY
            - order_by: Ordering specification
            - limit: Row limit
            - ambiguities: List of ambiguous aspects
            - needs_clarification: Boolean indicating if clarification is needed
        """
        try:
            logger.info(f"Understanding query: {query}")
            
            # Check cache first
            cache_key = f"query_understanding:{hashlib.md5(query.encode()).hexdigest()}"
            cached = await cache_service.get(cache_key)
            if cached:
                logger.info("Using cached query understanding")
                return cached
            
            # Format prompt
            prompt = format_query_understanding_prompt(query)
            
            # Use simple model for query understanding (fast, cost-effective)
            response = await self.llm.generate_completion(
                prompt=prompt,
                system_prompt="You are a Query Understanding Agent. Return only valid JSON.",
                temperature=0.2,  # Low temperature for consistent structured output
                max_tokens=500,
                complexity=QueryComplexity.SIMPLE,
                auto_select_model=True
            )
            
            # Parse JSON response
            try:
                # Clean up response (remove markdown if present)
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                elif response.startswith("```"):
                    response = response[3:]
                if response.endswith("```"):
                    response = response[:-3]
                response = response.strip()
                
                understanding = json.loads(response)
                
                # Validate required fields
                required_fields = ["intent", "tables", "columns", "filters", "aggregations"]
                for field in required_fields:
                    if field not in understanding:
                        understanding[field] = [] if field != "intent" else ""
                
                # Ensure optional fields have defaults
                understanding.setdefault("group_by", [])
                understanding.setdefault("order_by", None)
                understanding.setdefault("limit", None)
                understanding.setdefault("ambiguities", [])
                understanding.setdefault("needs_clarification", False)
                
                logger.info(f"Query understood: {understanding['intent']}, tables: {understanding['tables']}")
                
                # Cache for 24 hours
                await cache_service.set(cache_key, understanding, ttl=86400)
                
                return understanding
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse query understanding response: {e}")
                logger.error(f"Response was: {response}")
                # Return a fallback understanding
                return self._create_fallback_understanding(query)
                
        except Exception as e:
            logger.error(f"Error in query understanding: {e}")
            return self._create_fallback_understanding(query)
    
    def _create_fallback_understanding(self, query: str) -> Dict[str, Any]:
        """
        Create a fallback understanding when LLM parsing fails.
        Uses simple heuristics to extract basic information.
        
        CRITICAL: Do NOT default to any table. If we can't identify a valid table,
        return empty tables list to prevent hallucination.
        """
        query_lower = query.lower()
        
        # Simple table detection - only match if we're confident
        tables = []
        if "customer" in query_lower:
            tables.append("customers")
        if "product" in query_lower:
            tables.append("products")
        if "order" in query_lower and "item" not in query_lower:
            tables.append("orders")
        if "order_item" in query_lower or "order item" in query_lower:
            tables.append("order_items")
        
        # CRITICAL FIX: Do NOT default to customers table
        # If we can't identify a table, return empty list
        # This will cause grounding to fail properly instead of hallucinating
        
        return {
            "intent": query,
            "tables": tables,  # Empty if no match - this is correct behavior
            "columns": [],
            "filters": [],
            "aggregations": ["COUNT"] if "how many" in query_lower or "count" in query_lower else [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": ["Failed to parse query - using fallback heuristics. No valid tables identified."] if not tables else ["Failed to parse query - using fallback heuristics"],
            "needs_clarification": True
        }

