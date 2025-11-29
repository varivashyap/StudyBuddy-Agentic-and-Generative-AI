#!/usr/bin/env python3
"""
Test pipeline using preprocessed OCR/ASR text.

Skips ingestion stage, runs generation directly on preprocessed text.
"""

import sys
import json
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing.text_cleaner import TextCleaner
from src.representation.chunker import TextChunker
from src.representation.embeddings import EmbeddingModel
from src.representation.vector_store import VectorStore
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.reranker import Reranker
from src.generation.summary_generator import SummaryGenerator
from src.generation.flashcard_generator import FlashcardGenerator
from src.generation.quiz_generator import QuizGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_preprocessed_text(file_path: Path) -> str:
    """Load preprocessed text from file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Preprocessed file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    logger.info(f"Loaded preprocessed text from {file_path}")
    logger.info(f"  Length: {len(text)} characters")
    
    return text


def process_text(text: str, source_name: str):
    """
    Process text through the pipeline.
    
    Args:
        text: Preprocessed text
        source_name: Name of source (for metadata)
    """
    # Initialize components
    logger.info("Initializing pipeline components...")
    text_cleaner = TextCleaner()
    chunker = TextChunker()
    embedding_model = EmbeddingModel()
    vector_store = VectorStore(dimension=embedding_model.dimension)
    retriever = HybridRetriever(vector_store, embedding_model)
    reranker = Reranker()
    
    # Clean text
    logger.info("Cleaning text...")
    cleaned_text = text_cleaner.clean(text)
    
    # Create document
    document = {
        'text': cleaned_text,
        'metadata': {
            'source': source_name,
            'type': 'preprocessed'
        }
    }
    
    # Chunk
    logger.info("Chunking text...")
    chunks = chunker.chunk([document])
    logger.info(f"Created {len(chunks)} chunks")
    
    # Generate embeddings
    logger.info("Generating embeddings...")
    texts = [chunk['text'] for chunk in chunks]
    embeddings = embedding_model.embed(texts)
    
    # Add to vector store
    logger.info("Adding to vector store...")
    vector_store.add(embeddings, chunks)
    
    # Update retriever
    retriever.update_index()
    
    return retriever, reranker, chunks


def generate_outputs(retriever, reranker, chunks):
    """Generate summaries, flashcards, and quizzes."""
    results_dir = Path("results/testing")
    results_dir.mkdir(parents=True, exist_ok=True)

    # Initialize LLM client
    from src.generation import LLMClient
    llm_client = LLMClient()

    # Initialize generators
    summary_gen = SummaryGenerator(llm_client)
    flashcard_gen = FlashcardGenerator(llm_client)
    quiz_gen = QuizGenerator(llm_client)
    
    # Generate summary
    logger.info("\n=== Generating Summary ===")
    query = "What are the main topics, key concepts, important definitions, and core ideas discussed in this lecture? Provide a comprehensive overview covering all major themes and learning objectives."
    context_chunks = retriever.retrieve(query, top_k=10)
    context_chunks = reranker.rerank(query, context_chunks, top_m=8)

    # Pass context_chunks directly (already in correct format)
    summary = summary_gen.generate(context_chunks, scale="section")

    summary_file = results_dir / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump({'summary': summary, 'query': query}, f, indent=2)
    logger.info(f"✓ Summary saved to {summary_file}")

    # Generate flashcards
    logger.info("\n=== Generating Flashcards ===")
    flashcards = flashcard_gen.generate(context_chunks, max_cards=20)

    flashcards_file = results_dir / "flashcards.json"
    with open(flashcards_file, 'w') as f:
        json.dump({'flashcards': flashcards}, f, indent=2)
    logger.info(f"✓ Flashcards saved to {flashcards_file}")
    logger.info(f"  Generated {len(flashcards)} flashcards")

    # Generate quiz
    logger.info("\n=== Generating Quiz ===")
    questions = quiz_gen.generate(context_chunks, num_questions=10)

    quiz_file = results_dir / "questions.json"
    with open(quiz_file, 'w') as f:
        json.dump({'questions': questions}, f, indent=2)
    logger.info(f"✓ Quiz saved to {quiz_file}")
    logger.info(f"  Generated {len(questions)} questions")


def main():
    """Main testing pipeline."""
    logger.info("=" * 70)
    logger.info("Testing from Preprocessed Data")
    logger.info("=" * 70)
    
    preprocessed_dir = Path("data/preprocessed")
    
    # Load preprocessed texts
    ocr_file = preprocessed_dir / "sample_lecture_ocr.txt"
    asr_file = preprocessed_dir / "sample_lecture_asr.txt"
    
    # Combine OCR and ASR if both exist
    combined_text = ""
    
    if ocr_file.exists():
        ocr_text = load_preprocessed_text(ocr_file)
        combined_text += ocr_text + "\n\n"
    
    if asr_file.exists():
        asr_text = load_preprocessed_text(asr_file)
        combined_text += asr_text
    
    if not combined_text:
        logger.error("No preprocessed files found!")
        logger.error("Run scripts/preprocess_sample_data.py first")
        return
    
    # Process text
    logger.info("\n=== Processing Text ===")
    retriever, reranker, chunks = process_text(combined_text, "sample_lecture")
    
    # Generate outputs
    generate_outputs(retriever, reranker, chunks)
    
    logger.info("\n✓ Testing completed successfully!")
    logger.info("Results saved to: results/testing/")


if __name__ == "__main__":
    main()

