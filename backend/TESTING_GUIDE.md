# Testing Guide - Analysis and Visualization Agents

This guide explains how to test the new Analysis and Visualization agents to ensure they're working correctly.

## Quick Start Testing

### 1. Run Unit Tests

Test individual agents in isolation:

```bash
cd backend
source venv/bin/activate

# Test all agents
pytest tests/test_agents.py -v

# Test specific agents
pytest tests/test_agents.py::test_analysis_agent -v
pytest tests/test_agents.py::test_visualization_agent -v
pytest tests/test_agents.py::test_analysis_agent_empty_results -v
pytest tests/test_agents.py::test_visualization_agent_empty_results -v
```

### 2. Run Integration Tests

Test the full orchestrator pipeline:

```bash
pytest tests/test_orchestrator.py -v
```

### 3. Run Verification Script

Verify all agents are properly integrated:

```bash
python verify_agents.py
```

## Manual API Testing

### Start the Backend Server

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Test with cURL

#### Test 1: Simple Count Query (Should generate analysis and visualization)

```bash
curl -X POST http://localhost:8001/api/v1/queries/ \
  -H "Content-Type: application/json" \
  -d '{"query": "How many customers do we have?"}' | jq
```

**Expected Response:**
- `sql`: Generated SQL query
- `results`: Query results array
- `analysis`: Object with `insights`, `trends`, `anomalies`, `recommendations`, `summary`
- `visualization`: Object with `chart_type`, `recharts_component`, `data_key`, `category_key`, etc.

#### Test 2: Group By Query (Should generate bar chart visualization)

```bash
curl -X POST http://localhost:8001/api/v1/queries/ \
  -H "Content-Type: application/json" \
  -d '{"query": "How many products are in each category?"}' | jq
```

**Expected Response:**
- `visualization.chart_type`: Should be "bar" or "pie"
- `visualization.category_key`: Should be "category"
- `visualization.data_key`: Should be "product_count" or similar

#### Test 3: Time Series Query (Should generate line chart)

```bash
curl -X POST http://localhost:8001/api/v1/queries/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me orders by date"}' | jq
```

**Expected Response:**
- `visualization.chart_type`: Should be "line" or "area"
- `analysis.trends`: Should contain trend information

#### Test 4: Empty Results Query (Should handle gracefully)

```bash
curl -X POST http://localhost:8001/api/v1/queries/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me customers created in 2025"}' | jq
```

**Expected Response:**
- `results`: Empty array
- `analysis.anomalies`: Should indicate zero results
- `analysis.recommendations`: Should suggest adjusting filters

## Python Testing Script

Create a comprehensive test script:

```python
# test_new_features.py
import asyncio
import httpx
import json

async def test_query(query: str):
    """Test a query and verify analysis/visualization are present."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/v1/queries/",
            json={"query": query},
            timeout=60.0
        )
        return response.json()

async def main():
    test_queries = [
        "How many customers do we have?",
        "What's the total revenue from orders?",
        "How many products are in each category?",
        "Show me the most expensive products",
        "List customers by city"
    ]
    
    print("=" * 80)
    print("Testing Analysis and Visualization Agents")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: {query}")
        print("-" * 80)
        
        try:
            result = await test_query(query)
            
            # Check required fields
            assert "sql" in result, "Missing SQL"
            assert "results" in result, "Missing results"
            assert "analysis" in result, "Missing analysis"
            assert "visualization" in result, "Missing visualization"
            
            # Check analysis structure
            analysis = result.get("analysis", {})
            assert "insights" in analysis, "Analysis missing insights"
            assert "summary" in analysis, "Analysis missing summary"
            
            # Check visualization structure
            viz = result.get("visualization", {})
            assert "chart_type" in viz, "Visualization missing chart_type"
            assert "recharts_component" in viz, "Visualization missing recharts_component"
            
            print(f"   ✅ SQL: {result['sql'][:60]}...")
            print(f"   ✅ Results: {len(result['results'])} rows")
            print(f"   ✅ Analysis: {len(analysis.get('insights', []))} insights")
            print(f"   ✅ Visualization: {viz.get('chart_type')} chart")
            
        except AssertionError as e:
            print(f"   ❌ FAILED: {e}")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("Testing Complete")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
cd backend
source venv/bin/activate
python test_new_features.py
```

## Verification Checklist

### Analysis Agent Tests

- [ ] **Insights Generation**: Analysis contains `insights` array with at least one insight
- [ ] **Summary Generation**: Analysis contains `summary` string
- [ ] **Trends Detection**: For time-series queries, `trends` array is populated
- [ ] **Anomaly Detection**: For unusual data, `anomalies` array is populated
- [ ] **Recommendations**: Analysis contains `recommendations` array
- [ ] **Empty Results**: Handles empty results gracefully with appropriate messages

### Visualization Agent Tests

- [ ] **Chart Type Selection**: Correct chart type selected (bar, line, pie, etc.)
- [ ] **Recharts Component**: `recharts_component` matches chart type
- [ ] **Data Keys**: `data_key` and `category_key` are correctly identified
- [ ] **Configuration**: Chart config includes width, height, margins
- [ ] **Colors**: Color scheme is provided
- [ ] **Empty Results**: Handles empty results with appropriate fallback

### Integration Tests

- [ ] **Orchestrator Flow**: All agents execute in correct order
- [ ] **Error Handling**: Analysis/Visualization failures don't break pipeline
- [ ] **API Response**: Response includes all required fields
- [ ] **Caching**: Results are cached correctly with analysis/visualization

## Debugging Tips

### Check Logs

```bash
# Watch logs in real-time
tail -f logs/app.log

# Or if using uvicorn
# Logs will appear in terminal
```

### Test Individual Agents

```python
# test_individual_agent.py
import asyncio
from app.agents.analysis import AnalysisAgent
from app.agents.visualization import VisualizationAgent

async def test_analysis():
    agent = AnalysisAgent()
    query_understanding = {
        "intent": "Count customers",
        "tables": ["customers"],
        "aggregations": ["COUNT"]
    }
    results = [{"customer_count": 20}]
    
    analysis = await agent.analyze_results(
        query_understanding=query_understanding,
        natural_language_query="How many customers?",
        sql="SELECT COUNT(*) as customer_count FROM customers;",
        results=results
    )
    
    print("Analysis Result:")
    print(json.dumps(analysis, indent=2))

async def test_visualization():
    agent = VisualizationAgent()
    query_understanding = {
        "intent": "Show products by category",
        "tables": ["products"],
        "group_by": ["category"]
    }
    results = [
        {"category": "Electronics", "count": 10},
        {"category": "Clothing", "count": 5}
    ]
    
    viz = await agent.generate_visualization(
        query_understanding=query_understanding,
        natural_language_query="Show products by category",
        sql="SELECT category, COUNT(*) as count FROM products GROUP BY category;",
        results=results
    )
    
    print("Visualization Result:")
    print(json.dumps(viz, indent=2))

if __name__ == "__main__":
    asyncio.run(test_analysis())
    asyncio.run(test_visualization())
```

### Common Issues

1. **Analysis returns empty insights**
   - Check LLM API key is set
   - Check model availability (openai/gpt-oss-120b)
   - Review logs for LLM errors

2. **Visualization returns wrong chart type**
   - Check data structure analysis
   - Verify query understanding includes correct metadata
   - Review visualization agent logs

3. **Agents not being called**
   - Verify orchestrator workflow includes analyze/visualize nodes
   - Check orchestrator logs for execution flow
   - Ensure no errors in earlier pipeline steps

## Performance Testing

### Measure Execution Time

```python
import time
import asyncio
from app.agents.orchestrator import Orchestrator
from unittest.mock import AsyncMock

async def test_performance():
    mock_db = AsyncMock()
    orchestrator = Orchestrator(mock_db)
    
    start = time.time()
    result = await orchestrator.process_query("How many customers do we have?")
    elapsed = time.time() - start
    
    print(f"Total time: {elapsed:.2f}s")
    print(f"Analysis present: {result.get('analysis') is not None}")
    print(f"Visualization present: {result.get('visualization') is not None}")
```

## Expected Results

### Successful Query Response Structure

```json
{
  "query_id": "uuid",
  "natural_language_query": "How many customers do we have?",
  "generated_sql": "SELECT COUNT(*) as customer_count FROM customers;",
  "results": [{"customer_count": 20}],
  "analysis": {
    "insights": ["Total customer count is 20"],
    "trends": [],
    "anomalies": [],
    "recommendations": ["Monitor customer growth"],
    "summary": "The query returned a customer count of 20."
  },
  "visualization": {
    "chart_type": "bar",
    "recharts_component": "BarChart",
    "data_key": "customer_count",
    "category_key": "",
    "title": "Customer Count",
    "config": {
      "width": 800,
      "height": 400,
      "margin": {"top": 20, "right": 30, "left": 20, "bottom": 5}
    }
  },
  "error": null,
  "execution_time_ms": 1234.56
}
```

## Error Analysis Report Template

### Running Error Analysis

```bash
cd backend
source venv/bin/activate
pytest tests/test_comprehensive_queries.py::test_all_query_categories -v -s
```

### Error Analysis Report Format

```markdown
# Error Analysis Report

**Date:** [Date]
**Test Duration:** [Duration]
**Total Queries:** [Number]

## Summary

- **Success Rate:** [Percentage]% (Target: ≥85%)
- **Total Errors:** [Number]
- **Retryable Errors:** [Number] ([Percentage]%)
- **Non-Retryable Errors:** [Number] ([Percentage]%)

## Error Breakdown by Category

| Category | Count | Percentage | Retryable | Strategy |
|----------|-------|------------|------------|----------|
| Syntax Error | [N] | [%] | Yes | Self-correction |
| Schema Error | [N] | [%] | Yes | Context augmentation |
| Timeout Error | [N] | [%] | Yes | Query optimization |
| Execution Error | [N] | [%] | Yes | Retry with backoff |
| Empty Results | [N] | [%] | Yes | Intent check |
| Permission Error | [N] | [%] | No | No retry |
| LLM Error | [N] | [%] | Yes | Retry with backoff |
| Network Error | [N] | [%] | Yes | Retry with backoff |
| Unknown Error | [N] | [%] | [Yes/No] | Default strategy |

## Error Breakdown by Severity

| Severity | Count | Percentage |
|----------|-------|------------|
| Low | [N] | [%] |
| Medium | [N] | [%] |
| High | [N] | [%] |
| Critical | [N] | [%] |

## Retry Statistics

- **Total Retries:** [Number]
- **Successful After Retry:** [Number] ([Percentage]%)
- **Average Retries per Failed Query:** [Number]
- **Max Retries Reached:** [Number] queries

## Query Category Performance

| Category | Total | Successful | Failed | Success Rate |
|----------|-------|------------|--------|--------------|
| Simple | [N] | [N] | [N] | [%] |
| Filtering | [N] | [N] | [N] | [%] |
| Aggregation | [N] | [N] | [N] | [%] |
| Group By | [N] | [N] | [N] | [%] |
| Joins | [N] | [N] | [N] | [%] |
| Complex | [N] | [N] | [N] | [%] |
| Ambiguous | [N] | [N] | [N] | [%] |
| Edge Cases | [N] | [N] | [N] | [%] |
| Time-based | [N] | [N] | [N] | [%] |
| Sorting | [N] | [N] | [N] | [%] |

## Top Error Patterns

1. **[Error Pattern 1]:** [Count] occurrences
   - Common causes: [List]
   - Resolution: [Strategy]

2. **[Error Pattern 2]:** [Count] occurrences
   - Common causes: [List]
   - Resolution: [Strategy]

3. **[Error Pattern 3]:** [Count] occurrences
   - Common causes: [List]
   - Resolution: [Strategy]

## Recommendations

1. **Immediate Actions:**
   - [Action 1]
   - [Action 2]

2. **Improvements:**
   - [Improvement 1]
   - [Improvement 2]

3. **Monitoring:**
   - Track [Metric 1]
   - Alert on [Condition]

## Self-Correction Effectiveness

- **Self-Correction Attempts:** [Number]
- **Successful Corrections:** [Number] ([Percentage]%)
- **Most Corrected Error Type:** [Type]

## Hybrid RAG Performance

- **Vector Search Results:** [Average per query]
- **Keyword Search Results:** [Average per query]
- **Graph-Based Results:** [Average per query]
- **Combined Results:** [Average per query]
- **RAG Context Quality:** [Rating: Good/Fair/Poor]

## Next Steps

If all tests pass:
- ✅ Features are working correctly
- ✅ Ready for production use
- ✅ Can proceed with frontend integration

If tests fail:
- Review error messages in logs
- Check LLM API connectivity
- Verify database schema
- Review agent implementation
- Analyze error patterns and adjust strategies
```

### Generating Error Analysis Report

Create a script to generate the report:

```python
# generate_error_report.py
import asyncio
from app.services.error_handler import error_handler
from app.agents.orchestrator import Orchestrator
from tests.test_comprehensive_queries import TEST_QUERIES
from unittest.mock import AsyncMock, MagicMock

async def generate_report():
    # Run tests and collect statistics
    # ... (implementation)
    
    # Generate markdown report
    # ... (implementation)
    
    print("Error analysis report generated: error_analysis_report.md")

if __name__ == "__main__":
    asyncio.run(generate_report())
```

## Testing Error Handling Features

### Test Retry Logic

```bash
# Test exponential backoff
pytest tests/test_error_handling.py::test_retry_logic_exponential_backoff -v

# Test self-correction
pytest tests/test_error_handling.py::test_self_correction_syntax_error -v
pytest tests/test_error_handling.py::test_self_correction_schema_error -v

# Test error categorization
pytest tests/test_error_handling.py::test_error_categorization -v

# Test fallback strategies
pytest tests/test_error_handling.py::test_fallback_strategies -v
```

### Test Hybrid RAG

```bash
# Test vector search
pytest tests/test_hybrid_rag.py::test_hybrid_rag_vector_search -v

# Test keyword search
pytest tests/test_hybrid_rag.py::test_hybrid_rag_keyword_search -v

# Test graph-based retrieval
pytest tests/test_hybrid_rag.py::test_hybrid_rag_graph_retrieval -v

# Test result combination
pytest tests/test_hybrid_rag.py::test_hybrid_rag_combine_results -v
```

### Test Comprehensive Query Suite

```bash
# Test all query categories
pytest tests/test_comprehensive_queries.py -v

# Test specific category
pytest tests/test_comprehensive_queries.py::test_simple_queries -v
pytest tests/test_comprehensive_queries.py::test_complex_queries -v
pytest tests/test_comprehensive_queries.py::test_ambiguous_queries -v
```

## Performance Benchmarks

### Expected Performance Metrics

- **Average Query Time:** <2 seconds (p95)
- **Success Rate:** ≥85%
- **Retry Rate:** <15%
- **Self-Correction Success Rate:** ≥60%
- **Error Rate:** <15%

### Monitoring Commands

```bash
# Check error statistics
python -c "from app.services.error_handler import error_handler; import json; print(json.dumps(error_handler.get_error_statistics(), indent=2))"

# Check retry counts
grep "retry_count" logs/app.log | tail -20

# Check error categories
grep "error_category" logs/app.log | tail -20
```

