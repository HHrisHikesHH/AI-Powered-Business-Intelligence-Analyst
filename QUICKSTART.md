# Quick Start Guide

Get the AI-Powered Business Intelligence Analyst backend running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Groq API key (free at https://console.groq.com)

## Step-by-Step Setup

### 1. Get Your Groq API Key

1. Visit https://console.groq.com
2. Sign up for a free account
3. Create an API key
4. Copy the key (you'll need it in step 3)

### 2. Initial Setup

```bash
# Navigate to project directory
cd "AI-Powered Business Intelligence Analyst"

# Run setup (creates .env file)
make setup
```

### 3. Configure API Key

Edit `backend/.env` and replace `your_groq_api_key_here` with your actual Groq API key:

```bash
GROQ_API_KEY=gsk_your_actual_key_here
```

### 4. Build and Start Services

```bash
# Build Docker images (first time only, takes a few minutes)
make build

# Start all services
make up

# Wait 30-60 seconds for services to start
# Check status with:
docker-compose ps
```

### 5. Initialize Database

```bash
# Create database schema
make migrate

# Seed with sample data
make seed
```

### 6. Verify Setup

```bash
# Test the API
curl http://localhost:8001/health

# Or run the test script
docker-compose exec backend python test_setup.py
```

### 7. Test a Query

```bash
curl -X POST http://localhost:8001/api/v1/queries/ \
  -H "Content-Type: application/json" \
  -d '{"query": "How many customers do we have?"}'
```

Expected response:
```json
{
  "query_id": "...",
  "natural_language_query": "How many customers do we have?",
  "generated_sql": "SELECT COUNT(*) FROM customers LIMIT 100",
  "results": [{"count": 20}],
  "execution_time_ms": 1234.56
}
```

## Access Points

- **API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs (Interactive Swagger UI)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **ChromaDB**: http://localhost:8000

## Common Commands

```bash
# View logs
make logs

# Stop services
make down

# Restart services
make restart

# Reset database (drop and recreate)
make db-reset

# Access PostgreSQL shell
make shell-db

# Access backend container shell
make shell-backend
```

## Troubleshooting

### Services won't start
- Check if ports 5432, 6379, 8000, 8001 are available
- Verify Docker is running: `docker ps`
- Check logs: `make logs`

### Database errors
- Wait 10-15 seconds after `make up` before running migrations
- Check PostgreSQL is healthy: `docker-compose ps postgres`
- Try resetting: `make db-reset`

### LLM API errors
- Verify `GROQ_API_KEY` is set in `backend/.env`
- Check key is valid at https://console.groq.com
- Test with: `docker-compose exec backend python test_setup.py`

### ChromaDB connection issues
- ChromaDB takes 30-60 seconds to fully start
- Check health: `curl http://localhost:8000/api/v1/heartbeat`
- View logs: `docker-compose logs chromadb`

## Next Steps

Once everything is running:

1. Explore the API docs at http://localhost:8001/docs
2. Try different queries:
   - "Show me all products in the Electronics category"
   - "What's the total revenue from orders?"
   - "List customers from New York"
3. Check the database:
   ```bash
   make shell-db
   SELECT * FROM customers LIMIT 5;
   ```

## Architecture Overview

```
User Query → FastAPI → Query Executor → LLM (Groq/Llama 3)
                                    ↓
                              SQL Generation
                                    ↓
                              PostgreSQL
                                    ↓
                              Results + Caching (Redis)
                                    ↓
                              Vector Store (ChromaDB)
```

## What's Next?

This is Phase 1, Week 1 - Core Infrastructure. Future phases will add:
- Multi-agent system (Query Understanding, SQL Generation, Analysis, Visualization)
- Advanced RAG with hybrid search
- Self-healing and error recovery
- Frontend interface
- Admin dashboard

