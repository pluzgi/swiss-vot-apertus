"""
OpenWebUI Pipeline Integration
Custom pipeline for Swiss Voting Assistant with RAG
"""

from typing import List, Dict, Optional, AsyncIterator
import logging

from apertus_client import get_apertus_client
from rag import get_rag_pipeline
from prompts import create_chat_prompt, detect_language

logger = logging.getLogger(__name__)


class SwissVotingPipeline:
    """
    Custom pipeline for OpenWebUI integration
    Combines RAG retrieval with Apertus LLM
    """

    def __init__(self):
        self.name = "Swiss Voting Assistant"
        self.apertus_client = get_apertus_client()
        self.rag_pipeline = get_rag_pipeline()

    async def inlet(self, body: Dict) -> Dict:
        """
        Pre-process incoming request
        Called before LLM generation

        Args:
            body: Request body from OpenWebUI

        Returns:
            Modified request body
        """
        logger.info("Pipeline inlet: pre-processing request")

        messages = body.get("messages", [])
        if not messages:
            return body

        # Get the last user message
        last_message = messages[-1]
        if last_message.get("role") != "user":
            return body

        user_query = last_message.get("content", "")

        # Detect language
        language = detect_language(user_query)
        logger.info(f"Detected language: {language}")

        # Check if this query should use RAG
        should_use_rag = self._should_use_rag(user_query)

        if should_use_rag:
            logger.info("Using RAG pipeline for context retrieval")

            # Retrieve context
            try:
                rag_result = self.rag_pipeline.query_with_context(
                    query=user_query,
                    language=language,
                    top_k=5,
                    include_metadata=True
                )

                # Enrich messages with RAG context
                enriched_messages = create_chat_prompt(
                    user_query=user_query,
                    rag_result=rag_result,
                    language=language
                )

                body["messages"] = enriched_messages
                logger.info(f"RAG context added: {rag_result['num_contexts']} chunks")

            except Exception as e:
                logger.error(f"RAG retrieval failed: {e}")
                # Continue without RAG on error

        return body

    async def outlet(self, body: Dict) -> Dict:
        """
        Post-process LLM response
        Called after LLM generation

        Args:
            body: Response body from LLM

        Returns:
            Modified response body
        """
        logger.info("Pipeline outlet: post-processing response")

        # Add metadata or citations if needed
        # For now, pass through unchanged

        return body

    def _should_use_rag(self, query: str) -> bool:
        """
        Determine if query should use RAG

        Args:
            query: User query

        Returns:
            True if RAG should be used
        """
        query_lower = query.lower()

        # Keywords that indicate voting-related queries
        rag_keywords = [
            "initiative", "abstimmung", "volksinitiative",
            "votation", "vote", "referendum",
            "initiative", "votazione",
            "was ist", "worum geht", "erkläre",
            "qu'est-ce", "expliquer",
            "che cosa", "spiegare",
            "argumente", "arguments", "argomenti",
            "pro", "contra", "pour", "contre",
            "position", "empfehlung", "recommandation"
        ]

        return any(keyword in query_lower for keyword in rag_keywords)


# Global pipeline instance
_pipeline = None


def get_pipeline() -> SwissVotingPipeline:
    """Get or create pipeline singleton"""
    global _pipeline
    if _pipeline is None:
        _pipeline = SwissVotingPipeline()
    return _pipeline
