"""
Evaluation script for NL-to-SQL pipeline.
Tests 20-30 simple queries and calculates accuracy.
"""
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.agents.orchestrator import Orchestrator
from loguru import logger
from typing import List, Dict
import time


# Test queries with expected SQL patterns
TEST_QUERIES = [
    {
        "query": "How many customers do we have?",
        "expected_tables": ["customers"],
        "expected_keywords": ["COUNT"],
        "category": "aggregation"
    },
    {
        "query": "Show me all products",
        "expected_tables": ["products"],
        "expected_keywords": ["SELECT"],
        "category": "simple_select"
    },
    {
        "query": "List all customers from New York",
        "expected_tables": ["customers"],
        "expected_keywords": ["WHERE", "city"],
        "category": "filter"
    },
    {
        "query": "What's the total revenue from orders?",
        "expected_tables": ["orders"],
        "expected_keywords": ["SUM", "total_amount"],
        "category": "aggregation"
    },
    {
        "query": "Show me products in the Electronics category",
        "expected_tables": ["products"],
        "expected_keywords": ["WHERE", "category"],
        "category": "filter"
    },
    {
        "query": "How many orders were placed?",
        "expected_tables": ["orders"],
        "expected_keywords": ["COUNT"],
        "category": "aggregation"
    },
    {
        "query": "List customers with their email addresses",
        "expected_tables": ["customers"],
        "expected_keywords": ["SELECT", "email"],
        "category": "simple_select"
    },
    {
        "query": "What's the average order value?",
        "expected_tables": ["orders"],
        "expected_keywords": ["AVG", "total_amount"],
        "category": "aggregation"
    },
    {
        "query": "Show me all orders with status 'completed'",
        "expected_tables": ["orders"],
        "expected_keywords": ["WHERE", "status"],
        "category": "filter"
    },
    {
        "query": "How many products are in stock?",
        "expected_tables": ["products"],
        "expected_keywords": ["COUNT"],
        "category": "aggregation"
    },
    {
        "query": "List all products with price less than 100",
        "expected_tables": ["products"],
        "expected_keywords": ["WHERE", "price", "<"],
        "category": "filter"
    },
    {
        "query": "Show me customers from USA",
        "expected_tables": ["customers"],
        "expected_keywords": ["WHERE", "country"],
        "category": "filter"
    },
    {
        "query": "What's the maximum order amount?",
        "expected_tables": ["orders"],
        "expected_keywords": ["MAX", "total_amount"],
        "category": "aggregation"
    },
    {
        "query": "List all order items",
        "expected_tables": ["order_items"],
        "expected_keywords": ["SELECT"],
        "category": "simple_select"
    },
    {
        "query": "Show me products with low stock (less than 10)",
        "expected_tables": ["products"],
        "expected_keywords": ["WHERE", "stock_quantity", "<"],
        "category": "filter"
    },
    {
        "query": "How many orders does each customer have?",
        "expected_tables": ["orders"],
        "expected_keywords": ["COUNT", "GROUP BY", "customer_id"],
        "category": "group_by"
    },
    {
        "query": "What's the total quantity of products ordered?",
        "expected_tables": ["order_items"],
        "expected_keywords": ["SUM", "quantity"],
        "category": "aggregation"
    },
    {
        "query": "List customers ordered by name",
        "expected_tables": ["customers"],
        "expected_keywords": ["ORDER BY", "name"],
        "category": "ordering"
    },
    {
        "query": "Show me the most expensive products",
        "expected_tables": ["products"],
        "expected_keywords": ["ORDER BY", "price", "DESC"],
        "category": "ordering"
    },
    {
        "query": "How many products are in each category?",
        "expected_tables": ["products"],
        "expected_keywords": ["COUNT", "GROUP BY", "category"],
        "category": "group_by"
    },
    {
        "query": "List all pending orders",
        "expected_tables": ["orders"],
        "expected_keywords": ["WHERE", "status"],
        "category": "filter"
    },
    {
        "query": "What's the minimum product price?",
        "expected_tables": ["products"],
        "expected_keywords": ["MIN", "price"],
        "category": "aggregation"
    },
    {
        "query": "Show me customers created in 2024",
        "expected_tables": ["customers"],
        "expected_keywords": ["WHERE", "created_at"],
        "category": "filter"
    },
    {
        "query": "List products with descriptions",
        "expected_tables": ["products"],
        "expected_keywords": ["SELECT", "description"],
        "category": "simple_select"
    },
    {
        "query": "How many order items are there?",
        "expected_tables": ["order_items"],
        "expected_keywords": ["COUNT"],
        "category": "aggregation"
    },
    {
        "query": "Show me orders with total amount greater than 500",
        "expected_tables": ["orders"],
        "expected_keywords": ["WHERE", "total_amount", ">"],
        "category": "filter"
    },
    {
        "query": "List customers by city",
        "expected_tables": ["customers"],
        "expected_keywords": ["GROUP BY", "city"],
        "category": "group_by"
    },
    {
        "query": "What's the total line total from order items?",
        "expected_tables": ["order_items"],
        "expected_keywords": ["SUM", "line_total"],
        "category": "aggregation"
    },
    {
        "query": "Show me products ordered by stock quantity",
        "expected_tables": ["products"],
        "expected_keywords": ["ORDER BY", "stock_quantity"],
        "category": "ordering"
    },
    {
        "query": "How many customers are in each country?",
        "expected_tables": ["customers"],
        "expected_keywords": ["COUNT", "GROUP BY", "country"],
        "category": "group_by"
    }
]


async def evaluate_query(
    orchestrator: Orchestrator,
    test_case: Dict,
    db: AsyncSession
) -> Dict:
    """
    Evaluate a single query.
    
    Args:
        orchestrator: Orchestrator instance
        test_case: Test case dictionary
        db: Database session
    
    Returns:
        Evaluation result dictionary
    """
    query = test_case["query"]
    expected_tables = test_case["expected_tables"]
    expected_keywords = test_case["expected_keywords"]
    
    start_time = time.time()
    
    try:
        result = await orchestrator.process_query(query)
        
        execution_time = time.time() - start_time
        
        # Check if SQL was generated
        sql = result.get("sql", "").upper()
        sql_lower = sql.lower()
        
        # Validate tables
        tables_found = all(table.lower() in sql_lower for table in expected_tables)
        
        # Validate keywords
        keywords_found = all(keyword.upper() in sql for keyword in expected_keywords)
        
        # Check validation
        validation_passed = result.get("validation_passed", False)
        
        # Check execution
        has_results = len(result.get("results", [])) >= 0  # Allow empty results
        execution_success = not result.get("error", "")
        
        # Overall success: validation passed, tables found, keywords found, no errors
        success = (
            validation_passed and
            tables_found and
            keywords_found and
            execution_success
        )
        
        return {
            "query": query,
            "category": test_case["category"],
            "success": success,
            "sql": result.get("sql", ""),
            "validation_passed": validation_passed,
            "tables_found": tables_found,
            "keywords_found": keywords_found,
            "execution_success": execution_success,
            "results_count": len(result.get("results", [])),
            "error": result.get("error", ""),
            "execution_time_ms": execution_time * 1000,
            "query_understanding": result.get("query_understanding", {})
        }
        
    except Exception as e:
        logger.error(f"Error evaluating query '{query}': {e}")
        return {
            "query": query,
            "category": test_case["category"],
            "success": False,
            "sql": "",
            "validation_passed": False,
            "tables_found": False,
            "keywords_found": False,
            "execution_success": False,
            "results_count": 0,
            "error": str(e),
            "execution_time_ms": (time.time() - start_time) * 1000,
            "query_understanding": {}
        }


async def run_evaluation():
    """Run evaluation on all test queries."""
    logger.info("Starting pipeline evaluation...")
    
    # Create database connection
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    results = []
    
    # Use a single session but ensure clean state between queries
    async with async_session() as db:
        for i, test_case in enumerate(TEST_QUERIES, 1):
            logger.info(f"Evaluating query {i}/{len(TEST_QUERIES)}: {test_case['query']}")
            
            # Create a new orchestrator for each query to ensure clean state
            # But reuse the same session
            orchestrator = Orchestrator(db)
            
            # Ensure clean transaction state before each query
            try:
                await db.rollback()
            except:
                pass
            
            result = await evaluate_query(orchestrator, test_case, db)
            results.append(result)
            
            # Ensure clean state after each query
            try:
                await db.rollback()
            except:
                pass
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
    
    # Calculate statistics
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    accuracy = (successful / total * 100) if total > 0 else 0
    
    validation_passed = sum(1 for r in results if r["validation_passed"])
    avg_execution_time = sum(r["execution_time_ms"] for r in results) / total if total > 0 else 0
    
    # Category breakdown
    category_stats = {}
    for result in results:
        category = result["category"]
        if category not in category_stats:
            category_stats[category] = {"total": 0, "successful": 0}
        category_stats[category]["total"] += 1
        if result["success"]:
            category_stats[category]["successful"] += 1
    
    # Print results
    print("\n" + "="*80)
    print("EVALUATION RESULTS")
    print("="*80)
    print(f"\nTotal Queries: {total}")
    print(f"Successful: {successful}")
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Validation Passed: {validation_passed}/{total}")
    print(f"Average Execution Time: {avg_execution_time:.2f}ms")
    
    print("\nCategory Breakdown:")
    for category, stats in category_stats.items():
        cat_accuracy = (stats["successful"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {category}: {stats['successful']}/{stats['total']} ({cat_accuracy:.2f}%)")
    
    print("\nFailed Queries:")
    failed = [r for r in results if not r["success"]]
    for result in failed:
        print(f"  - {result['query']}")
        if result["error"]:
            print(f"    Error: {result['error']}")
        if not result["tables_found"]:
            print(f"    Missing expected tables")
        if not result["keywords_found"]:
            print(f"    Missing expected keywords")
    
    # Save detailed results
    output_file = "evaluation_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "summary": {
                "total": total,
                "successful": successful,
                "accuracy": accuracy,
                "validation_passed": validation_passed,
                "avg_execution_time_ms": avg_execution_time
            },
            "category_stats": category_stats,
            "results": results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to {output_file}")
    print("="*80)
    
    # Target: 70%+ accuracy
    if accuracy >= 70:
        print(f"\n✓ SUCCESS: Achieved {accuracy:.2f}% accuracy (target: 70%+)")
    else:
        print(f"\n✗ TARGET NOT MET: {accuracy:.2f}% accuracy (target: 70%+)")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_evaluation())

