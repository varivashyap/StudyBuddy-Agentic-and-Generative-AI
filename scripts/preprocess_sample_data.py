#!/usr/bin/env python3
"""
Preprocess sample data for offline testing.

Runs OCR on PDF and ASR on audio, saves preprocessed text.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.pdf_ingestion import PDFIngestion
from src.ingestion.audio_ingestion import AudioIngestion

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def preprocess_pdf(pdf_path: Path, output_path: Path):
    """
    Preprocess PDF with OCR.
    
    Args:
        pdf_path: Path to PDF file
        output_path: Path to save preprocessed text
    """
    logger.info(f"Processing PDF: {pdf_path}")
    
    pdf_ingestion = PDFIngestion()
    documents = pdf_ingestion.extract_text(pdf_path)
    
    # Combine all pages
    full_text = "\n\n".join([doc['text'] for doc in documents])
    
    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_text)
    
    logger.info(f"✓ Saved preprocessed PDF text to {output_path}")
    logger.info(f"  Total pages: {len(documents)}")
    logger.info(f"  Total characters: {len(full_text)}")


def preprocess_audio(audio_path: Path, output_path: Path):
    """
    Preprocess audio with ASR.
    
    Args:
        audio_path: Path to audio file
        output_path: Path to save preprocessed text
    """
    logger.info(f"Processing audio: {audio_path}")
    
    audio_ingestion = AudioIngestion()
    segments = audio_ingestion.transcribe(audio_path)
    
    # Combine all segments
    full_text = " ".join([seg['text'] for seg in segments])
    
    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_text)
    
    logger.info(f"✓ Saved preprocessed audio text to {output_path}")
    logger.info(f"  Total segments: {len(segments)}")
    logger.info(f"  Total characters: {len(full_text)}")


def main():
    """Main preprocessing pipeline."""
    logger.info("=" * 70)
    logger.info("Sample Data Preprocessing")
    logger.info("=" * 70)
    
    # Paths
    data_dir = Path("data")
    preprocessed_dir = data_dir / "preprocessed"
    
    pdf_path = data_dir / "sample_lecture.pdf"
    audio_path = data_dir / "sample_lecture.mp3"
    
    pdf_output = preprocessed_dir / "sample_lecture_ocr.txt"
    audio_output = preprocessed_dir / "sample_lecture_asr.txt"
    
    # Process PDF
    if pdf_path.exists():
        try:
            preprocess_pdf(pdf_path, pdf_output)
        except Exception as e:
            logger.error(f"Failed to process PDF: {e}")
    else:
        logger.warning(f"PDF not found: {pdf_path}")
    
    # Process audio
    if audio_path.exists():
        try:
            preprocess_audio(audio_path, audio_output)
        except Exception as e:
            logger.error(f"Failed to process audio: {e}")
    else:
        logger.warning(f"Audio not found: {audio_path}")
    
    logger.info("\n✓ Preprocessing completed!")
    logger.info(f"Preprocessed files saved to: {preprocessed_dir}")


if __name__ == "__main__":
    main()

