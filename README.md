# AI-Powered Business Intelligence Analyst

An intelligent multi-agent system that enables non-technical users to query databases using natural language, receiving actionable insights, visualizations, and recommendations.

## Overview

This implementation provides an enterprise-grade, production-oriented backend that follows the technical specification:
- Multi-agent NL→SQL pipeline with safety and self-correction
- Enterprise relational schema (40+ tables) with pgvector embeddings
- Redis-backed caching and Celery workers
- Comprehensive testing, benchmarking, and monitoring

## Architecture Overview

The system is built as a container-friendly, multi-agent analytics backend:

- **FastAPI backend** (`backend/app/main.py`): Async API surface for NL queries and admin operations
- **Multi-agent pipeline** (`backend/app/agents/*`): Orchestrated NL → SQL → Execution → Analysis → Visualization flow
- **PostgreSQL + pgvector**: Primary OLAP-style database with enterprise schema and vector embeddings
- **Redis**: Caching layer and Celery broker (query understanding cache, schema embeddings, etc.)
- **Celery worker**: Background tasks (embedding generation, heavy jobs)
- **Groq LLM API**: Multiple models with complexity-based routing (simple/medium/complex)
- **Prometheus + Grafana**: Metrics collection and dashboards for latency, errors, and throughput
- **Optional frontend** (`frontend/`): React + Tailwind UI for query console, history, and admin dashboard

## Project Structure

High-level layout (see `ARCHITECTURE.md`, `DATA_FLOW.md`, and `backend/TESTING_PLAN.md` for deep dives):

```
.
├── docker-compose.yml           # Redis, backend, Celery, Prometheus, Grafana
├── Makefile                     # Convenience commands
├── QUICKSTART.md                # 5‑minute Docker quick start
├── START_SERVICES.md            # Local backend + services guide
├── ARCHITECTURE.md              # Detailed multi-agent + RAG architecture
├── DATA_FLOW.md                 # End‑to‑end data and control flow
├── README.md                    # This file (high‑level overview)
├── backend/
│   ├── Dockerfile               # Backend container definition
│   ├── requirements.txt         # Python dependencies
│   ├── app/
│   │   ├── main.py              # FastAPI app entrypoint
│   │   ├── celery_app.py        # Celery configuration
│   │   ├── agents/              # Multi‑agent NL→SQL pipeline
│   │   │   ├── orchestrator.py        # LangGraph-based orchestrator
│   │   │   ├── query_understanding.py # Query understanding agent
│   │   │   ├── sql_generation.py      # SQL generation agent (with RAG)
│   │   │   ├── sql_validator.py       # SQL safety and schema validation
│   │   │   ├── analysis.py            # Result analysis agent
│   │   │   └── visualization.py       # Chart / config generation
│   │   ├── core/                # Core infra modules
│   │   │   ├── config.py              # Settings (DB, Redis, LLM, etc.)
│   │   │   ├── database_adapter.py    # Multi‑DB adapter (Postgres, MySQL, SQLite)
│   │   │   ├── database.py            # Session factory + dependency helpers
│   │   │   ├── redis_client.py        # Async Redis cache client
│   │   │   ├── pgvector_client.py     # Vector store client (pgvector)
│   │   │   └── llm_client.py          # Groq client + complexity routing
│   │   ├── services/            # Supporting services
│   │   │   ├── hybrid_rag.py          # Hybrid RAG (vector + keyword + graph)
│   │   │   ├── schema_introspection.py# Schema discovery + embeddings
│   │   │   ├── query_executor.py      # Safe SQL execution with timeouts
│   │   │   ├── error_handler.py       # Error categorization / retries
│   │   │   └── metrics.py             # Prometheus metric helpers
│   │   └── api/                 # Versioned API routes
│   │       └── v1/
│   │           ├── router.py
│   │           └── endpoints/
│   │               └── queries.py     # Primary NL query endpoint
│   ├── database/
│   │   ├── enterprise_schema.sql      # 40+ table enterprise schema
│   │   ├── enterprise_seed_data*.sql  # Comprehensive seed data
│   │   ├── DATABASE_MIGRATION_GUIDE.md
│   │   └── README.md                  # Schema documentation and quick start
│   ├── tests/                   # Comprehensive test suite (see TESTING_PLAN.md)
│   │   ├── test_database_adapter.py
│   │   ├── test_query_understanding.py
│   │   ├── test_sql_generation.py
│   │   ├── test_sql_validator.py
│   │   ├── test_analysis_agent.py
│   │   ├── test_visualization_agent.py
│   │   ├── test_orchestrator.py
│   │   ├── test_hybrid_rag.py
│   │   ├── test_enterprise_schema.py
│   │   ├── test_benchmark.py          # 500‑query benchmark harness (sampled)
│   │   ├── test_performance.py
│   │   ├── test_concurrency.py
│   │   ├── test_cost_optimization.py
│   │   ├── test_error_handling.py
│   │   └── test_security.py
│   └── scripts/
│       ├── setup_database.py          # Local DB bootstrap helpers
│       └── generate_benchmark_queries.py
├── frontend/                    # React + Vite + Tailwind frontend (query UI)
└── monitoring/
    └── prometheus.yml          # Prometheus scrape config for backend metrics
```

## Key Components & Flows

### Multi‑Agent NL→SQL Pipeline

The core intelligence lives in `backend/app/agents/` and is orchestrated by `orchestrator.py`:

1. **Query Understanding Agent** (`query_understanding.py`)
   - Parses natural language into a structured representation:
     - intent, tables, columns, filters, aggregations, group_by, order_by, limit
   - Uses Groq LLMs with a **non‑hallucinating prompt** and examples
   - Caches understandings in Redis for common queries

2. **SQL Generation Agent** (`sql_generation.py`)
   - Grounds the understanding against the **actual enterprise schema** (via `schema_introspection.py` + pgvector)
   - Uses **Hybrid RAG** (`hybrid_rag.py`): vector + keyword + graph relationships
   - Generates safe PostgreSQL SQL with:
     - Anti‑hallucination rules (only use tables/columns that exist)
     - Retry + self‑correction when validation fails

3. **SQL Validator** (`sql_validator.py`)
   - Blocks dangerous operations (DROP/DELETE/UPDATE/ALTER/etc.)
   - Ensures only `SELECT` queries run
   - Validates tables/columns against the schema cache

4. **Query Executor** (`services/query_executor.py`)
   - Runs SQL safely with:
     - Timeouts
     - Row limits
     - JSON‑friendly result shaping (dates, decimals, etc.)

5. **Analysis Agent** (`analysis.py`)
   - Interprets result sets and generates:
     - insights, trends, anomalies, recommendations, summary
   - Uses LLM with a JSON‑only protocol and robust fallback behavior

6. **Visualization Agent** (`visualization.py`)
   - Chooses appropriate chart types (bar/line/area/pie/number card/etc.)
   - Outputs a Recharts‑friendly config used by the frontend

End‑to‑end, this is wired together by the **LangGraph‑based orchestrator** (`orchestrator.py`), which:

- Manages step transitions (understand → generate → validate → execute → analyze/visualize)
- Applies retry logic and self‑correction
- Tracks metrics and error categories for observability

### Core Infra Modules

- **`backend/app/core/config.py`** – Typed settings for DB, Redis, LLMs, feature flags.
- **`backend/app/core/database_adapter.py`** – Factory for Postgres/MySQL/SQLite adapters.
- **`backend/app/core/database.py`** – Async session factory + FastAPI `get_db` dependency.
- **`backend/app/core/pgvector_client.py`** – Vector store client for schema/context embeddings.
- **`backend/app/core/redis_client.py`** – Redis connection and simple cache wrapper.
- **`backend/app/core/llm_client.py`** – Groq client with complexity classifier and model routing.

### Enterprise Schema

- **`backend/database/enterprise_schema.sql`** – 40+ table schema covering:
  - HR, Finance, Sales/CRM, Inventory, Projects, Support, Marketing
- **`backend/database/enterprise_seed_data*.sql`** – Comprehensive seed data for realistic queries.
- See `backend/database/README.md` for a full breakdown and quick start.

### Testing & Benchmarking

- **`backend/TESTING_PLAN.md`** – Master testing strategy (unit, integration, performance, security).
- **Key test files** (`backend/tests/`):
  - `test_database_adapter.py` – Multi‑DB adapter & schema introspection.
  - `test_query_understanding.py`, `test_sql_generation.py`, `test_sql_validator.py` – Agent‑level behavior.
  - `test_analysis_agent.py`, `test_visualization_agent.py` – Insights & visualization configs.
  - `test_orchestrator.py` – End‑to‑end orchestration paths and error handling.
  - `test_enterprise_schema.py` – Cross‑module enterprise queries (HR/Finance/Sales/etc.).
  - `test_benchmark.py` – 500‑query benchmark harness:
    - Deterministically samples **5 queries per category** for speed.
    - Prints **per‑query status** (ID, category, SQL accuracy, execution status) as it runs.
  - `test_performance.py`, `test_concurrency.py`, `test_cost_optimization.py` – Latency, load, and cost routing.
  - `test_error_handling.py`, `test_security.py` – Safety, injection protection, and hardening.

To run the full suite:

```bash
cd backend
source venv/bin/activate
pytest -v
```

To run the sampled benchmark with per‑query feedback:

```bash
cd backend
source venv/bin/activate
pytest tests/test_benchmark.py -v -s
```

## Setup Instructions

### Prerequisites

- Docker and Docker Compose installed (for containerized setup)
- Python 3.11+ (for local development)
- Groq API key (get one at https://console.groq.com)

### Local Development Setup (Recommended)

For local development without Docker:

```bash
# Run the bootstrap script
./scripts/dev_setup.sh

# Activate virtual environment
cd backend && source venv/bin/activate

# Create .env file
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
# IMPORTANT: For local development, ensure REDIS_HOST=localhost (not 'redis')
#            and POSTGRES_HOST=localhost (not Docker service names)

# Start Redis (required for Celery and caching)
# Option 1: Using Docker (recommended)
docker-compose up -d redis

# Option 2: Install Redis locally
# sudo apt-get install redis-server && sudo systemctl start redis-server

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# In another terminal, run Celery worker
cd backend && source venv/bin/activate
celery -A app.celery_app worker --loglevel=info
```

The bootstrap script will:
- Create a Python virtual environment
- Install CPU-only PyTorch (no GPU/CUDA dependencies)
- Install all dependencies
- Verify disk space and PostgreSQL connectivity
- Print helpful diagnostics

### Docker Setup

For containerized development:

### Step 1: Initial Setup

```bash
# Clone or navigate to the project directory
cd "AI-Powered Business Intelligence Analyst"

# Run setup (creates .env file)
make setup
```

### Step 2: Configure Environment

Edit `backend/.env` and add your Groq API key:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

**Optional**: Customize LLM model selection for intelligent routing:
```bash
# Simple queries (fast, cost-effective)
LLM_MODEL_SIMPLE=llama-3.1-8b-instant
# Medium queries (balanced)
LLM_MODEL_MEDIUM=llama-3.3-70b-versatile
# Complex queries (powerful)
LLM_MODEL_COMPLEX=openai/gpt-oss-120b
```

See `backend/MODELS.md` for available models and configuration details.

### Step 3: Build and Start Services

```bash
# Build Docker images
make build

# Start all services
make up

# Wait for services to be healthy (about 30 seconds)
# Check logs if needed
make logs
```

### Step 4: Initialize Database

```bash
# Create database schema
make migrate

# Seed with sample data
make seed
```

### Step 5: Verify Setup

```bash
# Check health endpoint
curl http://localhost:8001/health

# Test query endpoint
curl -X POST http://localhost:8001/api/v1/queries/ \
  -H "Content-Type: application/json" \
  -d '{"query": "How many customers do we have?"}'
```

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make setup` | Initial setup (creates .env file) |
| `make build` | Build Docker images |
| `make up` | Start all services |
| `make down` | Stop all services |
| `make restart` | Restart all services |
| `make logs` | View logs from all services |
| `make migrate` | Create database schema |
| `make seed` | Seed database with sample data |
| `make db-reset` | Reset database (drop and recreate) |
| `make shell-backend` | Open shell in backend container |
| `make shell-db` | Open PostgreSQL shell |
| `make test` | Run tests |
| `make clean` | Remove all containers, volumes, and images |

## API Endpoints

### Health Check
```
GET /health
```

### Submit Query
```
POST /api/v1/queries/
Content-Type: application/json

{
  "query": "Show me all customers from New York",
  "user_id": "optional_user_id"
}
```

Response:
```json
{
  "query_id": "uuid",
  "natural_language_query": "Show me all customers from New York",
  "generated_sql": "SELECT * FROM customers WHERE city = 'New York' LIMIT 100",
  "results": [...],
  "execution_time_ms": 1234.56
}
```

## Development

### Local Development

1. **Bootstrap your environment**:
   ```bash
   ./scripts/dev_setup.sh
   ```

2. **Activate virtual environment**:
   ```bash
   cd backend && source venv/bin/activate
   ```

3. **Run the application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

4. **Run Celery worker** (in another terminal):
   ```bash
   cd backend && source venv/bin/activate
   celery -A app.celery_app worker --loglevel=info
   ```

### Docker Development

### Running Tests

```bash
# Local
cd backend && source venv/bin/activate && pytest -v

# Docker
make test
```

### Accessing Services

- **FastAPI Backend**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

### Database Access

```bash
# PostgreSQL shell
make shell-db

# Example query
SELECT COUNT(*) FROM customers;
```

### Viewing Logs

```bash
# All services
make logs

# Specific service
docker-compose logs -f backend
```

## Embeddings: Local vs API-Based

This project uses **local embeddings** by default, which requires PyTorch and sentence-transformers to run on your machine.

### Why PyTorch is Included

- **Local Embeddings**: The system generates embeddings using `sentence-transformers/all-MiniLM-L6-v2` model
- **CPU-Only Build**: We use CPU-only PyTorch (~500MB) instead of GPU version (~2GB+) to:
  - Eliminate CUDA/GPU dependencies
  - Reduce disk usage
  - Enable development on any machine
- **RAG Functionality**: Embeddings power the RAG (Retrieval-Augmented Generation) system for schema-aware query generation

### Switching to API-Based Embeddings

To remove PyTorch entirely and use API-based embeddings:

1. **Remove torch dependencies**:
   ```bash
   pip uninstall torch transformers sentence-transformers
   ```

2. **Install an embedding API client** (e.g., OpenAI, Cohere):
   ```bash
   pip install openai  # or cohere
   ```

3. **Modify embedding code** in `backend/app/core/pgvector_client.py`:
   - Replace `SentenceTransformer` with API calls
   - Example: Use OpenAI's `text-embedding-ada-002` or Cohere's embedding API

4. **Benefits of API embeddings**:
   - No local model downloads (~500MB+ saved)
   - No PyTorch dependency
   - Potentially better quality embeddings
   - **Trade-off**: Requires API key and network calls

### Current Architecture

- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Storage**: PostgreSQL with pgvector extension
- **Usage**: Schema embeddings for RAG, query history for learning

## Technology Stack

- **FastAPI**: Modern async web framework
- **PostgreSQL**: Relational database with pgvector extension
- **Redis**: Caching and message broker
- **Celery**: Distributed task queue
- **SQLAlchemy**: ORM with async support
- **sentence-transformers**: Local embedding generation (CPU-only)
- **PyTorch**: CPU-only build for sentence-transformers (~500MB, no CUDA)
- **Groq API**: Fast LLM inference (Llama 3)
- **Docker**: Containerization (optional)

## Next Steps / Roadmap

Future work can focus on:

- **Benchmark expansion & tuning**: Grow the benchmark set toward 500+ queries, refine scoring, and capture per‑category analytics over time.
- **Advanced security & governance**: Fine‑grained RBAC, row/column‑level security, and stronger auditing around sensitive queries.
- **Autoscaling & resilience**: Horizontal scaling for the backend and workers, plus more robust circuit‑breaking and backoff strategies.
- **Frontend enhancements**: Richer query builder, saved dashboards, and admin controls for cost/performance tuning.

## Troubleshooting

### Services won't start
- Check if ports are already in use
- Verify Docker is running
- Check logs: `make logs`

### Database connection errors
- Ensure PostgreSQL container is healthy: `docker-compose ps`
- Wait a few seconds after `make up` before running migrations

### Prometheus / Grafana issues
- Ensure both services are running: `docker-compose ps prometheus grafana`
- Prometheus UI: `http://localhost:9090` (check backend scrape status)
- Grafana UI: `http://localhost:3001` (default login admin/admin; change in production)

### LLM API errors
- Verify GROQ_API_KEY is set in `backend/.env`
- Check API key validity at https://console.groq.com

### PyTorch/Embedding errors
- Ensure CPU-only PyTorch is installed: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
- Verify installation: `python -c "import torch; print(torch.__version__)"`
- Check disk space (embeddings model requires ~500MB)
- If issues persist, consider switching to API-based embeddings (see Embeddings section above)

### Redis connection errors (local development)
- **Error**: `Cannot connect to redis:6379` or `Temporary failure in name resolution`
- **Cause**: `.env` file has `REDIS_HOST=redis` (Docker service name) instead of `localhost`
- **Fix**: Update `backend/.env` to use `REDIS_HOST=localhost` for local development
- **Verify**: Ensure Redis is running: `redis-cli ping` should return `PONG`
- **Start Redis**: `docker-compose up -d redis` or install locally with `sudo apt-get install redis-server`

### PostgreSQL connection errors (local development)
- **Error**: Connection refused or hostname resolution failures
- **Cause**: `.env` file may have Docker service names instead of `localhost`
- **Fix**: For local development, use `POSTGRES_HOST=localhost` in `backend/.env`
- **Verify**: Ensure PostgreSQL is running: `sudo systemctl status postgresql`

## CI/CD Notes

For CI/CD pipelines, disable pip cache to reduce build time and disk usage:

```bash
# Disable pip cache during installation
pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
pip install --no-cache-dir -r requirements.txt
```

This is already configured in the Dockerfile for containerized builds.

## License

This project is part of a technical specification implementation for educational/portfolio purposes.

