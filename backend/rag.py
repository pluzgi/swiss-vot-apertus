"""
RAG (Retrieval-Augmented Generation) Pipeline
Semantic search and context retrieval for Swiss voting initiatives
"""

from typing import List, Dict, Optional
import logging

from vector_store import get_vector_store
from embeddings import get_embedding_model
from database import get_db_session
from models import Initiative

logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG pipeline for voting assistant queries"""

    def __init__(self):
        self.vector_store = get_vector_store()
        self.embedding_model = get_embedding_model()

    def retrieve_context(
        self,
        query: str,
        language: str = "de",
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict]:
        """
        Retrieve relevant context from brochure texts

        Args:
            query: User query
            language: Preferred language (de, fr, it)
            top_k: Number of chunks to retrieve
            score_threshold: Minimum similarity score

        Returns:
            List of context dicts with text, metadata, and scores
        """
        logger.info(f"RAG Query: '{query}' (lang={language}, top_k={top_k})")

        try:
            # Query vector store
            results = self.vector_store.query(
                query_texts=[query],
                n_results=top_k,
                where={"language": language}  # Filter by language
            )

            # Process results
            contexts = []
            if results and 'ids' in results and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    # ChromaDB returns distances (lower is better)
                    # Convert to similarity score (higher is better)
                    distance = results['distances'][0][i] if 'distances' in results else 0.0
                    similarity = 1.0 - min(distance, 1.0)

                    if similarity >= score_threshold:
                        context = {
                            "text": results['documents'][0][i],
                            "metadata": results['metadatas'][0][i],
                            "chunk_id": results['ids'][0][i],
                            "similarity": round(similarity, 4),
                            "distance": round(distance, 4)
                        }
                        contexts.append(context)

            logger.info(f"Retrieved {len(contexts)} relevant chunks")
            return contexts

        except Exception as e:
            logger.error(f"❌ Context retrieval failed: {e}")
            return []

    def retrieve_with_fallback(
        self,
        query: str,
        preferred_language: str = "de",
        top_k: int = 5
    ) -> List[Dict]:
        """
        Retrieve context with language fallback

        Args:
            query: User query
            preferred_language: Preferred language
            top_k: Number of chunks to retrieve

        Returns:
            List of context dicts
        """
        # Try preferred language first
        contexts = self.retrieve_context(
            query=query,
            language=preferred_language,
            top_k=top_k
        )

        # If not enough results, try other languages
        if len(contexts) < top_k // 2:
            logger.info(f"Insufficient results in {preferred_language}, trying other languages...")

            other_langs = [lang for lang in ["de", "fr", "it"] if lang != preferred_language]

            for lang in other_langs:
                additional = self.retrieve_context(
                    query=query,
                    language=lang,
                    top_k=top_k - len(contexts)
                )
                contexts.extend(additional)

                if len(contexts) >= top_k:
                    break

        return contexts[:top_k]

    def get_initiative_metadata(self, vote_ids: List[str]) -> Dict[str, Dict]:
        """
        Get initiative metadata for retrieved vote_ids

        Args:
            vote_ids: List of vote IDs

        Returns:
            Dict mapping vote_id to initiative metadata
        """
        metadata = {}

        try:
            with get_db_session() as session:
                for vote_id in set(vote_ids):  # Remove duplicates
                    initiative = session.query(Initiative).filter(
                        Initiative.vote_id == vote_id
                    ).first()

                    if initiative:
                        metadata[vote_id] = {
                            "vote_id": vote_id,
                            "title": initiative.schlagwort or initiative.offizieller_titel,
                            "date": initiative.abstimmungsdatum,
                            "policy_area": initiative.politikbereich,
                            "position_bundesrat": initiative.position_bundesrat,
                            "parteiparolen": initiative.parteiparolen,
                            "details_url": initiative.details_url,
                            "pdf_url": initiative.abstimmungsbuechlein_pdf
                        }

        except Exception as e:
            logger.error(f"❌ Failed to fetch initiative metadata: {e}")

        return metadata

    def format_context_for_llm(self, contexts: List[Dict]) -> str:
        """
        Format retrieved contexts into a prompt for the LLM

        Args:
            contexts: List of retrieved context dicts

        Returns:
            Formatted context string
        """
        if not contexts:
            return "Keine relevanten Informationen gefunden."

        # Group by initiative
        by_initiative = {}
        for ctx in contexts:
            vote_id = ctx["metadata"]["vote_id"]
            if vote_id not in by_initiative:
                by_initiative[vote_id] = []
            by_initiative[vote_id].append(ctx)

        # Format
        formatted_parts = []
        for vote_id, chunks in by_initiative.items():
            title = chunks[0]["metadata"].get("initiative_title", vote_id)
            formatted_parts.append(f"\n**Initiative {vote_id}: {title}**\n")

            for chunk in chunks:
                formatted_parts.append(chunk["text"])
                formatted_parts.append("")  # Empty line

        return "\n".join(formatted_parts)

    def query_with_context(
        self,
        query: str,
        language: str = "de",
        top_k: int = 5,
        include_metadata: bool = True
    ) -> Dict:
        """
        Complete RAG query with context and metadata

        Args:
            query: User query
            language: Language preference
            top_k: Number of chunks to retrieve
            include_metadata: Whether to include initiative metadata

        Returns:
            Dict with contexts, formatted context, and optional metadata
        """
        # Retrieve contexts
        contexts = self.retrieve_with_fallback(
            query=query,
            preferred_language=language,
            top_k=top_k
        )

        # Get vote IDs from contexts
        vote_ids = [ctx["metadata"]["vote_id"] for ctx in contexts]

        # Get initiative metadata
        metadata = {}
        if include_metadata and vote_ids:
            metadata = self.get_initiative_metadata(vote_ids)

        # Format context for LLM
        formatted_context = self.format_context_for_llm(contexts)

        return {
            "query": query,
            "language": language,
            "contexts": contexts,
            "formatted_context": formatted_context,
            "initiative_metadata": metadata,
            "num_contexts": len(contexts)
        }


# Singleton instance
_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAGPipeline singleton"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
