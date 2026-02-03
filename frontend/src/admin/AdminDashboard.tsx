import { useQuery } from '@tanstack/react-query';
import { adminApi } from '@/lib/api';
import type { AdminMetricsResponse } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatCurrency } from '@/lib/utils';

function MetricCard({
  title,
  value,
  description,
}: {
  title: string;
  value: string | number;
  description?: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold mb-1">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function AdminDashboard() {
  const { data, isLoading, isError } = useQuery<AdminMetricsResponse>({
    queryKey: ['admin', 'metrics'],
    queryFn: () => adminApi.getMetrics(),
    refetchInterval: 10_000, // 10s
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <p className="text-muted-foreground">Loading admin metrics...</p>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-6">
        <p className="text-destructive">
          Failed to load admin metrics. Check backend /api/v1/admin/metrics.
        </p>
      </div>
    );
  }

  const { realtime, tokens, errors, cache, forecast } = data;
  const qs = realtime.query_stats;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Admin Dashboard</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Real-time metrics, usage analytics, and cost forecasting
            </p>
          </div>
          <Badge variant="secondary">
            Window: last {realtime.window_minutes} minutes
          </Badge>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Top-level metrics */}
        <section className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Queries"
            value={qs.total}
            description="in the current window"
          />
          <MetricCard
            title="Success Rate"
            value={`${qs.success_rate.toFixed(1)}%`}
            description={`${qs.success} succeeded / ${qs.failed} failed`}
          />
          <MetricCard
            title="Avg Latency (ms)"
            value={qs.avg_latency_ms.toFixed(1)}
            description={`p95: ${qs.p95_latency_ms.toFixed(1)} ms`}
          />
          <MetricCard
            title="Active Users"
            value={realtime.active_users}
            description="distinct user IDs in window"
          />
        </section>

        {/* Cost & tokens */}
        <section className="grid gap-4 grid-cols-1 md:grid-cols-3">
          <MetricCard
            title="Total Cost (USD)"
            value={formatCurrency(tokens.total_cost)}
            description={`Avg per call: ${formatCurrency(tokens.average_cost_per_call)}`}
          />
          <MetricCard
            title="Total Tokens"
            value={tokens.total_tokens.total.toLocaleString()}
            description={`Input: ${tokens.total_tokens.input.toLocaleString()} / Output: ${tokens.total_tokens.output.toLocaleString()}`}
          />
          <MetricCard
            title="Forecast Monthly Cost"
            value={formatCurrency(forecast.monthly_cost_usd)}
            description="Simple extrapolation based on current rate"
          />
        </section>

        {/* Error breakdown and cache stats */}
        <section className="grid gap-4 grid-cols-1 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Error Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Total Errors</span>
                <span className="font-medium">{errors.total_errors}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Retryable</span>
                <span className="font-medium">
                  {errors.retryable_count} ({errors.retryable_percentage.toFixed(1)}%)
                </span>
              </div>
              <div>
                <h4 className="font-semibold mb-1">By Category</h4>
                {Object.keys(errors.by_category).length === 0 ? (
                  <p className="text-xs text-muted-foreground">No errors recorded.</p>
                ) : (
                  <ul className="text-xs text-muted-foreground space-y-1">
                    {Object.entries(errors.by_category).map(([cat, count]) => (
                      <li key={cat}>
                        <span className="font-medium">{cat}</span>: {count}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Cache & Caching Effectiveness</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Total Keys</span>
                <span className="font-medium">{cache.total_keys}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Keyspace Hits</span>
                <span className="font-medium">{cache.keyspace_hits}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Keyspace Misses</span>
                <span className="font-medium">{cache.keyspace_misses}</span>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Model usage breakdown */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle>Model Usage Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {Object.keys(tokens.model_breakdown).length === 0 ? (
                <p className="text-muted-foreground text-sm">
                  No model usage recorded yet.
                </p>
              ) : (
                <ul className="space-y-1">
                  {Object.entries(tokens.model_breakdown).map(([model, stats]) => (
                    <li
                      key={model}
                      className="flex items-center justify-between text-xs md:text-sm"
                    >
                      <span className="font-medium">{model}</span>
                      <span className="text-muted-foreground">
                        {stats.calls} calls • {stats.tokens.toLocaleString()} tokens •{' '}
                        {formatCurrency(stats.cost)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  );
}


