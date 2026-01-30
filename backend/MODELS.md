# LLM Models Configuration Guide

This document explains the available Groq models and how to configure intelligent model routing.

## Available Models

### Production Models (Recommended)

These models are stable and recommended for production use:

| Model ID | Speed (t/s) | Price (per 1M tokens) | Context Window | Best For |
|----------|-------------|------------------------|----------------|----------|
| `llama-3.1-8b-instant` | 560 | $0.05/$0.08 | 131,072 | Simple queries, fast responses |
| `llama-3.3-70b-versatile` | 280 | $0.59/$0.79 | 131,072 | Medium complexity, balanced |
| `openai/gpt-oss-20b` | 1000 | $0.075/$0.30 | 131,072 | Fast, good for simple-medium |
| `openai/gpt-oss-120b` | 500 | $0.15/$0.60 | 131,072 | Complex queries, high accuracy |

### Preview Models (Experimental)

These models are available for evaluation but may change:

| Model ID | Speed (t/s) | Price (per 1M tokens) | Context Window | Notes |
|----------|-------------|------------------------|----------------|-------|
| `qwen/qwen3-32b` | 400 | $0.29/$0.59 | 131,072 | Good reasoning capabilities |
| `meta-llama/llama-4-maverick-17b-128e-instruct` | 600 | $0.20/$0.60 | 131,072 | Latest Llama 4 model |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 750 | $0.11/$0.34 | 131,072 | Faster Llama 4 variant |
| `moonshotai/kimi-k2-instruct-0905` | 200 | $1.00/$3.00 | 262,144 | Large context window |

## Intelligent Model Routing

The system automatically selects the appropriate model based on query complexity:

### Simple Queries
- **Model**: `llama-3.1-8b-instant` (default)
- **Characteristics**: Single table, basic filters, simple aggregations
- **Example**: "How many customers do we have?"

### Medium Queries
- **Model**: `llama-3.3-70b-versatile` (default)
- **Characteristics**: 2-3 table joins, aggregations, GROUP BY
- **Example**: "Show me total revenue by product category"

### Complex Queries
- **Model**: `openai/gpt-oss-120b` (default)
- **Characteristics**: Subqueries, CTEs, window functions, 4+ joins
- **Example**: "Find customers who ordered more than the average order value in their city"

## Configuration

Edit `backend/.env` to customize model selection:

```bash
# Simple queries (fast, cost-effective)
LLM_MODEL_SIMPLE=llama-3.1-8b-instant

# Medium queries (balanced)
LLM_MODEL_MEDIUM=llama-3.3-70b-versatile

# Complex queries (powerful)
LLM_MODEL_COMPLEX=openai/gpt-oss-120b

# Default model (used when complexity is not specified)
LLM_MODEL_DEFAULT=llama-3.3-70b-versatile
```

## Cost Optimization Strategy

The intelligent routing system helps optimize costs:

1. **Simple queries** use the cheapest, fastest model (`llama-3.1-8b-instant`)
2. **Medium queries** use a balanced model (`llama-3.3-70b-versatile`)
3. **Complex queries** use the most capable model (`openai/gpt-oss-120b`)

This approach can reduce costs by **60%+** compared to always using the most powerful model.

## Manual Model Selection

You can also manually specify a model in code:

```python
from app.core.llm_client import llm_service

# Use specific model
response = await llm_service.generate_completion(
    prompt="Your query",
    model="llama-3.1-8b-instant"
)

# Force complexity level
from app.core.llm_client import QueryComplexity
response = await llm_service.generate_completion(
    prompt="Your query",
    complexity=QueryComplexity.SIMPLE
)
```

## Model Selection Logic

The system estimates complexity based on:

1. **Keywords**: Presence of complex SQL features (subqueries, CTEs, window functions)
2. **Query length**: Longer queries are more likely to be complex
3. **Table references**: More tables suggest more complex joins

You can override this by:
- Setting `auto_select_model=False` and specifying a model directly
- Providing a `complexity` parameter explicitly

## Testing Models

To test different models, you can:

1. **Temporarily change defaults** in `.env`:
   ```bash
   LLM_MODEL_DEFAULT=openai/gpt-oss-20b
   ```

2. **Use the API** with model parameter (future feature)

3. **Modify query_executor.py** to use a specific model:
   ```python
   sql = await self.llm.generate_completion(
       prompt=prompt,
       system_prompt=system_prompt,
       model="llama-3.1-8b-instant"  # Force specific model
   )
   ```

## Rate Limits

Be aware of rate limits for each model:

- **Developer Plan**: 
  - `llama-3.1-8b-instant`: 250K TPM, 1K RPM
  - `llama-3.3-70b-versatile`: 300K TPM, 1K RPM
  - `openai/gpt-oss-120b`: 250K TPM, 1K RPM

The system will automatically handle rate limit errors and may retry with a different model if configured.

## Recommendations

### For Development
- Use `llama-3.1-8b-instant` as default (fast, cheap)
- Switch to `llama-3.3-70b-versatile` for testing complex queries

### For Production
- Use intelligent routing (default behavior)
- Monitor costs and adjust model assignments based on usage patterns
- Consider using `openai/gpt-oss-20b` for simple queries if you need faster responses

### For High-Volume Applications
- Prefer `llama-3.1-8b-instant` for most queries
- Reserve `openai/gpt-oss-120b` only for truly complex queries
- Monitor query patterns and adjust complexity thresholds

## Getting Model Information

You can list all available models using the Groq API:

```python
from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
models = client.models.list()
print(models)
```

Or via curl:
```bash
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"
```

## Troubleshooting

### Model not found error
- Verify the model ID is correct (check available models)
- Ensure your API key has access to the model
- Some models may be preview-only and require special access

### Rate limit errors
- The system will automatically retry
- Consider using a different model for that complexity level
- Check your Groq account limits

### Poor SQL generation
- Try a more powerful model for that complexity level
- Adjust the complexity estimation logic
- Provide better schema context in the system prompt

