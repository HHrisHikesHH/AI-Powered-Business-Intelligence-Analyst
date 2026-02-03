"""
Tests for hybrid RAG implementation (vector + keyword + graph-based).
"""
import pytest
from app.services.hybrid_rag import HybridRAG
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_hybrid_rag_vector_search():
    """Test vector search component."""
    mock_db = AsyncMock()
    hybrid_rag = HybridRAG(mock_db)
    
    query_understanding = {
        "tables": ["customers"],
        "columns": ["name", "email"]
    }
    
    with patch.object(hybrid_rag.vector_store, 'search_similar', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [
            {"document": "Table: customers", "metadata": {"type": "table", "name": "customers"}}
        ]
        
        results = await hybrid_rag._vector_search("customers", n_results=5)
        
        assert len(results) > 0
        mock_search.assert_called_once()


@pytest.mark.asyncio
async def test_hybrid_rag_keyword_search():
    """Test keyword search component."""
    mock_db = AsyncMock()
    hybrid_rag = HybridRAG(mock_db)
    
    # Mock keyword index
    hybrid_rag._keyword_index = {
        "customers": {
            "document": "Table: customers",
            "metadata": {"type": "table", "name": "customers", "columns": ["id", "name"]},
            "type": "table",
            "name": "customers"
        }
    }
    
    results = await hybrid_rag._keyword_search(["customers"], ["name"], n_results=5)
    
    assert len(results) > 0
    assert results[0]["metadata"]["name"] == "customers"


@pytest.mark.asyncio
async def test_hybrid_rag_graph_retrieval():
    """Test graph-based retrieval."""
    mock_db = AsyncMock()
    hybrid_rag = HybridRAG(mock_db)
    
    # Mock schema graph
    hybrid_rag._schema_graph = {
        "orders": {"customers", "order_items"},
        "customers": {"orders"},
        "order_items": {"orders", "products"}
    }
    
    with patch.object(hybrid_rag, '_get_table_schema', new_callable=AsyncMock) as mock_get_schema:
        mock_get_schema.return_value = {
            "document": "Table: customers",
            "metadata": {"type": "table", "name": "customers"}
        }
        
        results = await hybrid_rag._graph_based_retrieval(["orders"], n_results=5)
        
        # Should retrieve related tables (customers, order_items)
        assert len(results) > 0
        assert mock_get_schema.call_count > 0


@pytest.mark.asyncio
async def test_hybrid_rag_combine_results():
    """Test result combination and deduplication."""
    mock_db = AsyncMock()
    hybrid_rag = HybridRAG(mock_db)
    
    vector_results = [
        {"metadata": {"type": "table", "name": "customers"}, "source": "vector"}
    ]
    
    keyword_results = [
        {"metadata": {"type": "table", "name": "customers"}, "source": "keyword"}
    ]
    
    graph_results = [
        {"metadata": {"type": "table", "name": "orders"}, "source": "graph"}
    ]
    
    combined = hybrid_rag._combine_results(
        vector_results, keyword_results, graph_results, n_results=10
    )
    
    # Should deduplicate (customers appears in both vector and keyword)
    assert len(combined) >= 2  # At least customers and orders
    # Keyword should have priority
    assert combined[0].get("source") == "keyword" or combined[0].get("source") == "vector"


@pytest.mark.asyncio
async def test_hybrid_rag_format_context():
    """Test context formatting."""
    mock_db = AsyncMock()
    hybrid_rag = HybridRAG(mock_db)
    
    results = [
        {
            "metadata": {
                "type": "table",
                "name": "customers",
                "columns": ["id", "name", "email"]
            }
        },
        {
            "metadata": {
                "type": "column",
                "table": "customers",
                "name": "email",
                "data_type": "varchar"
            }
        }
        ]
    
    context = hybrid_rag.format_context(results)
    
    assert "customers" in context
    assert "id" in context or "name" in context or "email" in context

