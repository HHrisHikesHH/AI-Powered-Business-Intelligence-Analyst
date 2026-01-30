"""
Test script to verify the three core capabilities:
1. Backend can accept queries
2. Backend can connect to database
3. Backend can call LLM APIs
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_database_connection():
    """Test 2: Database connection"""
    print("\n" + "="*60)
    print("TEST 2: Database Connection")
    print("="*60)
    try:
        from app.core.database import init_db
        await init_db()
        print("✓ Database connection: SUCCESS")
        return True
    except Exception as e:
        print(f"✗ Database connection: FAILED - {e}")
        return False

async def test_llm_api():
    """Test 3: LLM API calls"""
    print("\n" + "="*60)
    print("TEST 3: LLM API Calls")
    print("="*60)
    try:
        from app.core.llm_client import llm_service
        
        # Test a simple LLM call
        response = await llm_service.generate_completion(
            "Say 'Hello' if you can read this.",
            max_tokens=10
        )
        if response:
            print(f"✓ LLM API call: SUCCESS")
            print(f"  Response: {response[:50]}...")
            return True
        else:
            print("✗ LLM API call: FAILED - No response")
            return False
    except Exception as e:
        print(f"✗ LLM API call: FAILED - {e}")
        return False

def test_query_endpoint():
    """Test 1: Query endpoint (API structure)"""
    print("\n" + "="*60)
    print("TEST 1: Query Endpoint (Accept Queries)")
    print("="*60)
    try:
        from app.api.v1.endpoints.queries import router, QueryRequest, QueryResponse
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        # Create a test app
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/queries")
        
        # Test that the endpoint exists
        client = TestClient(app)
        
        # Check if endpoint is registered
        routes = [r.path for r in app.routes]
        if "/api/v1/queries/" in routes:
            print("✓ Query endpoint exists: SUCCESS")
            print(f"  Available routes: {routes}")
            return True
        else:
            print("✗ Query endpoint: FAILED - Endpoint not found")
            return False
    except Exception as e:
        print(f"✗ Query endpoint: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Testing Core Capabilities")
    print("="*60)
    
    results = []
    
    # Test 1: Query endpoint structure
    results.append(test_query_endpoint())
    
    # Test 2: Database connection
    results.append(await test_database_connection())
    
    # Test 3: LLM API
    results.append(await test_llm_api())
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Query Endpoint: {'✓ PASS' if results[0] else '✗ FAIL'}")
    print(f"Database Connection: {'✓ PASS' if results[1] else '✗ FAIL'}")
    print(f"LLM API Calls: {'✓ PASS' if results[2] else '✗ FAIL'}")
    print("="*60)
    
    if all(results):
        print("\n✓ All tests passed! All three capabilities are working.")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

