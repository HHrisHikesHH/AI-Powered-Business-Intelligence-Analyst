"""
LLM client for Groq API with support for multiple models.
Provides interface for natural language processing and SQL generation.
Supports intelligent model routing based on query complexity.
Includes token tracking for cost optimization.
"""
from groq import Groq
from loguru import logger
from app.core.config import settings
from app.services.token_tracker import token_tracker
from typing import Optional, Dict, List, Literal, Any
from enum import Enum
import json

groq_client: Optional[Groq] = None


class QueryComplexity(str, Enum):
    """Query complexity levels for model routing."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


def get_groq_client() -> Groq:
    """Get or initialize Groq client."""
    global groq_client
    if groq_client is None:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment variables")
        groq_client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("Groq client initialized successfully")
    return groq_client


class LLMService:
    """
    Service for LLM operations using Groq with multiple model support.
    
    Supports intelligent model routing:
    - Simple queries: llama-3.1-8b-instant (fast, cost-effective)
    - Medium queries: llama-3.3-70b-versatile (balanced)
    - Complex queries: openai/gpt-oss-120b (powerful)
    """
    
    def __init__(self):
        self.client = get_groq_client()
        self.models = {
            QueryComplexity.SIMPLE: settings.LLM_MODEL_SIMPLE,
            QueryComplexity.MEDIUM: settings.LLM_MODEL_MEDIUM,
            QueryComplexity.COMPLEX: settings.LLM_MODEL_COMPLEX,
        }
        self.default_model = settings.LLM_MODEL_DEFAULT
    
    def _select_model(self, complexity: Optional[QueryComplexity] = None) -> str:
        """
        Select appropriate model based on query complexity.
        
        Args:
            complexity: Query complexity level
        
        Returns:
            Model ID to use
        """
        if complexity and complexity in self.models:
            return self.models[complexity]
        return self.default_model
    
    def _estimate_complexity(self, prompt: str, system_prompt: Optional[str] = None) -> QueryComplexity:
        """
        Estimate query complexity based on prompt characteristics.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
        
        Returns:
            Estimated complexity level
        """
        full_text = (system_prompt or "") + " " + prompt
        text_lower = full_text.lower()
        
        # Simple heuristics for complexity estimation
        complex_indicators = [
            "subquery", "cte", "window function", "recursive", "union",
            "multiple tables", "aggregate", "join", "group by", "having",
            "case when", "coalesce", "extract", "date_trunc"
        ]
        
        simple_indicators = [
            "count", "select", "from", "where", "limit", "order by"
        ]
        
        complex_count = sum(1 for indicator in complex_indicators if indicator in text_lower)
        simple_count = sum(1 for indicator in simple_indicators if indicator in text_lower)
        
        # Count potential table references (rough estimate)
        word_count = len(full_text.split())
        
        if complex_count >= 2 or word_count > 100:
            return QueryComplexity.COMPLEX
        elif complex_count >= 1 or word_count > 50:
            return QueryComplexity.MEDIUM
        else:
            return QueryComplexity.SIMPLE
    
    def classify_from_understanding(self, query_understanding: Dict[str, Any]) -> QueryComplexity:
        """
        Classify complexity using query understanding data.
        More accurate than prompt-based estimation.
        
        Args:
            query_understanding: Query understanding output
        
        Returns:
            QueryComplexity level
        """
        from app.services.complexity_classifier import complexity_classifier
        return complexity_classifier.classify_from_understanding(query_understanding)
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: Optional[str] = None,
        complexity: Optional[QueryComplexity] = None,
        auto_select_model: bool = True
    ) -> str:
        """
        Generate text completion using Groq models.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            model: Specific model to use (overrides complexity-based selection)
            complexity: Query complexity level for model selection
            auto_select_model: Automatically select model based on complexity
        
        Returns:
            Generated text response
        """
        try:
            # Select model
            if model:
                selected_model = model
            elif auto_select_model and not complexity:
                complexity = self._estimate_complexity(prompt, system_prompt)
                selected_model = self._select_model(complexity)
                logger.debug(f"Auto-selected model {selected_model} for {complexity.value} query")
            else:
                selected_model = self._select_model(complexity)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Groq API uses max_tokens for all models
            request_params = {
                "model": selected_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            response = self.client.chat.completions.create(**request_params)
            
            logger.debug(f"Used model {selected_model} for completion")
            
            # Extract content safely
            content = response.choices[0].message.content
            if not content:
                logger.warning(f"Empty response from LLM model {selected_model}")
                raise ValueError("LLM returned empty response")
            
            # Track token usage
            try:
                # Try to get actual token counts from response
                input_tokens = getattr(response.usage, 'prompt_tokens', None) or 0
                output_tokens = getattr(response.usage, 'completion_tokens', None) or 0
                
                if input_tokens == 0 or output_tokens == 0:
                    # Fallback to estimation if not available
                    from app.services.complexity_classifier import complexity_classifier
                    input_tokens = complexity_classifier.estimate_tokens(prompt)
                    output_tokens = complexity_classifier.estimate_tokens(content)
                
                # Track usage (query_id will be set by orchestrator if available)
                token_tracker.track_llm_call(
                    model=selected_model,
                    prompt=prompt,
                    response=content
                )
            except Exception as e:
                logger.warning(f"Failed to track token usage: {e}")
            
            return content
        except Exception as e:
            logger.error(f"Error generating LLM completion: {e}")
            raise
    
    async def generate_structured_output(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_schema: Optional[Dict] = None,
        model: Optional[str] = None,
        complexity: Optional[QueryComplexity] = None
    ) -> Dict:
        """
        Generate structured JSON output.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            json_schema: Expected JSON schema (for validation)
            model: Specific model to use
            complexity: Query complexity level
        
        Returns:
            Parsed JSON response
        """
        if json_schema:
            schema_str = json.dumps(json_schema, indent=2)
            enhanced_prompt = f"{prompt}\n\nRespond with valid JSON matching this schema:\n{schema_str}"
        else:
            enhanced_prompt = f"{prompt}\n\nRespond with valid JSON only."
        
        response = await self.generate_completion(
            prompt=enhanced_prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for structured output
            model=model,
            complexity=complexity
        )
        
        try:
            # Extract JSON from response (might have markdown code blocks)
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")


llm_service = LLMService()

