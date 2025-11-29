"""Embedding generation for text chunks using 100% open-source local models."""

import logging
from typing import List, Optional
import numpy as np

from ..config import get_config

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """
    Generate embeddings using local sentence-transformers models.

    OPEN-SOURCE ONLY: Uses sentence-transformers library.
    NO PAID APIS: OpenAI embeddings support removed.

    Recommended models (all free, local):
    - all-MiniLM-L6-v2 (384-dim, fast, good quality)
    - all-mpnet-base-v2 (768-dim, best quality)
    - all-MiniLM-L12-v2 (384-dim, balanced)
    - paraphrase-multilingual-MiniLM-L12-v2 (multilingual)
    """

    def __init__(self):
        """Initialize local embedding model."""
        self.config = get_config()
        self.model_name = self.config.embeddings.model
        self.batch_size = self.config.embeddings.batch_size
        self.normalize = self.config.embeddings.normalize

        # Validate no paid API models
        if self.model_name.startswith("text-embedding"):
            logger.error(f"OpenAI embedding model not supported: {self.model_name}")
            logger.error("OpenAI API has been removed (paid service)")
            logger.error("Use local models: all-MiniLM-L6-v2, all-mpnet-base-v2, etc.")
            raise ValueError(
                f"OpenAI embeddings not supported. Use local sentence-transformers models.\n"
                f"Recommended: all-MiniLM-L6-v2 (fast) or all-mpnet-base-v2 (quality)"
            )

        self.model = None
        self._load_model()

        # Get actual dimension from loaded model
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.dimension}")

    def _load_model(self):
        """Load the local embedding model using sentence-transformers."""
        logger.info(f"Loading local embedding model: {self.model_name}")

        try:
            from sentence_transformers import SentenceTransformer

            # Determine device from config
            device = self.config.system.device

            # Load model (downloads from HuggingFace if not cached)
            self.model = SentenceTransformer(self.model_name, device=device)

            logger.info(f"✓ Loaded local embedding model: {self.model_name}")
            logger.info(f"  Model will run on: {self.model.device}")

        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            logger.error("Make sure sentence-transformers is installed: pip install sentence-transformers")
            logger.error("Model will be downloaded from HuggingFace on first use")
            raise
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts using local model.

        Args:
            texts: List of text strings

        Returns:
            Numpy array of embeddings (n_texts, dimension)
        """
        if not texts:
            # Return empty array with correct shape (0, dimension)
            return np.array([]).reshape(0, self.dimension)

        return self._embed_local(texts)

    def _embed_local(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings using local sentence-transformers model.

        This runs entirely locally with no API calls.
        """
        logger.debug(f"Generating embeddings for {len(texts)} texts")

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=len(texts) > 10,  # Show progress for large batches
                normalize_embeddings=self.normalize,
                convert_to_numpy=True
            )

            logger.info(f"✓ Generated {len(embeddings)} embeddings locally (no API calls)")
            return embeddings

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def _normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit length."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / norms
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query.
        
        Args:
            query: Query string
            
        Returns:
            Embedding vector
        """
        embeddings = self.embed([query])
        return embeddings[0]

