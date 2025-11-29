"""Text chunking with semantic continuity."""

import logging
from typing import List, Dict
import re

from ..config import get_config

logger = logging.getLogger(__name__)


class TextChunker:
    """Chunk text using sentence-based sliding window."""
    
    def __init__(self):
        """Initialize text chunker."""
        self.config = get_config()
        self.chunk_size = self.config.chunking.chunk_size_tokens
        self.overlap = self.config.chunking.overlap_tokens
        self.min_size = self.config.chunking.min_chunk_size
        self.max_size = self.config.chunking.max_chunk_size
    
    def chunk(self, documents: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Chunk documents into smaller pieces.

        Args:
            documents: List of document dicts with 'text' field

        Returns:
            List of chunk dicts with text and metadata
        """
        chunks = []

        # Check if we have many small documents (e.g., audio segments)
        # If so, combine them first before chunking
        if len(documents) > 50:
            avg_length = sum(len(doc.get('text', '')) for doc in documents) / len(documents)
            if avg_length < 200:  # Average segment is short (likely audio)
                logger.info(f"Detected {len(documents)} short segments (avg {avg_length:.0f} chars), combining before chunking")
                combined_text = ' '.join(doc.get('text', '') for doc in documents if doc.get('text'))
                # Use metadata from first document
                metadata = documents[0].get('metadata', {}) if documents else {}
                doc_chunks = self._chunk_text(combined_text, metadata)
                chunks.extend(doc_chunks)
                logger.info(f"Created {len(chunks)} chunks from combined text")
                return chunks

        # Normal processing: chunk each document separately
        for doc in documents:
            text = doc.get('text', '')
            if not text:
                continue

            doc_chunks = self._chunk_text(text, doc.get('metadata', {}))
            chunks.extend(doc_chunks)

        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks
    
    def _chunk_text(self, text: str, metadata: Dict) -> List[Dict[str, any]]:
        """Chunk a single text document."""
        # Split into sentences
        sentences = self._split_sentences(text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self._estimate_tokens(sentence)
            
            # Check if adding this sentence exceeds max size
            if current_tokens + sentence_tokens > self.max_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                if current_tokens >= self.min_size:
                    chunks.append({
                        'text': chunk_text,
                        'metadata': metadata.copy(),
                        'tokens': current_tokens
                    })
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk,
                    self.overlap
                )
                current_chunk = overlap_sentences
                current_tokens = sum(self._estimate_tokens(s) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
            
            # Check if we've reached target chunk size
            if current_tokens >= self.chunk_size:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'metadata': metadata.copy(),
                    'tokens': current_tokens
                })
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk,
                    self.overlap
                )
                current_chunk = overlap_sentences
                current_tokens = sum(self._estimate_tokens(s) for s in current_chunk)
        
        # Add remaining chunk
        if current_chunk and current_tokens >= self.min_size:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'metadata': metadata.copy(),
                'tokens': current_tokens
            })
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - could be enhanced with spaCy or NLTK
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
    
    def _get_overlap_sentences(self, sentences: List[str], overlap_tokens: int) -> List[str]:
        """Get sentences for overlap based on token count."""
        overlap_sentences = []
        token_count = 0
        
        # Take sentences from the end
        for sentence in reversed(sentences):
            sentence_tokens = self._estimate_tokens(sentence)
            if token_count + sentence_tokens > overlap_tokens:
                break
            overlap_sentences.insert(0, sentence)
            token_count += sentence_tokens
        
        return overlap_sentences

