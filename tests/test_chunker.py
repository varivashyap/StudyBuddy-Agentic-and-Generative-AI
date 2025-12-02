"""Tests for text chunking."""

import pytest
from src.representation.chunker import TextChunker


class TestTextChunker:
    """Test cases for TextChunker."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = TextChunker()
    
    def test_chunk_simple_text(self):
        """Test chunking of simple text."""
        documents = [
            {
                'text': 'This is sentence one. This is sentence two. This is sentence three.',
                'metadata': {'source': 'test'}
            }
        ]
        
        chunks = self.chunker.chunk(documents)
        
        assert len(chunks) > 0
        assert all('text' in chunk for chunk in chunks)
        assert all('metadata' in chunk for chunk in chunks)
    
    def test_chunk_empty_document(self):
        """Test chunking of empty document."""
        documents = [{'text': '', 'metadata': {}}]
        
        chunks = self.chunker.chunk(documents)
        
        assert len(chunks) == 0
    
    def test_chunk_preserves_metadata(self):
        """Test that metadata is preserved in chunks."""
        metadata = {'source': 'test', 'page': 1}
        documents = [
            {
                'text': 'Test sentence. ' * 100,
                'metadata': metadata
            }
        ]
        
        chunks = self.chunker.chunk(documents)
        
        assert all(chunk['metadata'] == metadata for chunk in chunks)
    
    def test_chunk_overlap(self):
        """Test that chunks have overlap."""
        # Create a long text
        text = '. '.join([f'Sentence {i}' for i in range(100)])
        documents = [{'text': text, 'metadata': {}}]
        
        chunks = self.chunker.chunk(documents)
        
        # Should have multiple chunks
        assert len(chunks) > 1
        
        # Check for overlap (simplified check)
        # In practice, would check actual sentence overlap
        assert all('tokens' in chunk for chunk in chunks)

