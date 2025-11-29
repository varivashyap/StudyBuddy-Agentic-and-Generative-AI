"""Hybrid retrieval combining vector search and BM25."""

import logging
from typing import List, Dict, Tuple, Optional
import numpy as np

from rank_bm25 import BM25Okapi

from ..config import get_config
from ..representation.vector_store import VectorStore
from ..representation.embeddings import EmbeddingModel

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Combine vector similarity and BM25 for retrieval."""
    
    def __init__(self, vector_store: VectorStore, embedding_model: EmbeddingModel):
        """
        Initialize hybrid retriever.
        
        Args:
            vector_store: Vector store instance
            embedding_model: Embedding model instance
        """
        self.config = get_config()
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        
        self.hybrid_enabled = self.config.retrieval.hybrid_enabled
        self.vector_weight = self.config.retrieval.vector_weight
        self.bm25_weight = self.config.retrieval.bm25_weight
        self.top_k = self.config.retrieval.top_k
        
        self.bm25 = None
        self._build_bm25_index()
    
    def _build_bm25_index(self):
        """Build BM25 index from documents in vector store."""
        if not self.hybrid_enabled or not self.vector_store.documents:
            return
        
        logger.info("Building BM25 index")
        
        # Tokenize documents
        tokenized_docs = []
        for doc in self.vector_store.documents:
            text = doc.get('text', '')
            tokens = text.lower().split()
            tokenized_docs.append(tokens)
        
        self.bm25 = BM25Okapi(tokenized_docs)
        logger.info(f"Built BM25 index with {len(tokenized_docs)} documents")
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Tuple[Dict, float]]:
        """
        Retrieve relevant documents using hybrid search.
        
        Args:
            query: Query string
            top_k: Number of results (uses config default if None)
            
        Returns:
            List of (document, score) tuples
        """
        if top_k is None:
            top_k = self.top_k
        
        if not self.hybrid_enabled or self.bm25 is None:
            # Vector-only retrieval
            return self._vector_retrieve(query, top_k)
        
        # Hybrid retrieval
        vector_results = self._vector_retrieve(query, top_k * 2)
        bm25_results = self._bm25_retrieve(query, top_k * 2)
        
        # Combine and rerank
        combined = self._combine_results(vector_results, bm25_results)
        
        # Return top-k
        return combined[:top_k]
    
    def _vector_retrieve(self, query: str, top_k: int) -> List[Tuple[Dict, float]]:
        """Retrieve using vector similarity."""
        query_embedding = self.embedding_model.embed_query(query)
        results = self.vector_store.search(query_embedding, top_k)
        return results
    
    def _bm25_retrieve(self, query: str, top_k: int) -> List[Tuple[Dict, float]]:
        """Retrieve using BM25."""
        if self.bm25 is None:
            return []
        
        query_tokens = query.lower().split()
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if idx < len(self.vector_store.documents):
                doc = self.vector_store.documents[idx]
                score = float(scores[idx])
                results.append((doc, score))
        
        return results
    
    def _combine_results(
        self,
        vector_results: List[Tuple[Dict, float]],
        bm25_results: List[Tuple[Dict, float]]
    ) -> List[Tuple[Dict, float]]:
        """
        Combine vector and BM25 results with weighted scoring.
        
        Uses Reciprocal Rank Fusion (RRF) for combining rankings.
        """
        # Normalize scores
        vector_scores = self._normalize_scores([s for _, s in vector_results])
        bm25_scores = self._normalize_scores([s for _, s in bm25_results])
        
        # Create score map
        score_map = {}
        
        # Add vector scores
        for i, (doc, _) in enumerate(vector_results):
            doc_id = id(doc)  # Use object id as key
            score_map[doc_id] = {
                'doc': doc,
                'vector_score': vector_scores[i],
                'bm25_score': 0.0
            }
        
        # Add BM25 scores
        for i, (doc, _) in enumerate(bm25_results):
            doc_id = id(doc)
            if doc_id in score_map:
                score_map[doc_id]['bm25_score'] = bm25_scores[i]
            else:
                score_map[doc_id] = {
                    'doc': doc,
                    'vector_score': 0.0,
                    'bm25_score': bm25_scores[i]
                }
        
        # Combine scores
        combined = []
        for doc_id, data in score_map.items():
            combined_score = (
                self.vector_weight * data['vector_score'] +
                self.bm25_weight * data['bm25_score']
            )
            combined.append((data['doc'], combined_score))
        
        # Sort by combined score
        combined.sort(key=lambda x: x[1], reverse=True)
        
        return combined
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to [0, 1] range."""
        if not scores:
            return []
        
        scores = np.array(scores)
        min_score = scores.min()
        max_score = scores.max()
        
        if max_score == min_score:
            return [1.0] * len(scores)
        
        normalized = (scores - min_score) / (max_score - min_score)
        return normalized.tolist()
    
    def update_index(self):
        """Rebuild BM25 index (call after adding documents)."""
        self._build_bm25_index()

