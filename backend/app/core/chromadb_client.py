"""
ChromaDB client for vector storage and retrieval.
Used for storing schema embeddings and query history for RAG.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger
from app.core.config import settings
from typing import List, Optional, Dict
from sentence_transformers import SentenceTransformer
import numpy as np

# Initialize sentence transformer model
embedding_model: Optional[SentenceTransformer] = None
chroma_client: Optional[chromadb.ClientAPI] = None


def get_embedding_model() -> SentenceTransformer:
    """Get or initialize the embedding model."""
    global embedding_model
    if embedding_model is None:
        logger.info("Loading sentence transformer model...")
        embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        logger.info("Embedding model loaded successfully")
    return embedding_model


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or initialize ChromaDB client."""
    global chroma_client
    if chroma_client is None:
        try:
            chroma_client = chromadb.HttpClient(
                host=settings.CHROMADB_HOST,
                port=settings.CHROMADB_PORT
            )
            logger.info("ChromaDB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
    return chroma_client


def init_chromadb():
    """Initialize ChromaDB connection and verify connectivity."""
    try:
        client = get_chroma_client()
        # Test connection
        client.heartbeat()
        logger.info("ChromaDB connection verified")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        raise


class VectorStore:
    """Service for vector storage operations."""
    
    def __init__(self, collection_name: str = "schema_embeddings"):
        self.collection_name = collection_name
        self.client = get_chroma_client()
        self.embedding_model = get_embedding_model()
        self.collection = None
    
    def _get_collection(self):
        """Get or create collection."""
        if self.collection is None:
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Schema and query embeddings"}
                )
        return self.collection
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def add_schema_element(self, element_id: str, text: str, metadata: Dict):
        """Add schema element (table, column) to vector store."""
        collection = self._get_collection()
        embedding = self.generate_embedding(text)
        collection.add(
            ids=[element_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar schema elements."""
        collection = self._get_collection()
        query_embedding = self.generate_embedding(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        return formatted_results


vector_store = VectorStore()

