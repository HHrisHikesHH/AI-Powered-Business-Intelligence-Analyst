export interface QueryRequest {
  query: string;
  user_id?: string;
  page?: number;
  page_size?: number;
}

export interface PaginationInfo {
  page: number;
  page_size: number;
  total_results: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface CostBreakdown {
  tokens: {
    total: number;
    input: number;
    output: number;
  };
  cost: number;
}

export interface QueryResponse {
  query_id: string;
  natural_language_query: string;
  generated_sql?: string;
  results?: any[];
  analysis?: {
    insights?: string[];
    summary?: string;
    recommendations?: string[];
  };
  visualization?: {
    chart_type: string;
    data_key?: string;
    category_key?: string;
    title?: string;
    description?: string;
    x_axis_label?: string;
    y_axis_label?: string;
    colors?: string[];
    config?: any;
  };
  error?: string;
  execution_time_ms?: number;
  pagination?: PaginationInfo;
  cost_breakdown?: CostBreakdown;
}

export interface QueryHistoryItem {
  id: string;
  query: string;
  timestamp: Date;
  response?: QueryResponse;
}

export interface AdminMetricsResponse {
  realtime: {
    window_minutes: number;
    query_stats: {
      total: number;
      success: number;
      failed: number;
      success_rate: number;
      avg_latency_ms: number;
      p95_latency_ms: number;
    };
    active_users: number;
    avg_cost_per_query: number;
  };
  tokens: {
    total_calls: number;
    total_tokens: {
      input: number;
      output: number;
      total: number;
    };
    total_cost: number;
    average_cost_per_call: number;
    model_breakdown: Record<string, { calls: number; tokens: number; cost: number }>;
  };
  errors: {
    total_errors: number;
    by_category: Record<string, number>;
    by_severity: Record<string, number>;
    retryable_count: number;
    retryable_percentage: number;
  };
  cache: {
    keyspace_hits: number;
    keyspace_misses: number;
    total_keys: number;
  };
  forecast: {
    monthly_cost_usd: number;
  };
}

