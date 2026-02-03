"""
Metrics and monitoring service for admin dashboard and alerts.
Tracks query-level statistics, success rate, latency, active users, and cost.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
import statistics

from loguru import logger

from app.services.token_tracker import token_tracker
from app.services.error_handler import error_handler
from app.core.redis_client import cache_service


@dataclass
class QueryRecord:
    timestamp: datetime
    success: bool
    latency_ms: float
    cost: float
    user_id: Optional[str] = None


class MetricsService:
    """
    In-memory metrics service for high-level admin statistics.
    Not intended for precise billing, but for monitoring trends.
    """

    def __init__(self, window_minutes: int = 60):
        # Sliding window for recent metrics
        self.window_minutes = window_minutes
        self.records: List[QueryRecord] = []
        self.total_queries: int = 0
        self.successful_queries: int = 0
        self.failed_queries: int = 0
        self.total_latency_ms: float = 0.0
        self.total_cost: float = 0.0
        self.active_users: Set[str] = set()

    def _prune_old_records(self) -> None:
        """Remove records outside the sliding window."""
        if not self.records:
            return
        cutoff = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        self.records = [r for r in self.records if r.timestamp >= cutoff]

    def record_query(
        self,
        success: bool,
        latency_ms: float,
        cost: float,
        user_id: Optional[str] = None,
    ) -> None:
        """Record a single query execution."""
        record = QueryRecord(
            timestamp=datetime.utcnow(),
            success=success,
            latency_ms=latency_ms,
            cost=cost,
            user_id=user_id,
        )
        self.records.append(record)

        # Update aggregates
        self.total_queries += 1
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1
        self.total_latency_ms += latency_ms
        self.total_cost += cost

        if user_id:
            self.active_users.add(user_id)

        # Prune old records and check alerts
        self._prune_old_records()
        self._check_alerts()

    def _check_alerts(self) -> None:
        """
        Simple alerting: log warnings when error rate is high.
        Can be extended to send emails or integrate with external systems.
        """
        if self.total_queries < 20:
            # Avoid noisy alerts at startup
            return

        error_rate = (self.failed_queries / self.total_queries) * 100 if self.total_queries else 0

        if error_rate > 15:
            logger.warning(
                f"[ALERT] High error rate detected: {error_rate:.1f}% "
                f"({self.failed_queries}/{self.total_queries} queries failed)"
            )

    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get metrics for the last N minutes."""
        self._prune_old_records()
        window_records = self.records

        if not window_records:
            return {
                "window_minutes": self.window_minutes,
                "query_stats": {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "success_rate": 0.0,
                    "avg_latency_ms": 0.0,
                    "p95_latency_ms": 0.0,
                },
                "active_users": 0,
                "avg_cost_per_query": 0.0,
            }

        total = len(window_records)
        success = sum(1 for r in window_records if r.success)
        failed = total - success
        success_rate = (success / total) * 100 if total else 0.0
        latencies = [r.latency_ms for r in window_records]
        avg_latency = statistics.mean(latencies)
        # Approximate p95
        try:
            p95 = statistics.quantiles(latencies, n=20)[18]
        except Exception:
            p95 = max(latencies) if latencies else 0.0

        avg_cost = statistics.mean(r.cost for r in window_records) if window_records else 0.0
        active_users = len({r.user_id for r in window_records if r.user_id})

        return {
            "window_minutes": self.window_minutes,
            "query_stats": {
                "total": total,
                "success": success,
                "failed": failed,
                "success_rate": success_rate,
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": p95,
            },
            "active_users": active_users,
            "avg_cost_per_query": avg_cost,
        }

    def forecast_monthly_cost(self) -> float:
        """
        Very simple cost forecast:
        - Use average cost per query in the window.
        - Multiply by an assumed number of queries per month based on current rate.
        """
        self._prune_old_records()
        window_records = self.records
        if not window_records:
            return 0.0

        total = len(window_records)
        window_minutes = self.window_minutes
        # Queries per minute -> per month (~30 days)
        qpm = total / window_minutes
        queries_per_month = qpm * 60 * 24 * 30
        avg_cost = statistics.mean(r.cost for r in window_records)
        return queries_per_month * avg_cost

    async def get_admin_summary(self) -> Dict[str, Any]:
        """Aggregate metrics, errors, cache stats, and cost forecast for admin dashboard."""
        realtime = self.get_realtime_metrics()
        token_stats = token_tracker.get_statistics()
        error_stats = error_handler.get_error_statistics()
        cache_stats = await cache_service.get_stats()

        forecast_monthly_cost = self.forecast_monthly_cost()

        return {
            "realtime": realtime,
            "tokens": token_stats,
            "errors": error_stats,
            "cache": cache_stats,
            "forecast": {
                "monthly_cost_usd": forecast_monthly_cost,
            },
        }


# Global metrics service instance
metrics_service = MetricsService()


