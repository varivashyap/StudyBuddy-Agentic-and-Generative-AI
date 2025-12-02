# Data Directory

This directory contains input files, outputs, and cached data for the Study Assistant.

## Structure

```
data/
├── uploads/        # Place your PDF and audio files here
├── outputs/        # Generated flashcards, quizzes, summaries
├── cache/          # Vector indices and embeddings cache
└── feedback.jsonl  # User feedback data
```

## Usage

### Input Files

Place your study materials in the `uploads/` directory:

```
data/uploads/
├── lecture_1.pdf
├── lecture_2.pdf
├── recording_1.mp3
└── textbook_chapter.pdf
```

### Outputs

Generated content will be saved to `outputs/`:

```
data/outputs/
├── flashcards.apkg      # Anki deck
├── flashcards.csv       # CSV format
├── quiz.csv             # Quiz questions
└── summaries.txt        # Generated summaries
```

### Cache

Vector indices are cached to avoid re-processing:

```
data/cache/
├── vector_index/
│   ├── index.faiss
│   └── documents.pkl
└── embeddings/
```

## Sample Files

To test the system, you can use:

1. **Sample PDF**: Any lecture slides or textbook chapter
2. **Sample Audio**: Lecture recording in MP3/WAV format

## Notes

- The `.gitignore` excludes actual data files from version control
- Cache files can be safely deleted to force re-processing
- Feedback data is stored in JSONL format for easy analysis

