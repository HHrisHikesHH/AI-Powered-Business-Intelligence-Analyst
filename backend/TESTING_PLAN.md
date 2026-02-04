# Comprehensive Testing Plan
## AI-Powered Business Intelligence Analyst

**Version:** 1.0  
**Date:** February 3, 2026  
**Status:** Production Readiness Testing

---

## Table of Contents

1. [Testing Overview](#1-testing-overview)
2. [Test Categories](#2-test-categories)
3. [Test Execution Strategy](#3-test-execution-strategy)
4. [Test Cases by Component](#4-test-cases-by-component)
5. [Benchmark Testing](#5-benchmark-testing)
6. [Performance Testing](#6-performance-testing)
7. [Test Automation](#7-test-automation)
8. [Success Criteria](#8-success-criteria)

---

## 1. Testing Overview

### 1.1 Testing Objectives

Based on the Technical Specification, we need to verify:

- ✅ **SQL Accuracy**: ≥85% on 500-query benchmark dataset
- ✅ **Latency**: <2 seconds p95 for 90% of queries
- ✅ **Cost Optimization**: <$0.02 average per query, 60% reduction through routing
- ✅ **Error Rate**: <8% failure rate
- ✅ **Cache Hit Rate**: >40% for common queries
- ✅ **Concurrent Users**: Support 50+ users with <2s p95 latency
- ✅ **Multi-Agent System**: All agents working correctly
- ✅ **RAG Functionality**: Hybrid search, schema context retrieval
- ✅ **Database Adapter**: Multi-database support (PostgreSQL, MySQL, SQLite)
- ✅ **Enterprise Schema**: Complex queries on 40+ tables

### 1.2 Testing Scope

**In Scope:**
- Functional correctness of all agents
- SQL generation accuracy
- Query execution and result handling
- Error handling and retry logic
- Cost optimization and model routing
- Performance and scalability
- Database adapter functionality
- Enterprise schema compatibility

**Out of Scope (for now):**
- Infrastructure deployment (AWS/GCP setup)
- Load balancing configuration
- Production monitoring setup (Prometheus/Grafana already scaffolded)
- CI/CD pipeline optimization

---

## 2. Test Categories

### 2.1 Unit Tests
- Individual agent functionality
- SQL validation logic
- Database adapter methods
- Utility functions

### 2.2 Integration Tests
- Multi-agent orchestration
- End-to-end query flow
- Database connection and queries
- RAG retrieval system

### 2.3 Functional Tests
- Natural language to SQL conversion
- Query result accuracy
- Visualization generation
- Analysis insights

### 2.4 Performance Tests
- Latency measurements
- Concurrent user simulation
- Cache effectiveness
- Database query performance

### 2.5 Accuracy Tests
- 500-query benchmark evaluation
- SQL correctness validation
- Result accuracy verification

### 2.6 Error Handling Tests
- Invalid query handling
- SQL error recovery
- Retry logic validation
- Self-correction mechanisms

### 2.7 Security Tests
- SQL injection prevention
- Permission validation
- Dangerous operation blocking
- Input sanitization

---

## 3. Test Execution Strategy

### 3.1 Test Environment Setup

```bash
# 1. Ensure database is populated
cd backend
source venv/bin/activate
PGPASSWORD=postgres psql -h localhost -U postgres -d ai_bi_db -f database/populate_remaining_tables.sql

# 2. Verify data exists
PGPASSWORD=postgres psql -h localhost -U postgres -d ai_bi_db -c "SELECT COUNT(*) FROM customers; SELECT COUNT(*) FROM employees; SELECT COUNT(*) FROM sales_orders;"

# 3. Ensure schema embeddings are generated
python -c "from app.core.database import get_db; from app.services.schema_introspection import ensure_schema_embeddings; import asyncio; asyncio.run(ensure_schema_embeddings(next(get_db().__anext__())))"
```

### 3.2 Test Execution Order

1. **Unit Tests** (Fast, no dependencies)
2. **Integration Tests** (Requires database)
3. **Functional Tests** (Requires full stack)
4. **Performance Tests** (Requires stable environment)
5. **Accuracy Tests** (Final validation)

---

## 4. Test Cases by Component

### 4.1 Database Adapter Tests

**Test File:** `tests/test_database_adapter.py`

#### Test Cases:

1. **Database Connection**
   - ✅ PostgreSQL connection
   - ✅ MySQL connection (if configured)
   - ✅ SQLite connection (if configured)
   - ✅ Connection failure handling

2. **Schema Introspection**
   - ✅ Table discovery (all 40+ tables)
   - ✅ Column metadata retrieval
   - ✅ Foreign key relationship detection
   - ✅ Cross-database compatibility

3. **Query Execution**
   - ✅ Simple SELECT queries
   - ✅ Complex JOIN queries
   - ✅ Aggregation queries
   - ✅ Subqueries and CTEs
   - ✅ Timeout handling
   - ✅ Row limit enforcement

**Expected Results:**
- All database types connect successfully
- All 40+ tables discovered
- All relationships identified
- Queries execute correctly

---

### 4.2 Query Understanding Agent Tests

**Test File:** `tests/test_query_understanding.py`

#### Test Cases:

1. **Simple Queries**
   - "How many customers do we have?"
   - "Show me all employees"
   - "List all products"

2. **Filtered Queries**
   - "Show customers from New York"
   - "Employees hired in 2024"
   - "Products with price > 1000"

3. **Aggregation Queries**
   - "Total revenue by month"
   - "Average salary by department"
   - "Count of orders by status"

4. **Complex Queries**
   - "Top 10 customers by total order value"
   - "Employees with performance rating > 4.0"
   - "Products with low inventory across all warehouses"

5. **Ambiguous Queries**
   - "Show me sales" (needs clarification)
   - "Revenue last year" (which year?)
   - "Best performing employee" (by what metric?)

**Expected Results:**
- Intent correctly extracted
- Tables and columns identified
- Filters, aggregations, grouping detected
- Ambiguities flagged when present

---

### 4.3 SQL Generation Agent Tests

**Test File:** `tests/test_sql_generation.py`

#### Test Cases:

1. **Simple SQL Generation**
   ```sql
   Input: "How many customers?"
   Expected: SELECT COUNT(*) FROM customers;
   ```

2. **JOIN Queries**
   ```sql
   Input: "Show customer names with their order totals"
   Expected: SELECT c.name, SUM(o.total_amount) 
             FROM customers c 
             JOIN sales_orders o ON c.id = o.customer_id 
             GROUP BY c.name;
   ```

3. **Complex Aggregations**
   ```sql
   Input: "Average order value by customer type"
   Expected: SELECT c.customer_type, AVG(o.total_amount) 
             FROM customers c 
             JOIN sales_orders o ON c.id = o.customer_id 
             GROUP BY c.customer_type;
   ```

4. **Time-Based Queries**
   ```sql
   Input: "Sales by month in 2024"
   Expected: SELECT DATE_TRUNC('month', order_date) as month, 
                    SUM(total_amount) as total_sales
             FROM sales_orders 
             WHERE order_date >= '2024-01-01' 
             GROUP BY month;
   ```

5. **Multi-Table Joins**
   ```sql
   Input: "Product sales by category and warehouse"
   Expected: Complex JOIN across products, sales_order_items, 
             sales_orders, inventory, warehouses
   ```

**Expected Results:**
- Syntactically correct SQL
- Semantically correct (matches intent)
- Uses correct table/column names
- Proper JOIN conditions
- Appropriate aggregations

---

### 4.4 SQL Validator Tests

**Test File:** `tests/test_sql_validator.py`

#### Test Cases:

1. **Valid SQL**
   - ✅ Simple SELECT
   - ✅ SELECT with JOINs
   - ✅ SELECT with aggregations
   - ✅ SELECT with subqueries

2. **Invalid SQL - Dangerous Operations**
   - ❌ DELETE statements
   - ❌ DROP TABLE
   - ❌ TRUNCATE
   - ❌ UPDATE without WHERE
   - ❌ ALTER TABLE

3. **Invalid SQL - Syntax Errors**
   - ❌ Missing FROM clause
   - ❌ Invalid column names
   - ❌ Missing table references

4. **Permission Checks**
   - ✅ Valid table access
   - ❌ Non-existent tables
   - ❌ Non-existent columns

5. **Cost Estimation**
   - ✅ Small queries (< 10K rows)
   - ⚠️ Large queries (> 1M rows) - should warn
   - ✅ Queries with LIMIT

**Expected Results:**
- Dangerous operations blocked
- Syntax errors caught
- Permission violations detected
- Large queries flagged

---

### 4.5 Analysis Agent Tests

**Test File:** `tests/test_analysis_agent.py`

#### Test Cases:

1. **Statistical Insights**
   - Mean, median, mode detection
   - Standard deviation calculation
   - Outlier identification

2. **Trend Detection**
   - Time-series trends (increasing/decreasing)
   - Month-over-month changes
   - Year-over-year comparisons

3. **Anomaly Detection**
   - Unusual spikes or drops
   - Data quality issues
   - Missing patterns

4. **Correlation Discovery**
   - Relationship identification
   - Pattern recognition
   - Business insights

5. **Recommendations**
   - Actionable suggestions
   - Business context awareness
   - Data-driven insights

**Expected Results:**
- Insights generated for all result sets
- Trends identified in time-series data
- Anomalies flagged appropriately
- Recommendations are actionable

---

### 4.6 Visualization Agent Tests

**Test File:** `tests/test_visualization_agent.py`

#### Test Cases:

1. **Chart Type Selection**
   - Time-series → Line/Area chart
   - Categorical → Bar/Pie chart
   - Single value → Number card
   - Comparison → Bar chart
   - Distribution → Histogram

2. **Recharts Configuration**
   - Valid chart configs
   - Proper data keys
   - Color schemes
   - Accessibility

3. **Edge Cases**
   - Empty results
   - Single data point
   - Large datasets
   - Missing data

**Expected Results:**
- Appropriate chart types selected
- Valid Recharts configurations
- Handles edge cases gracefully

---

### 4.7 Orchestrator Tests

**Test File:** `tests/test_orchestrator.py`

#### Test Cases:

1. **Simple Query Flow**
   - Query Understanding → SQL Generation → Validation → Execution → Analysis → Visualization

2. **Error Recovery**
   - SQL error → Retry with correction
   - Validation failure → Enhanced context retry
   - Timeout → Query optimization suggestion

3. **Model Routing**
   - Simple query → Haiku/GPT-4o mini
   - Medium query → Sonnet
   - Complex query → Sonnet/Opus

4. **Caching**
   - Identical queries cached
   - Schema embeddings cached
   - Cache invalidation on schema changes

5. **Cost Tracking**
   - Token counting per agent
   - Cost breakdown per query
   - Total cost calculation

**Expected Results:**
- Complete flow works end-to-end
- Errors handled gracefully
- Appropriate models selected
- Caching reduces costs
- Costs tracked accurately

---

### 4.8 RAG System Tests

**Test File:** `tests/test_hybrid_rag.py`

#### Test Cases:

1. **Vector Search**
   - Semantic similarity matching
   - Schema element retrieval
   - Query history retrieval

2. **Keyword Search**
   - Exact table name matching
   - Column name matching
   - BM25 ranking

3. **Graph-Based Retrieval**
   - Related table discovery
   - Foreign key traversal
   - Multi-hop relationships

4. **Hybrid Search**
   - Combined vector + keyword
   - Relevance ranking
   - Context augmentation

**Expected Results:**
- Relevant schema elements retrieved
- Similar queries found
- Related tables discovered
- Context properly augmented

---

### 4.9 Enterprise Schema Tests

**Test File:** `tests/test_enterprise_schema.py`

#### Test Cases:

1. **HR Module Queries**
   - "List all employees by department"
   - "Average salary by job position"
   - "Employees on leave this month"
   - "Performance reviews with rating > 4.0"

2. **Finance Module Queries**
   - "Total revenue by quarter"
   - "Outstanding invoices"
   - "Budget vs actual by department"
   - "General ledger entries for account 4000"

3. **Sales Module Queries**
   - "Top 10 customers by revenue"
   - "Sales pipeline by stage"
   - "Conversion rate from leads to customers"
   - "Average deal size by sales rep"

4. **Inventory Module Queries**
   - "Products below reorder point"
   - "Inventory value by warehouse"
   - "Purchase orders pending receipt"
   - "Inventory movements last 30 days"

5. **Projects Module Queries**
   - "Projects over budget"
   - "Time entries by employee"
   - "Task completion rates"
   - "Billable hours by project"

6. **Cross-Module Queries**
   - "Revenue by customer industry and sales rep department"
   - "Employee performance vs project success"
   - "Support tickets by customer revenue tier"
   - "Marketing campaign ROI by lead source"

**Expected Results:**
- All modules queryable
- Complex JOINs work correctly
- Aggregations accurate
- Cross-module queries successful

---

## 5. Benchmark Testing

### 5.1 500-Query Benchmark Dataset

**Test File:** `tests/benchmark_queries.json`

Create a comprehensive benchmark with 500 queries covering:

#### Query Categories (100 queries each):

1. **Simple Queries (100)**
   - Single table SELECTs
   - Basic filters
   - Simple aggregations

2. **Medium Queries (100)**
   - 2-3 table JOINs
   - GROUP BY aggregations
   - Date range filters

3. **Complex Queries (100)**
   - 4+ table JOINs
   - Subqueries and CTEs
   - Window functions
   - Multiple aggregations

4. **Enterprise Queries (100)**
   - Cross-module queries
   - Complex business logic
   - Multi-level aggregations

5. **Edge Cases (100)**
   - Ambiguous queries
   - Empty result sets
   - Large datasets
   - Unusual patterns

#### Benchmark Execution

```python
# tests/test_benchmark.py
async def test_500_query_benchmark():
    """Run 500-query benchmark and verify ≥85% accuracy."""
    results = []
    for query in benchmark_queries:
        result = await orchestrator.process_query(query["natural_language"])
        accuracy = validate_sql_accuracy(result["sql"], query["expected_sql"])
        results.append(accuracy)
    
    overall_accuracy = sum(results) / len(results)
    assert overall_accuracy >= 0.85, f"Accuracy {overall_accuracy} below 85% target"
```

**Success Criteria:**
- ≥85% SQL accuracy
- ≥90% result accuracy (correct data returned)
- All queries complete without crashes

---

## 6. Performance Testing

### 6.1 Latency Testing

**Test File:** `tests/test_performance.py`

#### Test Cases:

1. **Simple Query Latency**
   - Target: <500ms p95
   - Measure: Query Understanding + SQL Generation + Execution

2. **Medium Query Latency**
   - Target: <1.5s p95
   - Measure: Full pipeline including Analysis

3. **Complex Query Latency**
   - Target: <2s p95
   - Measure: Full pipeline with complex SQL

4. **Cached Query Latency**
   - Target: <100ms p95
   - Measure: Cache hit scenarios

**Execution:**
```python
@pytest.mark.asyncio
async def test_query_latency():
    """Measure query latency across complexity levels."""
    queries = [
        ("simple", "How many customers?"),
        ("medium", "Total revenue by month"),
        ("complex", "Top customers with order details and employee assignments")
    ]
    
    for complexity, query in queries:
        start = time.time()
        result = await orchestrator.process_query(query)
        latency = (time.time() - start) * 1000
        
        assert latency < latency_targets[complexity], \
            f"{complexity} query exceeded latency target"
```

---

### 6.2 Concurrent User Testing

**Test File:** `tests/test_concurrency.py`

#### Test Cases:

1. **10 Concurrent Users**
   - All queries complete successfully
   - No deadlocks or timeouts
   - p95 latency < 2s

2. **50 Concurrent Users**
   - System remains stable
   - p95 latency < 2s
   - Error rate < 8%

3. **100 Concurrent Users (Stress Test)**
   - System degrades gracefully
   - No crashes
   - Errors handled properly

**Execution:**
```python
@pytest.mark.asyncio
async def test_concurrent_users():
    """Test system under concurrent load."""
    async def run_query(query_id):
        result = await orchestrator.process_query(f"Query {query_id}")
        return result
    
    # Simulate 50 concurrent users
    tasks = [run_query(i) for i in range(50)]
    results = await asyncio.gather(*tasks)
    
    success_rate = sum(1 for r in results if r.get("error") is None) / len(results)
    assert success_rate >= 0.92, f"Success rate {success_rate} below 92%"
```

---

### 6.3 Cost Optimization Testing

**Test File:** `tests/test_cost_optimization.py`

#### Test Cases:

1. **Model Routing**
   - Simple queries use Haiku/GPT-4o mini
   - Complex queries use Sonnet
   - Routing decisions logged

2. **Caching Effectiveness**
   - Cache hit rate > 40%
   - Identical queries use cache
   - Schema embeddings cached

3. **Cost per Query**
   - Average < $0.02
   - Simple queries < $0.005
   - Complex queries < $0.05

**Execution:**
```python
@pytest.mark.asyncio
async def test_cost_optimization():
    """Verify cost optimization through routing and caching."""
    costs = []
    cache_hits = 0
    
    for query in test_queries:
        result = await orchestrator.process_query(query)
        cost = result.get("cost_breakdown", {}).get("total_cost", 0)
        costs.append(cost)
        
        if result.get("cached"):
            cache_hits += 1
    
    avg_cost = sum(costs) / len(costs)
    cache_rate = cache_hits / len(test_queries)
    
    assert avg_cost < 0.02, f"Average cost {avg_cost} exceeds $0.02"
    assert cache_rate > 0.40, f"Cache rate {cache_rate} below 40%"
```

---

## 7. Test Automation

### 7.1 Test Suite Structure

```
backend/tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── test_database_adapter.py      # Database adapter tests
├── test_query_understanding.py   # Query Understanding Agent
├── test_sql_generation.py         # SQL Generation Agent
├── test_sql_validator.py          # SQL Validator
├── test_analysis_agent.py         # Analysis Agent
├── test_visualization_agent.py    # Visualization Agent
├── test_orchestrator.py           # Orchestrator integration
├── test_hybrid_rag.py             # RAG system tests
├── test_enterprise_schema.py      # Enterprise schema queries
├── test_benchmark.py              # 500-query benchmark
├── test_performance.py            # Performance tests
├── test_concurrency.py            # Concurrent user tests
├── test_cost_optimization.py     # Cost optimization tests
├── test_error_handling.py         # Error handling tests
├── test_security.py               # Security tests
└── benchmark_queries.json         # 500-query benchmark dataset
```

### 7.2 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run by category
pytest tests/test_database_adapter.py -v
pytest tests/test_agents.py -v
pytest tests/test_orchestrator.py -v
pytest tests/test_enterprise_schema.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run performance tests
pytest tests/test_performance.py -v -m performance

# Run benchmark
pytest tests/test_benchmark.py -v --benchmark
```

### 7.3 Continuous Testing

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v --cov=app
      - name: Run benchmark
        run: pytest tests/test_benchmark.py -v
```

---

## 8. Success Criteria

### 8.1 Quantitative Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| SQL Accuracy | ≥85% | 500-query benchmark |
| Latency (p95) | <2s | Performance tests |
| Cost per Query | <$0.02 | Cost tracking |
| Error Rate | <8% | Error logging |
| Cache Hit Rate | >40% | Cache statistics |
| Concurrent Users | 50+ | Load testing |

### 8.2 Qualitative Criteria

- ✅ All agents function independently
- ✅ Error handling is robust
- ✅ Self-correction works
- ✅ Multi-database support verified
- ✅ Enterprise schema fully queryable
- ✅ Code is well-documented
- ✅ Tests have good coverage (>80%)

### 8.3 Production Readiness Checklist

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] 500-query benchmark ≥85% accuracy
- [ ] Performance targets met
- [ ] Cost optimization verified
- [ ] Error handling tested
- [ ] Security tests passing
- [ ] Database adapter tested (all types)
- [ ] Enterprise schema queries working
- [ ] Documentation complete
- [ ] Code coverage >80%

---

## 9. Test Execution Plan

### Phase 1: Foundation Testing (Week 1)

**Days 1-2: Unit Tests**
- Database adapter tests
- Individual agent tests
- SQL validator tests
- Utility function tests

**Days 3-4: Integration Tests**
- Orchestrator flow tests
- RAG system tests
- Database connection tests

**Days 5-7: Functional Tests**
- End-to-end query tests
- Enterprise schema queries
- Error handling tests

### Phase 2: Advanced Testing (Week 2)

**Days 1-3: Benchmark Testing**
- Create 500-query benchmark
- Run benchmark evaluation
- Analyze accuracy results
- Fix identified issues

**Days 4-5: Performance Testing**
- Latency measurements
- Concurrent user testing
- Cache effectiveness

**Days 6-7: Cost & Security Testing**
- Cost optimization verification
- Security tests
- SQL injection prevention

### Phase 3: Validation & Reporting (Week 3)

**Days 1-3: Final Validation**
- Re-run all tests
- Fix remaining issues
- Verify all success criteria

**Days 4-5: Documentation**
- Test results report
- Performance metrics
- Known issues list

**Days 6-7: Production Readiness Review**
- Final checklist review
- Code review
- Deployment preparation

---

## 10. Test Data Requirements

### 10.1 Database State

- ✅ 40+ tables populated
- ✅ 25,000+ total rows
- ✅ Realistic relationships
- ✅ Multiple data types
- ✅ Time-series data (2020-2025)
- ✅ Various data distributions

### 10.2 Test Queries

**Simple (100 queries):**
- Single table queries
- Basic filters
- Simple aggregations

**Medium (100 queries):**
- 2-3 table JOINs
- GROUP BY queries
- Date range filters

**Complex (100 queries):**
- 4+ table JOINs
- Subqueries
- Window functions

**Enterprise (100 queries):**
- Cross-module queries
- Complex business logic
- Multi-level aggregations

**Edge Cases (100 queries):**
- Ambiguous queries
- Empty results
- Large datasets
- Error scenarios

---

## 11. Test Reporting

### 11.1 Test Results Format

```json
{
  "test_suite": "AI-Powered BI Analyst",
  "date": "2026-02-03",
  "summary": {
    "total_tests": 500,
    "passed": 450,
    "failed": 30,
    "skipped": 20,
    "accuracy": 0.90,
    "avg_latency_ms": 1200,
    "avg_cost_per_query": 0.015,
    "cache_hit_rate": 0.45
  },
  "by_component": {
    "database_adapter": {"passed": 25, "failed": 0},
    "query_understanding": {"passed": 50, "failed": 2},
    "sql_generation": {"passed": 100, "failed": 10},
    "orchestrator": {"passed": 75, "failed": 5}
  },
  "benchmark_results": {
    "total_queries": 500,
    "accurate_sql": 425,
    "accurate_results": 450,
    "sql_accuracy": 0.85,
    "result_accuracy": 0.90
  }
}
```

### 11.2 Performance Metrics Report

- Latency distribution (p50, p95, p99)
- Cost breakdown by agent
- Cache hit/miss rates
- Error rate by category
- Concurrent user performance

---

## 12. Next Steps

1. **Create Test Files** - Implement all test cases
2. **Generate Benchmark Dataset** - Create 500-query benchmark
3. **Set Up Test Infrastructure** - Test database, fixtures, mocks
4. **Run Initial Test Suite** - Baseline measurements
5. **Fix Issues** - Address failures and gaps
6. **Re-run Tests** - Verify fixes
7. **Generate Report** - Document results
8. **Production Readiness Review** - Final validation

---

## Appendix: Quick Test Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_enterprise_schema.py -v

# Run performance tests only
pytest tests/test_performance.py -v -m performance

# Run benchmark
pytest tests/test_benchmark.py -v

# Run with detailed output
pytest tests/ -v -s

# Run failed tests only
pytest tests/ --lf

# Run last failed first
pytest tests/ --ff
```

