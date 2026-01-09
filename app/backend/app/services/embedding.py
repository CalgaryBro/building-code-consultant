"""
Embedding service for semantic search using sentence-transformers.

This service generates embeddings for code articles to enable
semantic/similarity search in EXPLORE mode.
"""
import numpy as np
from typing import List, Optional
from functools import lru_cache


class EmbeddingService:
    """
    Service for generating text embeddings.

    Uses sentence-transformers with all-MiniLM-L6-v2 model (384 dimensions)
    which provides a good balance of speed and quality for search.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector (384 dimensions)
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def get_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100
        )
        return embeddings.tolist()

    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        a = np.array(embedding1)
        b = np.array(embedding2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service instance."""
    return EmbeddingService()
