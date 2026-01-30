# AI-Powered Business Intelligence Analyst

An intelligent multi-agent system that enables non-technical users to query databases using natural language, receiving actionable insights, visualizations, and recommendations.

## Phase 1, Week 1: Core Infrastructure

This implementation provides the complete backend infrastructure setup as specified in the technical specification document.

## Architecture Overview

The system uses a containerized microservices architecture:

- **PostgreSQL**: Database for storing e-commerce data
- **Redis**: Caching layer and Celery message broker
- **ChromaDB**: Vector store for schema embeddings and RAG
- **FastAPI**: Async Python web framework for API endpoints
- **Celery**: Distributed task queue for async operations
- **Groq API**: Multiple LLM models with intelligent routing (Llama 3.1, Llama 3.3, GPT-OSS, Qwen, etc.)

## Project Structure

```
.
├── docker-compose.yml          # Docker Compose configuration
├── Makefile                    # Convenience commands
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
└── backend/
    ├── Dockerfile              # Backend container definition
    ├── requirements.txt        # Python dependencies
    ├── .env.example           # Environment variables template
    ├── app/
    │   ├── __init__.py
    │   ├── main.py            # FastAPI application entry point
    │   ├── celery_app.py      # Celery configuration
    │   ├── core/              # Core configuration and utilities
    │   │   ├── __init__.py
    │   │   ├── config.py      # Application settings
    │   │   ├── database.py    # PostgreSQL connection
    │   │   ├── redis_client.py # Redis caching
    │   │   ├── chromadb_client.py # ChromaDB vector store
    │   │   └── llm_client.py  # Groq/Llama 3 client
    │   ├── api/               # API routes
    │   │   └── v1/
    │   │       ├── router.py
    │   │       └── endpoints/
    │   │           └── queries.py # Query endpoints
    │   ├── services/          # Business logic
    │   │   └── query_executor.py # Query execution service
    │   └── tasks/             # Celery tasks
    │       └── embedding_tasks.py
    └── database/
        ├── init.sql           # Database schema
        └── seed_data.sql      # Sample e-commerce data
```

## Key Files Explained

### `docker-compose.yml`
Orchestrates all services with proper health checks and dependencies. Services include:
- PostgreSQL with persistent volume
- Redis with persistence
- ChromaDB for vector storage
- FastAPI backend
- Celery worker

### `backend/app/main.py`
FastAPI application with:
- CORS middleware
- Health check endpoints
- API router integration
- Startup/shutdown event handlers

### `backend/app/core/config.py`
Pydantic-based configuration management that loads environment variables and provides typed settings.

### `backend/app/core/database.py`
SQLAlchemy async engine setup for PostgreSQL with connection pooling.

### `backend/app/core/redis_client.py`
Redis client with async operations and caching service for query results and schema data.

### `backend/app/core/chromadb_client.py`
ChromaDB integration with sentence-transformers for embeddings. Provides vector store operations for RAG.

### `backend/app/core/llm_client.py`
Groq API client with support for multiple models. Features:
- Intelligent model routing based on query complexity
- Support for all Groq production and preview models
- Automatic model selection (simple → medium → complex)
- Manual model override capability
- Cost optimization through smart routing

### `backend/app/services/query_executor.py`
Simplified query execution service (Week 1 implementation):
- Natural language to SQL conversion using LLM
- SQL execution with safety checks
- Result formatting

### `backend/database/init.sql`
Creates the e-commerce schema:
- `customers`: Customer information
- `products`: Product catalog
- `orders`: Order records
- `order_items`: Order line items

### `backend/database/seed_data.sql`
Populates database with realistic sample data:
- 20 customers
- 20 products across multiple categories
- 26 orders with various statuses
- Associated order items

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
- **ChromaDB**: http://localhost:8000

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

## Next Steps (Future Phases)

- **Phase 1, Week 2**: Basic NL-to-SQL pipeline with improved accuracy
- **Phase 2**: Multi-agent system with specialized agents
- **Phase 3**: Production features (optimization, caching, frontend)
- **Phase 4**: Admin dashboard and monitoring

## Troubleshooting

### Services won't start
- Check if ports are already in use
- Verify Docker is running
- Check logs: `make logs`

### Database connection errors
- Ensure PostgreSQL container is healthy: `docker-compose ps`
- Wait a few seconds after `make up` before running migrations

### ChromaDB connection issues
- ChromaDB may take 30-60 seconds to fully start
- Check health: `curl http://localhost:8000/api/v1/heartbeat`

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

