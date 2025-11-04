"""
ChromaDB Vector Store Client
Manages vector embeddings for brochure texts
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import logging

from config import settings, get_chromadb_url

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB client for managing voting brochure embeddings"""

    def __init__(self):
        """Initialize ChromaDB client"""
        self.client = None
        self.collection = None
        self._connect()

    def _connect(self):
        """Connect to ChromaDB"""
        try:
            chroma_url = get_chromadb_url()
            logger.info(f"Connecting to ChromaDB at {chroma_url}")

            self.client = chromadb.HttpClient(
                host=settings.CHROMADB_HOST,
                port=settings.CHROMADB_PORT
            )

            # Test connection
            self.client.heartbeat()
            logger.info("✅ ChromaDB connection successful")

        except Exception as e:
            logger.error(f"❌ ChromaDB connection failed: {e}")
            raise

    def get_or_create_collection(self, collection_name: Optional[str] = None):
        """Get or create the brochure collection"""
        if collection_name is None:
            collection_name = settings.CHROMADB_COLLECTION

        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Swiss voting brochure texts"}
            )
            logger.info(f"✅ Collection '{collection_name}' ready ({self.collection.count()} documents)")
            return self.collection

        except Exception as e:
            logger.error(f"❌ Failed to get/create collection: {e}")
            raise

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ):
        """
        Add documents to collection

        Args:
            documents: List of text chunks
            metadatas: List of metadata dicts (vote_id, language, chunk_index, etc.)
            ids: List of unique IDs
            embeddings: Optional pre-computed embeddings (if None, ChromaDB will compute)
        """
        if self.collection is None:
            raise ValueError("Collection not initialized. Call get_or_create_collection() first")

        try:
            if embeddings:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                # Let ChromaDB compute embeddings
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )

            logger.info(f"✅ Added {len(documents)} documents to collection")

        except Exception as e:
            logger.error(f"❌ Failed to add documents: {e}")
            raise

    def query(
        self,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> Dict:
        """
        Query the collection for similar documents

        Args:
            query_texts: List of query strings
            n_results: Number of results to return
            where: Filter on metadata (e.g., {"language": "de"})
            where_document: Filter on document content

        Returns:
            Dict with ids, documents, metadatas, distances
        """
        if self.collection is None:
            raise ValueError("Collection not initialized")

        try:
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            return results

        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            raise

    def get_by_ids(self, ids: List[str]) -> Dict:
        """Get documents by their IDs"""
        if self.collection is None:
            raise ValueError("Collection not initialized")

        try:
            return self.collection.get(ids=ids)
        except Exception as e:
            logger.error(f"❌ Failed to get documents: {e}")
            raise

    def get_by_metadata(self, where: Dict) -> Dict:
        """Get documents by metadata filter"""
        if self.collection is None:
            raise ValueError("Collection not initialized")

        try:
            return self.collection.get(where=where)
        except Exception as e:
            logger.error(f"❌ Failed to get documents: {e}")
            raise

    def delete_by_vote_id(self, vote_id: str):
        """Delete all documents for a specific initiative"""
        if self.collection is None:
            raise ValueError("Collection not initialized")

        try:
            self.collection.delete(where={"vote_id": vote_id})
            logger.info(f"✅ Deleted documents for vote_id: {vote_id}")
        except Exception as e:
            logger.error(f"❌ Failed to delete documents: {e}")
            raise

    def count(self) -> int:
        """Get total number of documents in collection"""
        if self.collection is None:
            raise ValueError("Collection not initialized")

        return self.collection.count()

    def reset_collection(self):
        """Delete and recreate collection - USE WITH CAUTION!"""
        if self.collection is None:
            return

        try:
            collection_name = self.collection.name
            self.client.delete_collection(name=collection_name)
            logger.warning(f"⚠️  Deleted collection: {collection_name}")
            self.get_or_create_collection(collection_name)
            logger.info(f"✅ Recreated empty collection: {collection_name}")
        except Exception as e:
            logger.error(f"❌ Failed to reset collection: {e}")
            raise


# Singleton instance
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get or create VectorStore singleton"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        _vector_store.get_or_create_collection()
    return _vector_store
