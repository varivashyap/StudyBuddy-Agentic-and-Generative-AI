"""Basic usage example for Study Assistant.

100% OPEN-SOURCE - NO API KEYS REQUIRED!

This example demonstrates the complete pipeline using only local, open-source models:
- LLM: llama-cpp-python with GGUF models
- Embeddings: sentence-transformers
- OCR: PaddleOCR + Tesseract
- ASR: Whisper (open-source)

Before running:
1. Download a GGUF model (see MODELS_GUIDE.md)
2. Place it in models/ directory
3. Update config.yaml with the model name
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import StudyAssistantPipeline


def main():
    """Demonstrate basic usage of the Study Assistant pipeline."""

    print("=" * 70)
    print("Study Assistant - 100% Open-Source")
    print("NO API KEYS • NO COSTS • RUNS LOCALLY")
    print("=" * 70)

    # Check for model
    models_dir = Path("models")
    if not models_dir.exists() or not list(models_dir.glob("*.gguf")):
        print("\n⚠️  WARNING: No GGUF model found in models/ directory!")
        print("   Please download a model first. See MODELS_GUIDE.md for instructions.")
        print("\n   Quick download:")
        print("   pip install huggingface-hub")
        print("   huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF \\")
        print("     mistral-7b-instruct-v0.2.Q4_K_M.gguf \\")
        print("     --local-dir models/ --local-dir-use-symlinks False")
        print("\n   Then update config.yaml with the model name.\n")
        return

    # Initialize pipeline
    print("\nInitializing Study Assistant...")
    print("Loading local models (this may take a moment on first run)...")
    try:
        pipeline = StudyAssistantPipeline()
        print("✓ Pipeline initialized successfully!")
    except Exception as e:
        print(f"\n❌ Error initializing pipeline: {e}")
        print("\nTroubleshooting:")
        print("1. Check that your GGUF model is in models/ directory")
        print("2. Verify config.yaml has the correct model name")
        print("3. See MODELS_GUIDE.md for detailed setup instructions")
        return
    
    # Example 1: Process a PDF
    print("\n=== Example 1: Processing PDF ===")
    pdf_path = "data/sample_lecture.pdf"
    
    if Path(pdf_path).exists():
        pipeline.ingest_pdf(pdf_path)
        print(f"✓ Ingested PDF: {pdf_path}")
    else:
        print(f"⚠ PDF not found: {pdf_path}")
        print("  Place your PDF in data/sample_lecture.pdf to try this example")
    
    # Example 2: Process audio
    print("\n=== Example 2: Processing Audio ===")
    audio_path = "data/sample_lecture.mp3"
    
    if Path(audio_path).exists():
        pipeline.ingest_audio(audio_path)
        print(f"✓ Ingested audio: {audio_path}")
    else:
        print(f"⚠ Audio not found: {audio_path}")
        print("  Place your audio in data/sample_lecture.mp3 to try this example")
    
    # Check if we have any content
    if pipeline.vector_store.index.ntotal == 0:
        print("\n⚠ No content ingested. Please add PDF or audio files.")
        return
    
    # Example 3: Generate summaries
    print("\n=== Example 3: Generating Summaries ===")
    
    # Sentence summary
    summary = pipeline.generate_summaries(scale="sentence")
    print(f"\nSentence summary:\n{summary}")
    
    # Paragraph summary
    summary = pipeline.generate_summaries(scale="paragraph")
    print(f"\nParagraph summary:\n{summary}")
    
    # Example 4: Generate flashcards
    print("\n=== Example 4: Generating Flashcards ===")
    
    flashcards = pipeline.generate_flashcards(card_type="definition", max_cards=5)
    print(f"\nGenerated {len(flashcards)} flashcards:")
    for i, card in enumerate(flashcards[:3], 1):
        print(f"\n{i}. Front: {card['front']}")
        print(f"   Back: {card['back']}")
    
    # Example 5: Generate quiz questions
    print("\n=== Example 5: Generating Quiz Questions ===")
    
    questions = pipeline.generate_quizzes(question_type="mcq", num_questions=3)
    print(f"\nGenerated {len(questions)} questions:")
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. {q['question']}")
        if 'options' in q:
            for j, opt in enumerate(q['options'], 1):
                print(f"   {chr(64+j)}. {opt}")
        print(f"   Answer: {q.get('correct_answer', q.get('answer', 'N/A'))}")
    
    # Example 6: Export to Anki
    print("\n=== Example 6: Exporting to Anki ===")
    
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    anki_path = output_dir / "flashcards.apkg"
    pipeline.export_anki(flashcards, str(anki_path))
    print(f"✓ Exported to Anki: {anki_path}")
    
    # Example 7: Export to CSV
    print("\n=== Example 7: Exporting to CSV ===")
    
    csv_path = output_dir / "flashcards.csv"
    pipeline.export_csv_flashcards(flashcards, str(csv_path))
    print(f"✓ Exported flashcards to CSV: {csv_path}")
    
    quiz_csv_path = output_dir / "quiz.csv"
    pipeline.export_csv_quizzes(questions, str(quiz_csv_path))
    print(f"✓ Exported quiz to CSV: {quiz_csv_path}")
    
    # Example 8: Save index for later use
    print("\n=== Example 8: Saving Index ===")
    
    index_path = "data/cache/vector_index"
    pipeline.save_index(index_path)
    print(f"✓ Saved vector index to: {index_path}")
    
    # Show metrics
    print("\n=== Metrics Summary ===")
    metrics = pipeline.get_metrics_summary()
    print(metrics)

    print("\n" + "=" * 70)
    print("✓ All examples completed successfully!")
    print("=" * 70)
    print("\n💡 Tips:")
    print("   - All processing happened locally on your machine")
    print("   - No data was sent to external servers")
    print("   - No API costs incurred")
    print("   - You can use this offline (after models are downloaded)")
    print("\n📚 Next steps:")
    print("   - Try with your own PDFs and audio files")
    print("   - Adjust config.yaml for different models or settings")
    print("   - See MODELS_GUIDE.md for other model options")
    print("   - Import flashcards.apkg into Anki desktop app")


if __name__ == "__main__":
    main()

