# Architecture Documentation

## Overview

This document explains the key components and file structure of the AI-Powered Business Intelligence Analyst backend infrastructure (Phase 1, Week 1).

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │PostgreSQL│  │  Redis   │  │ ChromaDB │  │ FastAPI  │   │
│  │  :5432   │  │  :6379   │  │  :8000   │  │  :8001   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────┐                                              │
│  │  Celery  │                                              │
│  │  Worker  │                                              │
│  └──────────┘                                              │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
.
├── docker-compose.yml          # Service orchestration
├── Makefile                    # Development commands
├── README.md                   # Main documentation
├── QUICKSTART.md               # Quick start guide
├── ARCHITECTURE.md             # This file
└── backend/
    ├── Dockerfile              # Backend container definition
    ├── requirements.txt        # Python dependencies
    ├── .env.example           # Environment template
    ├── test_setup.py          # Setup verification script
    ├── app/
    │   ├── main.py            # FastAPI application
    │   ├── celery_app.py      # Celery configuration
    │   ├── core/              # Core services
    │   ├── api/               # API routes
    │   ├── services/          # Business logic
    │   └── tasks/             # Celery tasks
    └── database/
        ├── init.sql           # Schema definition
        └── seed_data.sql      # Sample data
```

## Key Components

### 1. Docker Compose (`docker-compose.yml`)

Orchestrates all services:
- **PostgreSQL**: Database with persistent volume
- **Redis**: Cache and Celery broker
- **ChromaDB**: Vector store for embeddings
- **FastAPI Backend**: Main application server
- **Celery Worker**: Async task processor

**Key Features:**
- Health checks for all services
- Proper dependency ordering
- Volume persistence
- Network isolation

### 2. FastAPI Application (`backend/app/main.py`)

Main entry point that:
- Initializes all services on startup
- Sets up CORS middleware
- Registers API routes
- Provides health check endpoints

**Startup Sequence:**
1. Initialize PostgreSQL connection
2. Initialize Redis connection
3. Initialize ChromaDB connection
4. Verify all services are healthy

### 3. Core Services (`backend/app/core/`)

#### `config.py`
- Pydantic-based configuration management
- Loads environment variables
- Provides typed settings with validation
- Constructs connection URLs

#### `database.py`
- SQLAlchemy async engine setup
- Connection pooling (10 connections, 20 overflow)
- Async session management
- Database initialization

#### `redis_client.py`
- Async Redis client
- Caching service with TTL support
- JSON serialization for complex objects
- Connection lifecycle management

#### `chromadb_client.py`
- ChromaDB HTTP client
- Sentence transformer integration (all-MiniLM-L6-v2)
- Vector store operations
- Embedding generation and similarity search

#### `llm_client.py`
- Groq API client for Llama 3
- Text completion generation
- Structured JSON output support
- Error handling and retry logic

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

### 5. Business Logic (`backend/app/services/`)

#### `query_executor.py`
Simplified query execution for Week 1:
1. **SQL Generation**: Uses LLM to convert natural language to SQL
2. **SQL Validation**: Ensures only SELECT queries
3. **Execution**: Runs SQL against PostgreSQL
4. **Result Formatting**: Converts rows to JSON

**Future Enhancements (later phases):**
- Multi-agent pipeline
- Schema-aware SQL generation
- Query optimization
- Result analysis

### 6. Celery Tasks (`backend/app/tasks/`)

#### `embedding_tasks.py`
Async tasks for:
- Schema embedding generation
- Query history storage
- Batch processing

**Usage:**
```python
from app.tasks.embedding_tasks import generate_schema_embeddings_task
generate_schema_embeddings_task.delay(schema_elements)
```

### 7. Database (`backend/database/`)

#### `init.sql`
Creates e-commerce schema:
- `customers`: Customer information
- `products`: Product catalog
- `orders`: Order records
- `order_items`: Order line items
- Indexes for performance

#### `seed_data.sql`
Populates database with:
- 20 customers across various cities
- 20 products in 4 categories (Electronics, Clothing, Home & Kitchen, Books)
- 26 orders with different statuses
- Associated order items with proper relationships

## Data Flow

### Query Processing Flow (Week 1)

```
1. User submits natural language query
   ↓
2. FastAPI endpoint receives request
   ↓
3. Check Redis cache (if exists, return cached result)
   ↓
4. QueryExecutor service:
   a. Generate SQL using LLM (Groq/Llama 3)
   b. Validate SQL (SELECT only, safety checks)
   c. Execute against PostgreSQL
   d. Format results
   ↓
5. Cache results in Redis (1 hour TTL)
   ↓
6. Return response to user
```

### Future Multi-Agent Flow (Later Phases)

```
1. Query Understanding Agent → Extract intent, tables, filters
   ↓
2. SQL Generation Agent → Generate SQL with RAG context
   ↓
3. SQL Validator → Syntax, permissions, safety checks
   ↓
4. Query Executor → Run SQL
   ↓
5. Analysis Agent → Generate insights
   ↓
6. Visualization Agent → Create chart configs
   ↓
7. Return comprehensive response
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
- Celery message broker
- Simple key-value operations
- Persistence support

### Why ChromaDB?
- Open-source vector database
- Easy integration
- Good performance for RAG
- HTTP API for containerization

### Why Groq (Llama 3)?
- Free/open-source LLM access
- Fast inference (optimized hardware)
- Good SQL generation capabilities
- Cost-effective for development

### Why Celery?
- Distributed task processing
- Async operations (embeddings, heavy processing)
- Scalable worker architecture
- Integration with Redis

## Configuration

### Environment Variables

All configuration is managed through `backend/.env`:

```bash
# Database
POSTGRES_HOST=postgres
POSTGRES_USER=ai_bi_user
POSTGRES_PASSWORD=ai_bi_password
POSTGRES_DB=ai_bi_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# ChromaDB
CHROMADB_HOST=chromadb
CHROMADB_PORT=8000

# LLM
GROQ_API_KEY=your_key_here

# Application
ENVIRONMENT=development
BACKEND_PORT=8001
```

## Security Considerations

### Current Implementation (Week 1)
- SQL injection prevention: Only SELECT queries allowed
- Row limits: Automatic LIMIT 10000
- Read-only operations: No INSERT/UPDATE/DELETE
- Environment variable secrets: API keys in .env

### Future Enhancements
- User authentication and authorization
- Query permission checks
- Rate limiting
- Input sanitization
- Audit logging

## Performance Optimizations

### Current (Week 1)
- Connection pooling (PostgreSQL)
- Redis caching (1 hour TTL)
- Async operations throughout
- Docker containerization

### Future
- Intelligent model routing (cost optimization)
- Query result pagination
- Schema embedding caching
- Batch processing for embeddings

## Monitoring & Observability

### Current
- Loguru for structured logging
- Health check endpoints
- Error tracking in logs

### Future
- LangSmith integration for agent tracing
- Prometheus metrics
- Cost tracking per query
- Performance dashboards

## Testing

### Setup Verification
```bash
docker-compose exec backend python test_setup.py
```

Tests:
- Database connectivity
- Redis caching
- ChromaDB embeddings
- LLM API access

### Manual Testing
```bash
# Health check
curl http://localhost:8001/health

# Query test
curl -X POST http://localhost:8001/api/v1/queries/ \
  -H "Content-Type: application/json" \
  -d '{"query": "How many customers?"}'
```

## Development Workflow

1. **Make changes** to code in `backend/app/`
2. **Hot reload** enabled (FastAPI auto-reloads)
3. **View logs**: `make logs`
4. **Test changes**: Use API docs at http://localhost:8001/docs
5. **Reset database**: `make db-reset` (if needed)

## Next Steps (Future Phases)

### Phase 1, Week 2
- Improved SQL generation accuracy
- Schema-aware query generation
- Better error handling

### Phase 2
- Multi-agent system implementation
- Query Understanding Agent
- Analysis Agent
- Visualization Agent

### Phase 3
- Frontend interface
- Advanced caching
- Cost optimization
- Performance tuning

### Phase 4
- Admin dashboard
- Monitoring and analytics
- Documentation
- Production deployment

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

4. **ChromaDB connection issues**
   - Wait 30-60 seconds for startup
   - Check health endpoint
   - Verify network configuration

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Groq API Documentation](https://console.groq.com/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

