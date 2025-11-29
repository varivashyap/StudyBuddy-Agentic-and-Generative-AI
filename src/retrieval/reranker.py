"""Reranking module using cross-encoder models."""

import logging
from typing import List, Dict, Tuple, Optional

from sentence_transformers import CrossEncoder

from ..config import get_config

logger = logging.getLogger(__name__)


class Reranker:
    """Rerank retrieved documents using cross-encoder."""
    
    def __init__(self):
        """Initialize reranker."""
        self.config = get_config()
        self.enabled = self.config.retrieval.reranker_enabled
        self.model_name = self.config.retrieval.reranker_model
        self.top_m = self.config.retrieval.top_m
        
        self.model = None
        if self.enabled:
            self._load_model()
    
    def _load_model(self):
        """Load cross-encoder model."""
        logger.info(f"Loading reranker model: {self.model_name}")

        # Determine device from config
        device = self.config.system.device

        self.model = CrossEncoder(self.model_name, device=device)
        logger.info(f"Reranker model loaded on {device}")
    
    def rerank(
        self,
        query: str,
        documents: List[Tuple[Dict, float]],
        top_m: Optional[int] = None
    ) -> List[Tuple[Dict, float]]:
        """
        Rerank documents based on query relevance.
        
        Args:
            query: Query string
            documents: List of (document, score) tuples
            top_m: Number of top documents to return (uses config default if None)
            
        Returns:
            Reranked list of (document, score) tuples
        """
        if not self.enabled or not documents:
            return documents[:top_m] if top_m else documents
        
        if top_m is None:
            top_m = self.top_m
        
        # Prepare pairs for cross-encoder
        pairs = []
        for doc, _ in documents:
            text = doc.get('text', '')
            pairs.append([query, text])
        
        # Get reranking scores
        scores = self.model.predict(pairs)
        
        # Combine documents with new scores
        reranked = []
        for i, (doc, _) in enumerate(documents):
            reranked.append((doc, float(scores[i])))
        
        # Sort by new scores
        reranked.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Reranked {len(documents)} documents, returning top {top_m}")
        return reranked[:top_m]

