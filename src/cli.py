"""Command-line interface for Study Assistant."""

import argparse
import logging
from pathlib import Path

from .pipeline import StudyAssistantPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Study Assistant - AI-powered learning content generator"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest PDF or audio files')
    ingest_parser.add_argument('files', nargs='+', help='Files to ingest')
    ingest_parser.add_argument('--index', default='data/cache/vector_index', help='Index path')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate content')
    gen_parser.add_argument('--index', default='data/cache/vector_index', help='Index path')
    gen_parser.add_argument('--type', choices=['summary', 'flashcards', 'quiz'], required=True)
    gen_parser.add_argument('--output', required=True, help='Output file path')
    gen_parser.add_argument('--query', help='Optional query to focus generation')
    gen_parser.add_argument('--num', type=int, default=10, help='Number of items to generate')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export to different formats')
    export_parser.add_argument('input', help='Input file (JSON)')
    export_parser.add_argument('--format', choices=['anki', 'csv'], required=True)
    export_parser.add_argument('--output', required=True, help='Output file path')
    
    args = parser.parse_args()
    
    if args.command == 'ingest':
        ingest_files(args)
    elif args.command == 'generate':
        generate_content(args)
    elif args.command == 'export':
        export_content(args)
    else:
        parser.print_help()


def ingest_files(args):
    """Ingest files into the pipeline."""
    logger.info("Initializing pipeline...")
    pipeline = StudyAssistantPipeline()
    
    # Load existing index if available
    index_path = Path(args.index)
    if index_path.exists():
        logger.info(f"Loading existing index from {index_path}")
        pipeline.load_index(str(index_path))
    
    # Ingest files
    for file_path in args.files:
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            continue
        
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            logger.info(f"Ingesting PDF: {file_path}")
            pipeline.ingest_pdf(str(file_path))
        elif suffix in ['.mp3', '.wav', '.m4a', '.mp4']:
            logger.info(f"Ingesting audio: {file_path}")
            pipeline.ingest_audio(str(file_path))
        else:
            logger.warning(f"Unsupported file type: {suffix}")
    
    # Save index
    logger.info(f"Saving index to {index_path}")
    pipeline.save_index(str(index_path))
    
    logger.info("✓ Ingestion complete")


def generate_content(args):
    """Generate content from ingested materials."""
    logger.info("Initializing pipeline...")
    pipeline = StudyAssistantPipeline()
    
    # Load index
    index_path = Path(args.index)
    if not index_path.exists():
        logger.error(f"Index not found: {index_path}")
        logger.error("Please run 'ingest' command first")
        return
    
    pipeline.load_index(str(index_path))
    
    # Generate content
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if args.type == 'summary':
        logger.info("Generating summary...")
        summary = pipeline.generate_summaries(query=args.query, scale='paragraph')
        
        with open(output_path, 'w') as f:
            f.write(summary)
        
        logger.info(f"✓ Summary saved to {output_path}")
    
    elif args.type == 'flashcards':
        logger.info("Generating flashcards...")
        flashcards = pipeline.generate_flashcards(
            query=args.query,
            max_cards=args.num
        )
        
        # Export based on output format
        if output_path.suffix == '.apkg':
            pipeline.export_anki(flashcards, str(output_path))
        else:
            pipeline.export_csv_flashcards(flashcards, str(output_path))
        
        logger.info(f"✓ {len(flashcards)} flashcards saved to {output_path}")
    
    elif args.type == 'quiz':
        logger.info("Generating quiz...")
        questions = pipeline.generate_quizzes(
            query=args.query,
            num_questions=args.num
        )
        
        pipeline.export_csv_quizzes(questions, str(output_path))
        logger.info(f"✓ {len(questions)} questions saved to {output_path}")


def export_content(args):
    """Export content to different formats."""
    import json
    
    logger.info("Initializing pipeline...")
    pipeline = StudyAssistantPipeline()
    
    # Load input
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Export
    if args.format == 'anki':
        pipeline.export_anki(data, str(output_path))
    elif args.format == 'csv':
        if isinstance(data, list) and data and 'question' in data[0]:
            pipeline.export_csv_quizzes(data, str(output_path))
        else:
            pipeline.export_csv_flashcards(data, str(output_path))
    
    logger.info(f"✓ Exported to {output_path}")


if __name__ == '__main__':
    main()

