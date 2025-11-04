"""
Text Embedding Generation
Uses sentence-transformers for multilingual embeddings
"""

from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging
import torch

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Wrapper for sentence-transformers embedding model"""

    def __init__(self, model_name: str = None):
        """
        Initialize embedding model

        Args:
            model_name: HuggingFace model name (default from settings)
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()

    def _load_model(self):
        """Load the sentence-transformers model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            logger.info(f"Using device: {self.device}")

            self.model = SentenceTransformer(
                self.model_name,
                device=self.device
            )

            logger.info(f"✅ Model loaded successfully")
            logger.info(f"   Embedding dimension: {self.model.get_sentence_embedding_dimension()}")

        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings for texts

        Args:
            texts: Single text or list of texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar

        Returns:
            List of embedding vectors
        """
        if self.model is None:
            raise ValueError("Model not loaded")

        # Convert single string to list
        if isinstance(texts, str):
            texts = [texts]

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )

            # Convert to list of lists
            return embeddings.tolist()

        except Exception as e:
            logger.error(f"❌ Encoding failed: {e}")
            raise

    def encode_single(self, text: str) -> List[float]:
        """
        Encode a single text

        Args:
            text: Input text

        Returns:
            Embedding vector as list
        """
        result = self.encode([text], batch_size=1)
        return result[0]

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        if self.model is None:
            raise ValueError("Model not loaded")
        return self.model.get_sentence_embedding_dimension()


# Singleton instance
_embedding_model = None


def get_embedding_model() -> EmbeddingModel:
    """Get or create EmbeddingModel singleton"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """
    Split text into overlapping chunks

    Args:
        text: Input text
        chunk_size: Maximum characters per chunk (default from settings)
        overlap: Overlap between chunks (default from settings)

    Returns:
        List of text chunks
    """
    if chunk_size is None:
        chunk_size = settings.CHUNK_SIZE
    if overlap is None:
        overlap = settings.CHUNK_OVERLAP

    if not text or len(text) == 0:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Find the end of the last complete sentence before chunk_size
        if end < len(text):
            # Look for sentence endings: . ! ?
            last_period = text.rfind('.', start, end)
            last_exclaim = text.rfind('!', start, end)
            last_question = text.rfind('?', start, end)

            sentence_end = max(last_period, last_exclaim, last_question)

            if sentence_end > start:
                end = sentence_end + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position with overlap
        start = end - overlap if end < len(text) else len(text)

    return chunks


def prepare_brochure_for_indexing(
    vote_id: str,
    brochure_texts: dict,
    chunk_size: int = None,
    overlap: int = None
) -> List[dict]:
    """
    Prepare brochure texts for vector indexing

    Args:
        vote_id: Initiative vote ID
        brochure_texts: Dict with language keys (de, fr, it) and text values
        chunk_size: Chunk size for splitting
        overlap: Overlap between chunks

    Returns:
        List of dicts with chunks and metadata
    """
    prepared_chunks = []

    for lang, text in brochure_texts.items():
        if not text:
            continue

        chunks = chunk_text(text, chunk_size, overlap)

        for idx, chunk in enumerate(chunks):
            prepared_chunks.append({
                "vote_id": vote_id,
                "language": lang,
                "chunk_index": idx,
                "text": chunk,
                "chunk_id": f"{vote_id}_{lang}_{idx}"
            })

    return prepared_chunks
