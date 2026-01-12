"""
Embedding Service for Semantic Search.

Uses sentence-transformers to generate embeddings for building code articles.
These embeddings enable semantic (meaning-based) search using pgvector.

Model: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
- Optimized for semantic similarity
- Small size (~80MB), fast inference
- Good performance on technical/legal text
"""
import logging
from typing import List, Optional, Tuple
from functools import lru_cache
import threading

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_model = None
_model_lock = threading.Lock()
_model_loaded = False

# Model configuration
MODEL_NAME = "all-MiniLM-L6-v2"  # 384 dimensions, good balance of speed/quality
EMBEDDING_DIM = 384


def get_embedding_model():
    """Lazy load the sentence-transformers model."""
    global _model, _model_loaded

    if _model_loaded:
        return _model

    with _model_lock:
        if _model_loaded:
            return _model

        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {MODEL_NAME}")
            _model = SentenceTransformer(MODEL_NAME)
            _model_loaded = True
            logger.info(f"Embedding model loaded: {MODEL_NAME} ({EMBEDDING_DIM} dimensions)")
            return _model

        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            return None
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return None


def is_model_available() -> bool:
    """Check if the embedding model is available."""
    try:
        import sentence_transformers
        return True
    except ImportError:
        return False


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        self._model = None

    def _ensure_model_loaded(self) -> bool:
        """Ensure the model is loaded."""
        if self._model is None:
            self._model = get_embedding_model()
        return self._model is not None

    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed (will be truncated if too long)

        Returns:
            List of floats (embedding vector) or None if error
        """
        if not self._ensure_model_loaded():
            return None

        try:
            # Truncate very long text (model has ~256 token limit)
            if len(text) > 2000:
                text = text[:2000]

            embedding = self._model.encode(text, convert_to_numpy=True)
            return embedding.tolist()

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors (or None for failed texts)
        """
        if not self._ensure_model_loaded():
            return [None] * len(texts)

        try:
            # Truncate long texts
            truncated = [t[:2000] if len(t) > 2000 else t for t in texts]

            embeddings = self._model.encode(
                truncated,
                convert_to_numpy=True,
                batch_size=batch_size,
                show_progress_bar=len(texts) > 100
            )

            return [e.tolist() for e in embeddings]

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [None] * len(texts)

    def embed_query(self, query: str) -> Optional[List[float]]:
        """
        Generate embedding for a search query.

        For some models, query embedding differs from document embedding.
        This uses the same encoding but is provided for API clarity.

        Args:
            query: Search query text

        Returns:
            Embedding vector or None if error
        """
        return self.embed_text(query)

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between -1 and 1 (1 = identical)
        """
        try:
            import numpy as np
            e1 = np.array(embedding1)
            e2 = np.array(embedding2)

            # Cosine similarity
            dot_product = np.dot(e1, e2)
            norm1 = np.linalg.norm(e1)
            norm2 = np.linalg.norm(e2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return float(dot_product / (norm1 * norm2))

        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0

    def get_model_info(self) -> dict:
        """Get information about the embedding model."""
        return {
            "model_name": MODEL_NAME,
            "embedding_dim": EMBEDDING_DIM,
            "loaded": _model_loaded,
            "available": is_model_available(),
        }


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
