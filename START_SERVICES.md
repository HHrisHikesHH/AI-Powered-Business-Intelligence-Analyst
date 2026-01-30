# How to Start Backend and Connected Services

## Quick Start (Local Development)

### Prerequisites
- PostgreSQL running locally (port 5432)
- Python 3.11+ installed
- Dependencies installed (see below)
- `.env` file configured with database credentials and GROQ_API_KEY

---

## Step-by-Step Instructions

### 1. Start Redis (Required for caching and Celery)

**Option A: Using Docker (Recommended)**
```bash
# Start only Redis
docker-compose up -d redis

# Verify Redis is running
docker-compose ps redis
# Should show: ai_bi_redis ... Up ... healthy
```

**Option B: Install and Run Redis Locally**
```bash
# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis-server
# Or: redis-server

# Verify
redis-cli ping
# Should return: PONG
```

---

### 2. Install Python Dependencies

```bash
cd backend

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Configure Environment Variables

Make sure your `.env` file in the project root has:

```bash
# PostgreSQL (local database)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database

# Redis (local)
REDIS_HOST=localhost
REDIS_PORT=6379

# Groq API Key (required)
GROQ_API_KEY=your_groq_api_key_here

# Optional: Environment
ENVIRONMENT=development
```

---

### 4. Initialize Database (First Time Only)

```bash
# Make sure PostgreSQL is running
sudo systemctl status postgresql

# Run migrations
make migrate

# Seed sample data
make seed
```

---

### 5. Start the Backend

**Option A: Using Uvicorn Directly**
```bash
cd backend
source venv/bin/activate  # If using venv

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Option B: Using Python Module**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Option C: Using Makefile (if configured)**
```bash
# You can add this to Makefile if needed
make run-backend
```

The backend will start on: **http://localhost:8001**

---

### 6. Start Celery Worker (Optional - for async tasks)

**In a new terminal:**
```bash
cd backend
source venv/bin/activate  # If using venv

# Start Celery worker
celery -A app.celery_app worker --loglevel=info
```

---

## Verify Everything is Running

### Check Backend Health
```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "pgvector": "connected"
}
```

### Test Query Endpoint
```bash
curl -X POST http://localhost:8001/api/v1/queries/ \
  -H "Content-Type: application/json" \
  -d '{"query": "How many customers do we have?"}'
```

### Check API Documentation
Open in browser: **http://localhost:8001/docs**

---

## Service Status Checklist

- [ ] PostgreSQL running (port 5432)
- [ ] Redis running (port 6379)
- [ ] Backend running (port 8001)
- [ ] Celery worker running (optional)
- [ ] Database schema created (`make migrate`)
- [ ] Sample data seeded (`make seed`)
- [ ] GROQ_API_KEY set in `.env`

---

## Troubleshooting

### Backend won't start
```bash
# Check if port 8001 is available
lsof -i :8001

# Check logs
# Look for error messages in terminal where you started uvicorn
```

### Database connection errors
```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql

# Test connection manually
psql -h localhost -U your_user -d your_database

# Check .env file has correct credentials
cat .env | grep POSTGRES
```

### Redis connection errors
```bash
# Verify Redis is running
redis-cli ping

# Check if Redis is accessible
redis-cli -h localhost -p 6379 ping
```

### Missing dependencies
```bash
# Reinstall dependencies
cd backend
pip install -r requirements.txt --upgrade
```

---

## Quick Commands Reference

```bash
# Start Redis only
docker-compose up -d redis

# Start backend (in backend directory)
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Start Celery worker (in backend directory)
celery -A app.celery_app worker --loglevel=info

# Check all services
docker-compose ps
ps aux | grep uvicorn
ps aux | grep celery

# Stop services
docker-compose down  # Stops Redis
# Press Ctrl+C to stop uvicorn/celery
```

---

## Alternative: Run Everything in Docker

If you prefer to run everything in Docker:

```bash
# Start all services (backend, redis, celery)
make up

# View logs
make logs

# Stop all services
make down
```

Note: Make sure your `.env` file has correct PostgreSQL credentials for Docker to connect to your local database.

