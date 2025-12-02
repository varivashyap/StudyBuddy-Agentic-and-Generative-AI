"""Vector store for efficient similarity search."""

import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
import pickle

import faiss

from ..config import get_config

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store with metadata."""
    
    def __init__(self, dimension: Optional[int] = None):
        """
        Initialize vector store.

        Args:
            dimension: Embedding dimension (required - pass from EmbeddingModel)
        """
        self.config = get_config()

        # Dimension must be provided (no longer in config, auto-detected from model)
        if dimension is None:
            raise ValueError(
                "Dimension must be provided to VectorStore. "
                "Pass dimension from EmbeddingModel: VectorStore(dimension=embedding_model.dimension)"
            )

        self.dimension = dimension
        self.backend = self.config.get("vector_store.backend", "faiss")

        self.index = None
        self.documents = []  # Store original documents with metadata
        self.n_probe = self.config.get("vector_store.faiss.n_probe", 16)

        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize FAISS index."""
        logger.info(f"Initializing FAISS index with dimension {self.dimension}")
        
        # Start with a flat index (will upgrade to IVF when we have enough vectors)
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product for normalized vectors
        self.is_trained = True
    
    def add(self, embeddings: np.ndarray, documents: List[Dict[str, any]]):
        """
        Add embeddings and documents to the store.
        
        Args:
            embeddings: Numpy array of embeddings (n, dimension)
            documents: List of document dicts with metadata
        """
        if len(embeddings) != len(documents):
            raise ValueError("Number of embeddings must match number of documents")

        # Handle empty case
        if len(embeddings) == 0:
            logger.warning("No embeddings to add (empty input)")
            return

        # Ensure embeddings are 2D array with correct shape
        if embeddings.ndim == 1:
            raise ValueError(f"Embeddings must be 2D array, got shape {embeddings.shape}")

        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, got {embeddings.shape[1]}"
            )

        # Ensure embeddings are float32
        embeddings = embeddings.astype('float32')
        
        # Check if we should upgrade to IVF index
        total_vectors = self.index.ntotal + len(embeddings)
        if total_vectors >= 1000 and isinstance(self.index, faiss.IndexFlatIP):
            logger.info("Upgrading to IVF index")
            self._upgrade_to_ivf(total_vectors)
        
        # Add to index
        self.index.add(embeddings)
        self.documents.extend(documents)
        
        logger.info(f"Added {len(embeddings)} vectors. Total: {self.index.ntotal}")
    
    def _upgrade_to_ivf(self, n_vectors: int):
        """Upgrade from flat index to IVF index."""
        # Calculate n_list (number of clusters)
        n_list = int(np.sqrt(n_vectors))
        n_list = max(n_list, 100)  # Minimum 100 clusters
        
        logger.info(f"Creating IVF index with {n_list} clusters")
        
        # Create IVF index
        quantizer = faiss.IndexFlatIP(self.dimension)
        new_index = faiss.IndexIVFFlat(quantizer, self.dimension, n_list)
        
        # Train on existing vectors if any
        if self.index.ntotal > 0:
            # Extract existing vectors
            vectors = np.zeros((self.index.ntotal, self.dimension), dtype='float32')
            for i in range(self.index.ntotal):
                vectors[i] = self.index.reconstruct(i)
            
            # Train new index
            new_index.train(vectors)
            new_index.add(vectors)
        
        new_index.nprobe = self.n_probe
        self.index = new_index
        self.is_trained = True
    
    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of (document, score) tuples
        """
        if self.index.ntotal == 0:
            logger.warning("Vector store is empty")
            return []
        
        # Ensure query is 2D and float32
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = query_embedding.astype('float32')
        
        # Search
        scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        # Retrieve documents
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.documents):
                results.append((self.documents[idx], float(score)))
        
        return results
    
    def save(self, path: str):
        """
        Save index and documents to disk.
        
        Args:
            path: Directory path to save to
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_path = path / "index.faiss"
        faiss.write_index(self.index, str(index_path))
        
        # Save documents
        docs_path = path / "documents.pkl"
        with open(docs_path, 'wb') as f:
            pickle.dump(self.documents, f)
        
        logger.info(f"Saved vector store to {path}")
    
    def load(self, path: str):
        """
        Load index and documents from disk.
        
        Args:
            path: Directory path to load from
        """
        path = Path(path)
        
        # Load FAISS index
        index_path = path / "index.faiss"
        self.index = faiss.read_index(str(index_path))
        
        # Set nprobe if IVF index
        if hasattr(self.index, 'nprobe'):
            self.index.nprobe = self.n_probe
        
        # Load documents
        docs_path = path / "documents.pkl"
        with open(docs_path, 'rb') as f:
            self.documents = pickle.load(f)
        
        logger.info(f"Loaded vector store from {path} ({self.index.ntotal} vectors)")
    
    def clear(self):
        """Clear the vector store."""
        self._initialize_index()
        self.documents = []
        logger.info("Cleared vector store")

