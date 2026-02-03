"""
Performance testing suite for Phase 3 optimizations.
Tests cost reduction, latency, caching effectiveness, and token tracking.
"""
import asyncio
import time
import statistics
import json
from pathlib import Path
import sys
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.orchestrator import Orchestrator
from app.services.token_tracker import token_tracker
from app.core.redis_client import cache_service
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from loguru import logger


class PerformanceTestSuite:
    """Comprehensive performance testing suite."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.db: AsyncSession = None
        self.engine = None
    
    async def setup(self):
        """Set up test environment."""
        database_url = (
            f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        
        self.engine = create_async_engine(database_url, echo=False)
        async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.db = async_session()
        
        # Clear token tracker
        token_tracker.clear()
        
        logger.info("Performance test environment ready")
    
    async def teardown(self):
        """Clean up test environment."""
        if self.db:
            await self.db.close()
        if self.engine:
            await self.engine.dispose()
        logger.info("Performance test environment cleaned up")
    
    def get_test_queries(self) -> List[Dict[str, str]]:
        """Get test queries of varying complexity."""
        return [
            # Simple queries
            {"query": "How many customers do we have?", "complexity": "simple"},
            {"query": "What's the total revenue?", "complexity": "simple"},
            {"query": "Show me all products", "complexity": "simple"},
            {"query": "List customer names", "complexity": "simple"},
            {"query": "Count orders", "complexity": "simple"},
            
            # Medium queries
            {"query": "Show me total revenue by product category", "complexity": "medium"},
            {"query": "List customers with their order counts", "complexity": "medium"},
            {"query": "What are the top 5 products by sales?", "complexity": "medium"},
            {"query": "Show revenue by month", "complexity": "medium"},
            {"query": "List orders with customer information", "complexity": "medium"},
            
            # Complex queries
            {"query": "Find customers who ordered more than the average order value", "complexity": "complex"},
            {"query": "Show monthly revenue trends with year-over-year comparison", "complexity": "complex"},
            {"query": "List products that have never been ordered", "complexity": "complex"},
            {"query": "Show customer lifetime value by city", "complexity": "complex"},
            {"query": "Find the top 10 customers by total spending with their order history", "complexity": "complex"},
        ]
    
    async def test_query(self, query_data: Dict[str, Any], orchestrator: Orchestrator) -> Dict[str, Any]:
        """Test a single query and collect metrics."""
        query = query_data["query"]
        expected_complexity = query_data["complexity"]
        
        start_time = time.time()
        
        try:
            result = await orchestrator.process_query(query)
            
            execution_time = time.time() - start_time
            
            success = result.get("error") == "" and result.get("sql", "") != ""
            
            # Get token usage
            query_id = f"test_{hash(query)}"
            tokens = token_tracker.get_query_tokens(query_id)
            cost = token_tracker.get_query_cost(query_id)
            
            # Get query understanding for complexity verification
            understanding = result.get("query_understanding", {})
            from app.services.complexity_classifier import complexity_classifier
            detected_complexity = complexity_classifier.classify_from_understanding(understanding)
            
            return {
                "query": query,
                "expected_complexity": expected_complexity,
                "detected_complexity": detected_complexity.value,
                "success": success,
                "execution_time": execution_time,
                "tokens": tokens,
                "cost": cost,
                "error": result.get("error", "")
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "query": query,
                "expected_complexity": expected_complexity,
                "detected_complexity": "unknown",
                "success": False,
                "execution_time": execution_time,
                "tokens": {"input": 0, "output": 0, "total": 0},
                "cost": 0.0,
                "error": str(e)
            }
    
    async def test_caching_effectiveness(self, orchestrator: Orchestrator):
        """Test caching effectiveness by running same queries twice."""
        test_query = "How many customers do we have?"
        
        # First run (cold cache)
        start1 = time.time()
        result1 = await orchestrator.process_query(test_query)
        time1 = time.time() - start1
        
        # Second run (warm cache)
        start2 = time.time()
        result2 = await orchestrator.process_query(test_query)
        time2 = time.time() - start2
        
        cache_improvement = ((time1 - time2) / time1 * 100) if time1 > 0 else 0
        
        return {
            "cold_cache_time": time1,
            "warm_cache_time": time2,
            "improvement_percent": cache_improvement,
            "cache_working": time2 < time1 * 0.8  # At least 20% faster
        }
    
    async def run_tests(self):
        """Run comprehensive performance tests."""
        logger.info("Starting performance tests...")
        
        orchestrator = Orchestrator(self.db, max_retries=3)
        
        test_queries = self.get_test_queries()
        
        # Test all queries
        for query_data in test_queries:
            result = await self.test_query(query_data, orchestrator)
            self.results.append(result)
            logger.info(
                f"Query: {query_data['query'][:50]}... | "
                f"Time: {result['execution_time']:.2f}s | "
                f"Cost: ${result['cost']:.6f} | "
                f"Success: {result['success']}"
            )
        
        # Test caching
        cache_results = await self.test_caching_effectiveness(orchestrator)
        
        # Generate report
        report = self.generate_report(cache_results)
        
        return report
    
    def generate_report(self, cache_results: Dict[str, Any]) -> str:
        """Generate performance test report."""
        total_queries = len(self.results)
        successful_queries = sum(1 for r in self.results if r["success"])
        failed_queries = total_queries - successful_queries
        
        execution_times = [r["execution_time"] for r in self.results if r["success"]]
        costs = [r["cost"] for r in self.results if r["success"]]
        tokens = [r["tokens"]["total"] for r in self.results if r["success"]]
        
        # Calculate percentiles
        p50 = statistics.median(execution_times) if execution_times else 0
        p90 = statistics.quantiles(execution_times, n=10)[8] if len(execution_times) >= 10 else max(execution_times) if execution_times else 0
        p95 = statistics.quantiles(execution_times, n=20)[18] if len(execution_times) >= 20 else max(execution_times) if execution_times else 0
        
        # Complexity breakdown
        complexity_stats = {}
        for result in self.results:
            complexity = result["detected_complexity"]
            if complexity not in complexity_stats:
                complexity_stats[complexity] = {
                    "count": 0,
                    "avg_time": [],
                    "avg_cost": [],
                    "avg_tokens": []
                }
            complexity_stats[complexity]["count"] += 1
            if result["success"]:
                complexity_stats[complexity]["avg_time"].append(result["execution_time"])
                complexity_stats[complexity]["avg_cost"].append(result["cost"])
                complexity_stats[complexity]["avg_tokens"].append(result["tokens"]["total"])
        
        # Calculate averages per complexity
        for complexity in complexity_stats:
            stats = complexity_stats[complexity]
            stats["avg_time"] = statistics.mean(stats["avg_time"]) if stats["avg_time"] else 0
            stats["avg_cost"] = statistics.mean(stats["avg_cost"]) if stats["avg_cost"] else 0
            stats["avg_tokens"] = statistics.mean(stats["avg_tokens"]) if stats["avg_tokens"] else 0
        
        # Get overall token statistics
        token_stats = token_tracker.get_statistics()
        
        report = f"""
================================================================================
PERFORMANCE TEST REPORT - Phase 3 Optimizations
================================================================================

## Test Summary

- Total Queries: {total_queries}
- Successful: {successful_queries} ({successful_queries/total_queries*100:.1f}%)
- Failed: {failed_queries} ({failed_queries/total_queries*100:.1f}%)

## Latency Metrics

- Average Execution Time: {statistics.mean(execution_times):.3f}s
- Median (p50): {p50:.3f}s
- p90: {p90:.3f}s
- p95: {p95:.3f}s
- Min: {min(execution_times):.3f}s
- Max: {max(execution_times):.3f}s

Target: <2s for 90% of queries
Status: {'✅ PASS' if p90 < 2.0 else '❌ FAIL'} (p90: {p90:.3f}s)

## Cost Metrics

- Average Cost per Query: ${statistics.mean(costs):.6f}
- Total Cost: ${sum(costs):.6f}
- Median Cost: ${statistics.median(costs):.6f}
- Min Cost: ${min(costs):.6f}
- Max Cost: ${max(costs):.6f}

Target: <$0.02 average per query
Status: {'✅ PASS' if statistics.mean(costs) < 0.02 else '❌ FAIL'} (avg: ${statistics.mean(costs):.6f})

## Token Usage

- Average Tokens per Query: {statistics.mean(tokens):.0f}
- Total Tokens: {sum(tokens):,}
- Median Tokens: {statistics.median(tokens):.0f}

## Complexity Breakdown

"""
        
        for complexity in ["simple", "medium", "complex"]:
            if complexity in complexity_stats:
                stats = complexity_stats[complexity]
                report += f"""
### {complexity.upper()}
- Count: {stats['count']}
- Avg Time: {stats['avg_time']:.3f}s
- Avg Cost: ${stats['avg_cost']:.6f}
- Avg Tokens: {stats['avg_tokens']:.0f}
"""
        
        report += f"""
## Caching Effectiveness

- Cold Cache Time: {cache_results['cold_cache_time']:.3f}s
- Warm Cache Time: {cache_results['warm_cache_time']:.3f}s
- Improvement: {cache_results['improvement_percent']:.1f}%
- Cache Working: {'✅ YES' if cache_results['cache_working'] else '❌ NO'}

## Overall Token Statistics

{json.dumps(token_stats, indent=2)}

## Recommendations

"""
        
        if p90 >= 2.0:
            report += "- ⚠️  p90 latency exceeds 2s target. Consider further optimization.\n"
        if statistics.mean(costs) >= 0.02:
            report += "- ⚠️  Average cost exceeds $0.02 target. Review model routing.\n"
        if not cache_results['cache_working']:
            report += "- ⚠️  Caching not showing expected improvement. Check cache configuration.\n"
        
        if p90 < 2.0 and statistics.mean(costs) < 0.02:
            report += "- ✅ All performance targets met!\n"
        
        report += "\n================================================================================\n"
        
        return report


async def main():
    """Run performance tests."""
    suite = PerformanceTestSuite()
    
    try:
        await suite.setup()
        report = await suite.run_tests()
        print(report)
        
        # Save report to file
        with open("backend/performance_test_report.txt", "w") as f:
            f.write(report)
        logger.info("Performance test report saved to backend/performance_test_report.txt")
        
    finally:
        await suite.teardown()


if __name__ == "__main__":
    import json
    asyncio.run(main())

