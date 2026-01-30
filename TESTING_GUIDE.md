# Testing Guide: Backend Capabilities

This guide explains how to test the three core backend capabilities:
1. **Backend can accept queries**
2. **Backend can connect to database**
3. **Backend can call LLM APIs**

## Prerequisites

Before testing, ensure:
- Services are running (PostgreSQL, Redis, Backend)
- Environment variables are configured (especially `GROQ_API_KEY`)
- Database is initialized and seeded with data

### Quick Setup Check

```bash
# Check if services are running (Docker)
docker-compose ps

# Or check health endpoint
curl http://localhost:8001/health
```

## Method 1: Automated Test Script (Recommended)

The project includes a dedicated test script that verifies all three capabilities.

### Run the Capabilities Test

**Option A: Local Development**
```bash
cd backend
source venv/bin/activate
python test_capabilities.py
```

**Option B: Docker**
```bash
docker-compose exec backend python test_capabilities.py
```

**Option C: Direct Execution**
```bash
cd backend
python3 test_capabilities.py
```

### What It Tests

1. **Query Endpoint Structure** - Verifies the `/api/v1/queries/` endpoint exists and is properly configured
2. **Database Connection** - Tests PostgreSQL connectivity
3. **LLM API Calls** - Tests Groq API integration

### Expected Output

```
============================================================
Testing Core Capabilities
============================================================

============================================================
TEST 1: Query Endpoint (Accept Queries)
============================================================
✓ Query endpoint exists: SUCCESS
  Available routes: ['/api/v1/queries/', ...]

============================================================
TEST 2: Database Connection
============================================================
✓ Database connection: SUCCESS

============================================================
TEST 3: LLM API Calls
============================================================
✓ LLM API call: SUCCESS
  Response: Hello...

============================================================
SUMMARY
============================================================
Query Endpoint: ✓ PASS
Database Connection: ✓ PASS
LLM API Calls: ✓ PASS
============================================================

✓ All tests passed! All three capabilities are working.
```

## Method 2: Comprehensive Setup Test

For a more detailed test of all backend components:

```bash
cd backend
source venv/bin/activate
python test_setup.py
```

This tests:
- Database connection and query execution
- Redis connection and caching
- pgvector connection and embeddings
- LLM (Groq) API calls

## Method 3: Manual API Testing

### Test 1: Accept Queries (HTTP Endpoint)

**Using curl:**
```bash
curl -X POST http://localhost:8001/api/v1/queries/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many customers do we have?",
    "user_id": "test_user"
  }'
```

**Expected Response:**
```json
{
  "query_id": "uuid-here",
  "natural_language_query": "How many customers do we have?",
  "generated_sql": "SELECT COUNT(*) FROM customers LIMIT 10000",
  "results": [{"count": 20}],
  "execution_time_ms": 1234.56
}
```

**Using FastAPI Interactive Docs:**
1. Open http://localhost:8001/docs
2. Navigate to `POST /api/v1/queries/`
3. Click "Try it out"
4. Enter a query: `"How many customers do we have?"`
5. Click "Execute"

### Test 2: Database Connection

**Check Health Endpoint:**
```bash
curl http://localhost:8001/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "pgvector": "connected"
}
```

**Direct Database Query Test:**
```bash
# Using PostgreSQL shell
make shell-db

# Then run:
SELECT COUNT(*) FROM customers;
```

**Or test via Python:**
```python
import asyncio
from app.core.database import init_db, get_db
from sqlalchemy import text

async def test_db():
    await init_db()
    async for db in get_db():
        result = await db.execute(text("SELECT COUNT(*) FROM customers"))
        row = result.fetchone()
        print(f"Customers: {row[0]}")
        break

asyncio.run(test_db())
```

### Test 3: LLM API Calls

**Direct LLM Test:**
```python
import asyncio
from app.core.llm_client import llm_service

async def test_llm():
    response = await llm_service.generate_completion(
        "Say 'Hello' if you can read this.",
        max_tokens=10
    )
    print(f"LLM Response: {response}")

asyncio.run(test_llm())
```

**Test via Query Endpoint (which uses LLM):**
```bash
curl -X POST http://localhost:8001/api/v1/queries/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the total revenue?"}'
```

This will:
1. Accept the query ✓
2. Call LLM to generate SQL ✓
3. Execute SQL against database ✓

## Method 4: Integration Test (All Three Together)

The query endpoint tests all three capabilities in one request:

```bash
curl -X POST http://localhost:8001/api/v1/queries/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me the top 5 products by price"
  }'
```

**This single request verifies:**
1. ✅ **Accepts queries** - Endpoint receives and processes the request
2. ✅ **Calls LLM APIs** - Generates SQL from natural language
3. ✅ **Connects to database** - Executes SQL and returns results

## Troubleshooting

### Query Endpoint Not Working

**Symptoms:**
- 404 Not Found
- Connection refused

**Solutions:**
```bash
# Check if backend is running
docker-compose ps backend

# Check logs
docker-compose logs backend

# Verify endpoint exists
curl http://localhost:8001/docs
```

### Database Connection Fails

**Symptoms:**
- "Failed to connect to database"
- Connection timeout

**Solutions:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Verify connection settings in backend/.env
cat backend/.env | grep POSTGRES

# Test connection manually
psql -h localhost -U postgres -d ai_bi_db -c "SELECT 1;"
```

### LLM API Calls Fail

**Symptoms:**
- "GROQ_API_KEY is not set"
- API authentication errors

**Solutions:**
```bash
# Verify API key is set
cat backend/.env | grep GROQ_API_KEY

# Test API key validity
# Visit https://console.groq.com to verify your key

# Check LLM service logs
docker-compose logs backend | grep -i llm
```

## Test Scripts Reference

### `test_capabilities.py`
- **Purpose:** Tests the three core capabilities
- **Location:** `backend/test_capabilities.py`
- **Usage:** `python test_capabilities.py`

### `test_setup.py`
- **Purpose:** Comprehensive backend setup verification
- **Location:** `backend/test_setup.py`
- **Usage:** `python test_setup.py`

## Quick Test Checklist

- [ ] Services are running (`docker-compose ps` or check processes)
- [ ] Health endpoint responds (`curl http://localhost:8001/health`)
- [ ] Database is initialized (`make migrate` and `make seed`)
- [ ] GROQ_API_KEY is set in `backend/.env`
- [ ] Run `test_capabilities.py` - all tests pass
- [ ] Query endpoint accepts requests (test via curl or /docs)
- [ ] LLM generates SQL (check `generated_sql` in response)
- [ ] Database returns results (check `results` in response)

## Next Steps

Once all three capabilities are verified:
- Test with more complex queries
- Monitor performance metrics
- Check caching behavior
- Review logs for any warnings

For more information, see:
- `CAPABILITIES_VERIFICATION.md` - Implementation details
- `README.md` - Setup and configuration
- `START_SERVICES.md` - Service management

