"""Main pipeline orchestration for Study Assistant."""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from .config import get_config
from .ingestion import PDFIngestion, AudioIngestion
from .preprocessing import TextCleaner
from .representation import TextChunker, EmbeddingModel, VectorStore
from .retrieval import HybridRetriever, Reranker
from .generation import LLMClient, SummaryGenerator, FlashcardGenerator, QuizGenerator
from .evaluation import ContentValidator, EvaluationMetrics
from .export import AnkiExporter, CSVExporter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StudyAssistantPipeline:
    """Main pipeline for processing study materials and generating content."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the study assistant pipeline.
        
        Args:
            config_path: Path to config file (optional)
        """
        # Load configuration
        if config_path:
            from .config import Config
            self.config = Config(config_path)
        else:
            self.config = get_config()
        
        logger.info("Initializing Study Assistant Pipeline")
        
        # Initialize components
        self.pdf_ingestion = PDFIngestion()
        self.audio_ingestion = AudioIngestion()
        self.text_cleaner = TextCleaner()
        self.chunker = TextChunker()
        self.embedding_model = EmbeddingModel()
        # Pass dimension from embedding model to vector store
        self.vector_store = VectorStore(dimension=self.embedding_model.dimension)
        self.retriever = HybridRetriever(self.vector_store, self.embedding_model)
        self.reranker = Reranker()
        
        self.llm_client = LLMClient()
        self.summary_generator = SummaryGenerator(self.llm_client)
        self.flashcard_generator = FlashcardGenerator(self.llm_client)
        self.quiz_generator = QuizGenerator(self.llm_client)
        
        self.validator = ContentValidator(self.embedding_model)
        self.metrics = EvaluationMetrics()
        
        self.anki_exporter = AnkiExporter()
        self.csv_exporter = CSVExporter()
        
        logger.info("Pipeline initialized successfully")
    
    def ingest_pdf(self, pdf_path: str):
        """
        Ingest and process a PDF file.
        
        Args:
            pdf_path: Path to PDF file
        """
        logger.info(f"Ingesting PDF: {pdf_path}")
        
        # Extract text
        pages = self.pdf_ingestion.extract(pdf_path)
        
        # Clean text
        pages = self.text_cleaner.clean_batch(pages)
        
        # Chunk text
        chunks = self.chunker.chunk(pages)
        
        # Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedding_model.embed(texts)
        
        # Add to vector store
        self.vector_store.add(embeddings, chunks)
        
        # Update retriever index
        self.retriever.update_index()
        
        logger.info(f"Successfully ingested PDF with {len(chunks)} chunks")
    
    def ingest_audio(self, audio_path: str):
        """
        Ingest and process an audio/video file.
        
        Args:
            audio_path: Path to audio/video file
        """
        logger.info(f"Ingesting audio: {audio_path}")
        
        # Transcribe
        segments = self.audio_ingestion.transcribe(audio_path)
        
        # Clean text
        segments = self.text_cleaner.clean_batch(segments)
        
        # Chunk text
        chunks = self.chunker.chunk(segments)
        
        # Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedding_model.embed(texts)
        
        # Add to vector store
        self.vector_store.add(embeddings, chunks)
        
        # Update retriever index
        self.retriever.update_index()
        
        logger.info(f"Successfully ingested audio with {len(chunks)} chunks")
    
    def generate_summaries(
        self,
        query: Optional[str] = None,
        scale: str = "paragraph"
    ) -> str:
        """
        Generate summary from ingested content.
        
        Args:
            query: Optional query to focus summary (uses general summary if None)
            scale: Summary scale ("sentence", "paragraph", "section")
            
        Returns:
            Generated summary
        """
        logger.info(f"Generating {scale} summary")
        
        # Retrieve context
        if query is None:
            query = "Summarize the main concepts and key information"
        
        context = self._retrieve_context(query)
        
        # Generate summary
        summary = self.summary_generator.generate(context, scale)
        
        # Validate
        validation = self.validator.validate_summary(summary, context)
        if not validation['is_valid']:
            logger.warning(f"Summary validation warnings: {validation['warnings']}")
        
        # Record metrics
        self.metrics.record_factuality(validation['source_containment'], 'summary')
        
        return summary
    
    def generate_flashcards(
        self,
        query: Optional[str] = None,
        card_type: str = "definition",
        max_cards: int = 50
    ) -> List[Dict[str, str]]:
        """
        Generate flashcards from ingested content.
        
        Args:
            query: Optional query to focus flashcards
            card_type: Type of flashcard
            max_cards: Maximum number of cards
            
        Returns:
            List of flashcard dicts
        """
        logger.info(f"Generating {card_type} flashcards")
        
        # Retrieve context
        if query is None:
            query = "Extract key concepts, definitions, and facts"
        
        context = self._retrieve_context(query, top_k=30)
        
        # Generate flashcards
        flashcards = self.flashcard_generator.generate(context, card_type, max_cards)
        
        logger.info(f"Generated {len(flashcards)} flashcards")
        return flashcards
    
    def generate_quizzes(
        self,
        query: Optional[str] = None,
        question_type: str = "mcq",
        num_questions: int = 10
    ) -> List[Dict[str, any]]:
        """
        Generate quiz questions from ingested content.
        
        Args:
            query: Optional query to focus questions
            question_type: Type of question
            num_questions: Number of questions
            
        Returns:
            List of question dicts
        """
        logger.info(f"Generating {question_type} questions")
        
        # Retrieve context
        if query is None:
            query = "Generate assessment questions covering key concepts"
        
        context = self._retrieve_context(query, top_k=30)
        
        # Generate questions
        questions = self.quiz_generator.generate(context, question_type, num_questions)
        
        logger.info(f"Generated {len(questions)} questions")
        return questions
    
    def export_anki(self, flashcards: List[Dict[str, str]], output_path: str):
        """Export flashcards to Anki deck."""
        self.anki_exporter.export(flashcards, output_path)
    
    def export_csv_flashcards(self, flashcards: List[Dict[str, str]], output_path: str):
        """Export flashcards to CSV."""
        self.csv_exporter.export_flashcards(flashcards, output_path)
    
    def export_csv_quizzes(self, questions: List[Dict[str, any]], output_path: str):
        """Export quiz questions to CSV."""
        self.csv_exporter.export_quizzes(questions, output_path)
    
    def save_index(self, path: str):
        """Save vector store index to disk."""
        self.vector_store.save(path)
        logger.info(f"Saved index to {path}")
    
    def load_index(self, path: str):
        """Load vector store index from disk."""
        self.vector_store.load(path)
        self.retriever.update_index()
        logger.info(f"Loaded index from {path}")
    
    def _retrieve_context(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Tuple[Dict, float]]:
        """Retrieve and rerank context for a query."""
        # Retrieve
        results = self.retriever.retrieve(query, top_k)
        
        # Rerank
        results = self.reranker.rerank(query, results)
        
        return results
    
    def get_metrics_summary(self) -> Dict:
        """Get evaluation metrics summary."""
        return self.metrics.get_summary()

