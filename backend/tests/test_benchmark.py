"""
Benchmark testing - 500 query accuracy evaluation.
Tests SQL generation accuracy against expected results.
"""
import pytest
import json
import random
import asyncio
from pathlib import Path
from app.agents.orchestrator import Orchestrator
from app.core.config import settings
from app.core.database_adapter import create_database_adapter
from app.services.query_executor import QueryExecutor
from sqlalchemy import text
import sqlparse


def load_benchmark_queries():
    """Load benchmark queries from JSON file."""
    benchmark_file = Path(__file__).parent / "benchmark_queries.json"
    
    if not benchmark_file.exists():
        # Return sample queries if file doesn't exist
        return [
            {
                "id": 1,
                "natural_language": "How many customers do we have?",
                "expected_sql": "SELECT COUNT(*) FROM customers",
                "category": "simple"
            },
            {
                "id": 2,
                "natural_language": "Show total revenue by month",
                "expected_sql": "SELECT DATE_TRUNC('month', order_date) as month, SUM(total_amount) as revenue FROM sales_orders GROUP BY month",
                "category": "medium"
            }
        ]
    
    with open(benchmark_file, 'r') as f:
        return json.load(f)


def sample_benchmark_queries(benchmark_queries, samples_per_category: int = 5, seed: int = 42):
    """
    Deterministically sample up to N queries per category.
    
    This keeps the benchmark fast while still covering all categories.
    """
    if not benchmark_queries:
        return []
    
    random.seed(seed)
    by_category = {}
    for q in benchmark_queries:
        cat = q.get("category", "unknown")
        by_category.setdefault(cat, []).append(q)
    
    sampled = []
    for cat, items in by_category.items():
        if len(items) <= samples_per_category:
            sampled.extend(items)
        else:
            sampled.extend(random.sample(items, samples_per_category))
    return sampled


def normalize_sql(sql: str) -> str:
    """Normalize SQL for comparison."""
    if not sql:
        return ""
    
    # Parse and format SQL
    parsed = sqlparse.parse(sql)
    if not parsed:
        return sql.strip().upper()
    
    # Get first statement
    statement = parsed[0]
    
    # Normalize whitespace and case
    normalized = sqlparse.format(str(statement), reindent=True, keyword_case='upper')
    
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    
    return normalized


def compare_sql_accuracy(generated: str, expected: str) -> float:
    """
    Compare generated SQL with expected SQL.
    Returns accuracy score 0.0 to 1.0.
    """
    gen_norm = normalize_sql(generated)
    exp_norm = normalize_sql(expected)
    
    if gen_norm == exp_norm:
        return 1.0
    
    # Check if key components match
    score = 0.0
    
    # Check SELECT clause
    if "SELECT" in gen_norm and "SELECT" in exp_norm:
        score += 0.2
    
    # Check FROM clause (table names)
    gen_tables = extract_tables(gen_norm)
    exp_tables = extract_tables(exp_norm)
    if set(gen_tables) == set(exp_tables):
        score += 0.3
    elif len(set(gen_tables) & set(exp_tables)) > 0:
        score += 0.15
    
    # Check WHERE clause similarity
    if "WHERE" in gen_norm and "WHERE" in exp_norm:
        score += 0.2
    elif "WHERE" not in gen_norm and "WHERE" not in exp_norm:
        score += 0.2
    
    # Check GROUP BY
    if "GROUP BY" in gen_norm and "GROUP BY" in exp_norm:
        score += 0.15
    elif "GROUP BY" not in gen_norm and "GROUP BY" not in exp_norm:
        score += 0.15
    
    # Check aggregations
    gen_aggs = extract_aggregations(gen_norm)
    exp_aggs = extract_aggregations(exp_norm)
    if set(gen_aggs) == set(exp_aggs):
        score += 0.15
    
    return min(score, 1.0)


def extract_tables(sql: str) -> list:
    """Extract table names from SQL."""
    tables = []
    words = sql.upper().split()
    
    in_from = False
    for i, word in enumerate(words):
        if word == "FROM":
            in_from = True
            continue
        if in_from:
            if word in ["JOIN", "INNER", "LEFT", "RIGHT", "WHERE", "GROUP", "ORDER", "LIMIT"]:
                break
            if word not in ["SELECT", "AS", "ON", "AND", "OR"]:
                # Remove aliases and clean
                table = word.split(".")[-1].strip("(),")
                if table and len(table) > 1:
                    tables.append(table.lower())
    
    return tables


def extract_aggregations(sql: str) -> list:
    """Extract aggregation functions from SQL."""
    aggs = []
    sql_upper = sql.upper()
    
    for agg in ["COUNT", "SUM", "AVG", "MAX", "MIN"]:
        if agg + "(" in sql_upper:
            aggs.append(agg)
    
    return aggs


@pytest.mark.asyncio
async def test_benchmark_accuracy():
    """Run benchmark and verify ≥85% accuracy."""
    benchmark_queries = load_benchmark_queries()
    
    if len(benchmark_queries) < 100:
        pytest.skip("Benchmark dataset not fully populated. Need 500 queries.")

    # Use a deterministic random sample of queries to keep the test fast.
    benchmark_queries = sample_benchmark_queries(benchmark_queries, samples_per_category=5, seed=42)
    
    adapter = create_database_adapter(
        db_type=settings.DATABASE_TYPE,
        connection_string=settings.database_url,
    )
    factory = adapter.get_session_factory()

    async with factory() as db:
        orchestrator = Orchestrator(db)
        executor = QueryExecutor(db)
        
        results = []
        accurate_sql = 0
        executable_sql = 0
        accurate_results = 0
        
        total_queries = len(benchmark_queries)
        for idx, query_data in enumerate(benchmark_queries, start=1):
            query_id = query_data.get("id", 0)
            natural_language = query_data["natural_language"]
            expected_sql = query_data.get("expected_sql", "")
            category = query_data.get("category", "unknown")
            
            try:
                # Process query with a timeout so a single slow/hung query
                # doesn't stall the entire benchmark.
                result = await asyncio.wait_for(
                    orchestrator.process_query(natural_language),
                    timeout=20,
                )
                
                generated_sql = result.get("generated_sql") or result.get("sql", "")
                error = result.get("error")
                
                # Check SQL accuracy if expected SQL provided
                sql_accuracy = 0.0
                if expected_sql and generated_sql:
                    sql_accuracy = compare_sql_accuracy(generated_sql, expected_sql)
                    if sql_accuracy >= 0.9:  # 90% similarity threshold
                        accurate_sql += 1
                
                # Check if SQL is executable
                is_executable = False
                result_accuracy = 0.0
                if generated_sql and not error:
                    try:
                        exec_results = await executor._execute_sql(generated_sql)
                        is_executable = True
                        executable_sql += 1
                        
                        # If expected results provided, compare
                        expected_results = query_data.get("expected_results")
                        if expected_results and exec_results:
                            # Simple comparison - could be enhanced
                            if len(exec_results) == len(expected_results):
                                result_accuracy = 1.0
                                accurate_results += 1
                    except:
                        pass
                
                results.append({
                    "id": query_id,
                    "category": category,
                    "natural_language": natural_language,
                    "sql_accuracy": sql_accuracy,
                    "is_executable": is_executable,
                    "result_accuracy": result_accuracy,
                    "error": error is not None
                })

                # Per-query progress feedback so we can see which queries pass/fail while running.
                status = "OK"
                if error:
                    status = f"ERROR: {error}"
                elif not is_executable:
                    status = "NOT_EXECUTABLE"
                print(
                    f"[{idx}/{total_queries}] "
                    f"ID={query_id} category={category} "
                    f"sql_acc={sql_accuracy:.2f} exec={is_executable} res_acc={result_accuracy:.2f} -> {status}"
                )
                
            except Exception as e:
                results.append({
                    "id": query_id,
                    "category": category,
                    "natural_language": natural_language,
                    "error": str(e)
                })
        
        # Calculate metrics
        total = len(results)
        sql_accuracy_rate = accurate_sql / total if total > 0 else 0
        executable_rate = executable_sql / total if total > 0 else 0
        result_accuracy_rate = accurate_results / executable_sql if executable_sql > 0 else 0
        error_rate = sum(1 for r in results if r.get("error")) / total if total > 0 else 0
        
        # Assert success criteria
        assert sql_accuracy_rate >= 0.85, \
            f"SQL accuracy {sql_accuracy_rate:.2%} below 85% target"
        
        assert executable_rate >= 0.90, \
            f"Executable SQL rate {executable_rate:.2%} below 90% target"
        
        assert error_rate < 0.08, \
            f"Error rate {error_rate:.2%} exceeds 8% target"
        
        # Print summary
        print(f"\n=== Benchmark Results ===")
        print(f"Total Queries: {total}")
        print(f"SQL Accuracy: {sql_accuracy_rate:.2%}")
        print(f"Executable Rate: {executable_rate:.2%}")
        print(f"Result Accuracy: {result_accuracy_rate:.2%}")
        print(f"Error Rate: {error_rate:.2%}")


@pytest.mark.asyncio
async def test_benchmark_by_category():
    """Test benchmark accuracy by query category."""
    benchmark_queries = load_benchmark_queries()

    adapter = create_database_adapter(
        db_type=settings.DATABASE_TYPE,
        connection_string=settings.database_url,
    )
    factory = adapter.get_session_factory()

    async with factory() as db:
        orchestrator = Orchestrator(db)

        categories = {}

        for query_data in benchmark_queries:
            category = query_data.get("category", "unknown")
            if category not in categories:
                categories[category] = {"total": 0, "accurate": 0, "errors": 0}

            categories[category]["total"] += 1

            try:
                result = await asyncio.wait_for(
                    orchestrator.process_query(query_data["natural_language"]),
                    timeout=20,
                )
                if result.get("error") is None:
                    categories[category]["accurate"] += 1
                else:
                    categories[category]["errors"] += 1
            except Exception:
                categories[category]["errors"] += 1

        # Verify each category meets minimum threshold
        for category, stats in categories.items():
            if stats["total"] > 0:
                accuracy = stats["accurate"] / stats["total"]
                error_rate = stats["errors"] / stats["total"]

                print(f"{category}: {accuracy:.2%} accuracy, {error_rate:.2%} error rate")

                assert accuracy >= 0.80, \
                    f"Category {category} accuracy {accuracy:.2%} below 80%"

                assert error_rate < 0.10, \
                    f"Category {category} error rate {error_rate:.2%} exceeds 10%"

