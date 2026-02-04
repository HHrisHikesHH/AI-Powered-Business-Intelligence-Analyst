# Architecture Documentation

## Overview

This document explains the key components and architecture of the AI-Powered Business Intelligence Analyst system, including backend services, multi-agent orchestration, observability, and the React-based frontend.

## System Architecture

```plantuml
@startuml
actor User
actor "Admin" as Admin

rectangle "Frontend (React + Shadcn/UI)" {
  User --> (Query UI)
  Admin --> (Admin Dashboard)
}

rectangle "Backend (FastAPI)" {
  (Query API) --> (Orchestrator)
  (Admin API) --> (Metrics Service)
  (Metrics Endpoint)
}

rectangle "Agents & Services" {
  (Query Understanding Agent)
  (SQL Generation Agent)
  (SQL Validator)
  (Analysis Agent)
  (Visualization Agent)
  (Token Tracker)
  (Error Handler)
  (Metrics Service)
}

rectangle "Data Layer" {
  (PostgreSQL + pgvector)
  (Redis Cache)
}

rectangle "Observability" {
  (Prometheus)
  (Grafana)
}

User -> (Query UI)
(Query UI) --> (Query API): POST /api/v1/queries
(Query API) --> (Orchestrator)
(Orchestrator) --> (Query Understanding Agent)
(Orchestrator) --> (SQL Generation Agent)
(Orchestrator) --> (SQL Validator)
(Orchestrator) --> (Analysis Agent)
(Orchestrator) --> (Visualization Agent)
(Orchestrator) --> (Token Tracker)
(Orchestrator) --> (Error Handler)
(Orchestrator) --> (Metrics Service)
(Orchestrator) --> (PostgreSQL + pgvector)
(Orchestrator) --> (Redis Cache)

Admin --> (Admin Dashboard)
(Admin Dashboard) --> (Admin API): GET /api/v1/admin/metrics
(Admin API) --> (Metrics Service)
(Metrics Service) --> (Redis Cache)

(Prometheus) --> (Metrics Endpoint): scrape /metrics
(Grafana) --> (Prometheus): visualise

@enduml
```

## Directory Structure

```
.
├── docker-compose.yml           # Backend, Redis, Celery worker, Prometheus, Grafana
├── Makefile                     # Development commands
├── README.md                    # Main documentation
├── ARCHITECTURE.md              # This file
├── START_SERVICES.md            # Local backend + services guide
└── backend/
    ├── Dockerfile               # Backend container definition
    ├── requirements.txt         # Python dependencies
    ├── app/
    │   ├── main.py              # FastAPI application entrypoint
    │   ├── celery_app.py        # Celery configuration
    │   ├── agents/              # Multi-agent NL→SQL pipeline
    │   ├── core/                # Core services (config, DB, Redis, pgvector, LLM)
    │   ├── services/            # Hybrid RAG, query execution, metrics, error handling
    │   ├── api/                 # Versioned API routes
    │   └── tasks/               # Celery tasks
    ├── database/
    │   ├── enterprise_schema.sql      # 40+ table enterprise schema
    │   ├── enterprise_seed_data*.sql  # Comprehensive seed data
    │   ├── init.sql                   # Legacy minimal schema (for reference)
    │   └── README.md                  # Schema documentation and quick start
    ├── tests/                   # Unit, integration, performance, security, benchmark tests
    └── scripts/                 # DB and helper scripts (e.g., setup_database.py)
```

## Key Components

### 1. Docker Compose (`docker-compose.yml`)

Orchestrates the core runtime services:

- **Backend (FastAPI + agents)** – serves the public query API, admin endpoints, and `/metrics`.
- **Redis** – shared cache and Celery broker.
- **Celery worker** – executes background jobs (e.g., schema embedding).
- **Prometheus** – scrapes the backend’s `/metrics` endpoint.
- **Grafana** – visualises metrics dashboards.

> **Note:** PostgreSQL is expected to run outside this compose file (e.g., local Postgres or a managed DB). The backend connects using `DATABASE_URL` or `POSTGRES_*` settings.

Key features:
- Health checks and dependency ordering.
- Isolation via a dedicated Docker network.

### 2. FastAPI Application (`backend/app/main.py`)

The main process:
- Loads configuration (`config.py`) and logging.
- Initializes:
  - Database adapter and async session factory (`database_adapter.py`, `database.py`).
  - Redis client (`redis_client.py`).
  - LLM client (`llm_client.py`).
  - Schema introspection & pgvector embeddings (`schema_introspection.py`, `pgvector_client.py`).
- Registers:
  - Public query routes under `/api/v1/queries`.
  - Admin/metrics routes under `/api/v1/admin`.
  - Health and readiness endpoints.

### 3. Core Services (`backend/app/core/`)

#### `config.py`
- Pydantic-based configuration management.
- Loads environment variables from `.env` and environment.
- Provides typed settings (DB, Redis, LLM models, environment flags).

#### `database_adapter.py` & `database.py`
- Multi-DB abstraction for PostgreSQL, MySQL, and SQLite.
- Builds async SQLAlchemy engines and session factories.
- Exposes FastAPI-friendly dependencies (`get_db_adapter`, `get_db`).

#### `redis_client.py`
- Async Redis client.
- Simple caching API with TTL support and JSON serialisation.

#### `pgvector_client.py`
- Manages embeddings stored in PostgreSQL with the `pgvector` extension.
- Used by schema introspection and hybrid RAG to retrieve relevant tables/columns/relationships.

#### `llm_client.py`
- Groq API client for Llama 3 / GPT‑OSS families.
- Centralises model selection, timeouts, and retry logic.

### 4. API Layer (`backend/app/api/v1/`)

#### `router.py`
- Main API router
- Aggregates all endpoint routers
- Version management (v1)

#### `endpoints/queries.py`
- POST `/api/v1/queries/`: Accept natural language queries
- GET `/api/v1/queries/{query_id}`: Retrieve query results (placeholder)
- Request/response models with Pydantic
- Caching integration
- Error handling

### 5. Agents & Business Logic (`backend/app/agents/` & `backend/app/services/`)

#### Orchestrator (`agents/orchestrator.py`)
- LangGraph-based state machine that wires:
  - `QueryUnderstandingAgent`
  - `SQLGenerationAgent`
  - `SQLValidator`
  - `AnalysisAgent`
  - `VisualizationAgent`
  - `QueryExecutor`, `ErrorHandler`, and `Metrics` services.
- Implements retries, self-correction, and “simple vs complex” branching to skip heavy analysis where appropriate.

#### Query Understanding (`agents/query_understanding.py`)
- Normalises natural language queries into a rich, typed structure.
- Enforces “no default table” policy to avoid hallucinated joins.

#### SQL Generation (`agents/sql_generation.py` + `services/hybrid_rag.py` + `services/schema_introspection.py`)
- Grounds query understanding against the live enterprise schema.
- Uses hybrid RAG over pgvector to retrieve relevant tables/columns/relationships and examples.
- Generates **schema-respecting** SQL with explicit constraints against non-existent tables/columns.

#### SQL Validation (`agents/sql_validator.py`)
- Ensures only safe SQL reaches the database.
- Uses `sqlparse` and schema cache to reject dangerous or malformed queries.

#### Execution (`services/query_executor.py`)
- Runs SQL with timeouts and automatic row limits.
- Normalises results to JSON-friendly types.

#### Analysis & Visualisation (`agents/analysis.py`, `agents/visualization.py`)
- AnalysisAgent: produces business-ready insights/trends/anomalies/recommendations.
- VisualizationAgent: selects chart types and constructs Recharts configuration for the frontend.

### 6. Celery Tasks (`backend/app/tasks/`)

#### `embedding_tasks.py`
- Background jobs for:
  - Generating and refreshing schema embeddings.
  - Potentially precomputing heavy analytics or materialised views.

### 7. Database (`backend/database/`)

- **`enterprise_schema.sql`** – 40+ table enterprise schema (HR, Finance, Sales/CRM, Inventory, Projects, Support, Marketing).
- **`enterprise_seed_data*.sql`** – Rich, cross-linked seed data for realistic testing.
- **`init.sql` / `seed_data.sql`** – Legacy minimal schema and seed data (kept for reference and simple demos).

## Data Flow

### End-to-End NL→SQL→Insights

```
1. User submits natural language query
   ↓
2. FastAPI Query API receives request and initialises AgentState
   ↓
3. Orchestrator runs "understand" node
   - QueryUnderstandingAgent produces structured understanding (intent, tables, filters, etc.)
   - May serve from Redis cache for repeated queries
   ↓
4. Orchestrator runs "generate" node
   - SQLGenerationAgent:
     • Retrieves schema & embedding context (Hybrid RAG over pgvector)
     • Generates candidate SQL constrained to known tables/columns
   ↓
5. Orchestrator runs "validate" node
   - SQLValidator:
     • Enforces SELECT-only
     • Blocks dangerous operations
     • Checks schema consistency
   - On failure, orchestrator may retry or trigger self-correction
   ↓
6. Orchestrator runs "execute" node
   - QueryExecutor executes SQL with timeout and row limit
   - Results are normalised and may be cached in Redis
   ↓
7. Orchestrator decides analysis path
   - Simple queries may skip analysis/visualisation
   - Complex/aggregated queries proceed to "analyze_and_visualize"
   ↓
8. Orchestrator runs "analyze_and_visualize"
   - AnalysisAgent: insights, trends, anomalies, recommendations, summary
   - VisualizationAgent: selects chart type and builds config
   ↓
9. Response returned to client
```

## Technology Choices

### Why FastAPI?
- Modern async/await support
- Automatic API documentation (Swagger)
- Type validation with Pydantic
- High performance

### Why PostgreSQL?
- Robust relational database
- ACID compliance
- Rich SQL features
- Excellent async support via asyncpg

### Why Redis?
- Fast in-memory caching
- Shared infrastructure for request-level caching and background jobs
- Simple, battle-tested operational model

### Why pgvector (in PostgreSQL)?
- Keeps vector search close to the relational data.
- Avoids an additional vector database dependency.
- Works well for schema embeddings and semantic schema search.

### Why Groq (Llama 3 / GPT‑OSS)?
- High-performance hosted LLMs with strong SQL reasoning.
- Multiple model sizes for cost-aware routing.
- Straightforward HTTP API integrated through `llm_client.py`.

### Why Celery?
- Distributed task processing
- Async operations (embeddings, heavy processing)
- Scalable worker architecture
- Integration with Redis

## Configuration

### Environment Variables

All configuration is managed through `backend/.env` and loaded by `config.py`. Key settings:

```bash
# Database (PostgreSQL by default)
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=ai_bi_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=ai_bi_db
# Or override with a single DATABASE_URL:
# DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM (Groq)
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL_SIMPLE=llama-3.1-8b-instant
LLM_MODEL_MEDIUM=llama-3.3-70b-versatile
LLM_MODEL_COMPLEX=openai/gpt-oss-120b

# Application
ENVIRONMENT=development
BACKEND_PORT=8001
LOG_LEVEL=INFO
```

## Security Considerations

### Current Protections
- SQL safety: `SQLValidator` enforces SELECT-only semantics and blocks dangerous operations.
- Row limits and timeouts: `QueryExecutor` enforces sensible limits and async timeouts.
- Least-privilege DB accounts: intended to be read-only or minimally privileged.
- Secrets management: API keys and credentials injected via environment variables.

### Future Enhancements
- Per-tenant and per-role query policies.
- Deeper auditing and data access logging.
- Rate limiting and anomaly detection on query patterns.

## Performance Optimizations

### Current
- Connection pooling and async I/O throughout the stack.
- Redis caching for hot query understandings and results.
- Schema embeddings stored and indexed via pgvector.
- Containerised services with clear separation of concerns.

### Future
- More advanced cost- and latency-aware model routing.
- Pagination and streaming for large result sets.
- Incremental and batched embedding refresh cycles.

## Monitoring & Observability

### Current
- Structured logging via Loguru.
- Health and readiness endpoints (used by Docker and load balancers).
- Prometheus `/metrics` endpoint for backend metrics.

### Future
- Distributed tracing for agent steps (e.g., LangGraph/OpenTelemetry).
- Cost tracking and SLO-based alerting.
- Richer Grafana dashboards for latency, errors, and LLM usage.

## Testing

### Running Tests

```bash
cd backend
source venv/bin/activate
pytest -v
```

Examples:

```bash
# Health and smoke tests
pytest tests/test_error_handling.py -v

# Orchestrator + multi-agent flow
pytest tests/test_orchestrator.py -v

# Enterprise schema end-to-end queries
pytest tests/test_enterprise_schema.py -v
```

## Development Workflow

1. **Make changes** to code in `backend/app/`
2. **Hot reload** enabled (FastAPI auto-reloads)
3. **View logs**: `make logs`
4. **Test changes**: Use API docs at http://localhost:8001/docs
5. **Reset database**: `make db-reset` (if needed)

## Next Steps / Roadmap

At this stage the core backend, multi-agent pipeline, enterprise schema, caching, and observability are in place. Future work can focus on:

- **Benchmark & evaluation**: Expand the benchmark dataset, automate result analysis, and wire metrics into Grafana.
- **Security & governance**: Role-based access, row/column-level security, and richer auditing.
- **Scalability**: Horizontal scaling for backend and workers, plus resilient LLM and DB failover patterns.
- **UX & tooling**: Enhance the React frontend (query builder, saved views, admin console) and add admin tools for cost/performance tuning.

## Troubleshooting

### Common Issues

1. **Services won't start**
   - Check port availability
   - Verify Docker is running
   - Check logs: `make logs`

2. **Database connection errors**
   - Wait for PostgreSQL to be healthy
   - Check environment variables
   - Verify network connectivity

3. **LLM API errors**
   - Verify GROQ_API_KEY is set
   - Check API key validity
   - Monitor rate limits

4. **Prometheus / Grafana issues**
   - Ensure both containers are running
   - Check `http://localhost:9090` (Prometheus) and `http://localhost:3001` (Grafana)
   - Verify backend `/metrics` is reachable from Prometheus

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Groq API Documentation](https://console.groq.com/docs)
- [Celery Documentation](https://docs.celeryq.dev/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [pgvector Extension](https://github.com/pgvector/pgvector)