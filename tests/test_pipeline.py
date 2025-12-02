"""Tests for main pipeline."""

import pytest
from unittest.mock import Mock, patch
from src.pipeline import StudyAssistantPipeline


class TestStudyAssistantPipeline:
    """Test cases for StudyAssistantPipeline."""
    
    @patch('src.pipeline.PDFIngestion')
    @patch('src.pipeline.AudioIngestion')
    @patch('src.pipeline.EmbeddingModel')
    @patch('src.pipeline.LLMClient')
    def setup_method(self, mock_llm, mock_embed, mock_audio, mock_pdf):
        """Set up test fixtures with mocks."""
        self.pipeline = StudyAssistantPipeline()
    
    def test_pipeline_initialization(self):
        """Test that pipeline initializes all components."""
        assert self.pipeline.pdf_ingestion is not None
        assert self.pipeline.audio_ingestion is not None
        assert self.pipeline.chunker is not None
        assert self.pipeline.embedding_model is not None
        assert self.pipeline.vector_store is not None
        assert self.pipeline.retriever is not None
        assert self.pipeline.llm_client is not None
    
    def test_retrieve_context(self):
        """Test context retrieval."""
        # Add some mock data to vector store
        import numpy as np
        
        embeddings = np.random.rand(5, self.pipeline.vector_store.dimension).astype('float32')
        documents = [
            {'text': f'Document {i}', 'metadata': {}}
            for i in range(5)
        ]
        
        self.pipeline.vector_store.add(embeddings, documents)
        self.pipeline.retriever.update_index()
        
        # Retrieve
        context = self.pipeline._retrieve_context("test query", top_k=3)
        
        assert len(context) <= 3
        assert all(isinstance(item, tuple) for item in context)

