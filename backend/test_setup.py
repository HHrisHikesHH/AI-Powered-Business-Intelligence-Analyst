"""
Simple test script to verify backend setup.
Run this after starting services to verify everything works.
"""
import asyncio
import sys
from app.core.database import init_db, get_db
from app.core.redis_client import init_redis, cache_service
from app.core.pgvector_client import init_pgvector, vector_store
from app.core.llm_client import llm_service
from sqlalchemy import text


async def test_database():
    """Test database connection and query."""
    print("Testing database connection...")
    try:
        await init_db()
        async for db in get_db():
            result = await db.execute(text("SELECT COUNT(*) as count FROM customers"))
            row = result.fetchone()
            print(f"✓ Database connected - Found {row[0]} customers")
            break
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


async def test_redis():
    """Test Redis connection and caching."""
    print("Testing Redis connection...")
    try:
        await init_redis()
        await cache_service.set("test_key", {"message": "Hello Redis"}, ttl=60)
        result = await cache_service.get("test_key")
        if result and result.get("message") == "Hello Redis":
            print("✓ Redis connected and caching works")
            return True
        else:
            print("✗ Redis cache test failed")
            return False
    except Exception as e:
        print(f"✗ Redis test failed: {e}")
        return False


async def test_pgvector():
    """Test pgvector connection."""
    print("Testing pgvector connection...")
    try:
        await init_pgvector()
        # Test embedding generation
        embedding = vector_store.generate_embedding("test query")
        if len(embedding) > 0:
            print(f"✓ pgvector connected - Generated embedding of size {len(embedding)}")
            return True
        else:
            print("✗ pgvector embedding generation failed")
            return False
    except Exception as e:
        print(f"✗ pgvector test failed: {e}")
        print("  Make sure pgvector extension is installed in PostgreSQL")
        print("  Run: CREATE EXTENSION IF NOT EXISTS vector;")
        return False


async def test_llm():
    """Test LLM (Groq) connection."""
    print("Testing LLM (Groq) connection...")
    try:
        response = await llm_service.generate_completion(
            "Say 'Hello' if you can read this.",
            max_tokens=10
        )
        if response:
            print(f"✓ LLM connected - Response: {response[:50]}...")
            return True
        else:
            print("✗ LLM test failed - No response")
            return False
    except Exception as e:
        print(f"✗ LLM test failed: {e}")
        print("  Make sure GROQ_API_KEY is set in backend/.env")
        return False


async def main():
    """Run all tests."""
    print("=" * 50)
    print("Backend Setup Verification")
    print("=" * 50)
    print()
    
    results = []
    results.append(await test_database())
    results.append(await test_redis())
    results.append(await test_pgvector())
    results.append(await test_llm())
    
    print()
    print("=" * 50)
    if all(results):
        print("✓ All tests passed! Backend is ready.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

