# Study Assistant - 100% Open-Source AI Learning Tool

**🎉 NO API KEYS • NO COSTS • 100% PRIVACY • RUNS LOCALLY**

A high-performance RAG-based study assistant that runs entirely on your machine using open-source models. Ingests lecture PDFs and audio/video content to generate summaries, flashcards, and quizzes.

## ✨ Key Features

### 🔒 Privacy-First
- **100% Local**: All processing happens on your machine
- **No API Calls**: Zero data sent to external servers
- **Offline Capable**: Works without internet (after model download)
- **No Subscriptions**: Completely free to use

### 📚 Content Processing
- **Multi-format Input**: PDF documents and audio/video files
- **Intelligent Processing**: PaddleOCR, Whisper ASR, semantic chunking
- **RAG Pipeline**: Hybrid retrieval (vector + BM25) with reranking
- **Smart Caching**: Process documents once, reuse embeddings (58% faster)

### 🎓 Content Generation
- **Multi-scale summaries** (sentence, paragraph, section)
- **Flashcards** (definition, concept, cloze)
- **Quiz questions** (MCQ, short-answer, numerical)
- **Export Formats**: Anki (.apkg), CSV

### 🌐 MCP Server (Production-Ready)
- **RESTful API**: Upload documents, generate study materials
- **Web Frontend**: Simple drag-and-drop interface
- **Batch Processing**: Generate all 3 types in one request
- **Session Management**: Automatic caching and deduplication
- **Modular Design**: Easy to extend with new models and request types

### 🧠 Advanced Features
- **Model Finetuning**: LoRA/QLoRA finetuning optimized for 4GB GPU
- **Hyperparameter Tuning**: Grid search and Bayesian optimization (Optuna)
- **Prompting Strategies**: Base, system, one-shot, and few-shot prompting
- **Quantitative Evaluation**: ROUGE, BERTScore, coverage, factuality metrics
- **Web Search Integration**: DuckDuckGo search for question enrichment (optional)

### 🚀 Technology Stack (All Open-Source)
- **LLM**: llama-cpp-python (Mistral, Llama, Phi-3, Gemma)
- **Embeddings**: sentence-transformers (all-MiniLM, all-mpnet)
- **OCR**: PaddleOCR + Tesseract
- **ASR**: OpenAI Whisper (open-source)
- **Vector DB**: FAISS
- **Training**: PEFT (LoRA), BitsAndBytes (4-bit quantization)
- **Optimization**: Optuna (Bayesian hyperparameter search)
- **Evaluation**: ROUGE, BERTScore, NLI (DeBERTa)

## Architecture

```
Input → Preprocessing → Chunking → Embeddings → Vector Store
                                                      ↓
                                                  Retrieval (Hybrid: Vector + BM25)
                                                      ↓
                                              Reranking (Cross-Encoder)
                                                      ↓
                                    Prompting Strategy (Base/System/One-Shot/Few-Shot)
                                                      ↓
                                                  LLM Generation
                                                      ↓
                                    Optional: Web Search Enrichment
                                                      ↓
                                                    Output
```

### Training & Evaluation Pipeline

```
Training Data → Finetuning (LoRA/QLoRA) → Improved Model
                     ↓
          Hyperparameter Search (Optuna)
                     ↓
              Best Configuration
                     ↓
         Evaluation (ROUGE, BERTScore, etc.)
                     ↓
          Improvement Report (JSON)
```

## 🚀 Quick Start

### Option 1: MCP Server (Recommended - Web Interface)

```bash
# 1. Setup (one-time)
./setup_mcp_server.sh

# 2. Start the MCP server
./start_mcp_server.sh

# 3. Start the frontend (in new terminal)
./start_frontend.sh

# 4. Open browser to http://localhost:8080
# Upload documents, generate study materials!
```

### Option 2: Python API (For Developers)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download model (Mistral-7B)
mkdir -p models
pip install huggingface-hub
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF \
  mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  --local-dir models/ --local-dir-use-symlinks False

# 3. Use the Python API (see below)
```

**See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed installation instructions.**

## 📖 Usage

### Web Interface (Easiest)

1. Start the server: `./start_mcp_server.sh`
2. Start the frontend: `./start_frontend.sh`
3. Open http://localhost:8080
4. Upload PDF or audio file
5. Select mode (Summary, Flashcards, Quiz)
6. Click "Generate" and wait for results

### Python API

```python
from src.pipeline import StudyAssistantPipeline

# Initialize pipeline
pipeline = StudyAssistantPipeline()

# Process documents
pipeline.ingest_pdf("lecture.pdf")
pipeline.ingest_audio("lecture.mp3")

# Generate study materials
summaries = pipeline.generate_summaries()
flashcards = pipeline.generate_flashcards()
quizzes = pipeline.generate_quizzes()

# Export to Anki
pipeline.export_anki("output.apkg")
```

### REST API

```bash
# Upload file
curl -X POST http://localhost:5000/upload -F "file=@lecture.pdf"

# Generate summary
curl -X POST http://localhost:5000/process \
  -H "Content-Type: application/json" \
  -d '{"file_id": "...", "request_type": "summary", "model": "default"}'

# Batch process (all 3 types)
curl -X POST http://localhost:5000/batch-process \
  -H "Content-Type: application/json" \
  -d '{"file_id": "...", "requests": [...]}'
```

**See [MCP_SERVER.md](MCP_SERVER.md) for complete API documentation.**

### Advanced: Model Finetuning

```bash
# Finetune for better quality (uses 4GB GPU with QLoRA)
make train-summary
make train-flashcard
make train-quiz

# Hyperparameter tuning
make tune-bayesian

# Evaluate improvements
make evaluate-improvement
```

## Project Structure

```
study-assistant/
├── config/              # Configuration files
│   ├── config.yaml     # Main configuration
│   └── prompts/        # Custom prompt templates
├── src/
│   ├── ingestion/      # PDF & audio input processing
│   ├── preprocessing/  # OCR, ASR, cleaning
│   ├── representation/ # Chunking, embeddings, vector store
│   ├── retrieval/      # Hybrid retrieval & reranking
│   │   └── websearch/  # Web search integration (NEW)
│   ├── generation/     # Summary, flashcard, quiz generation
│   │   └── prompting/  # Prompting strategies (NEW)
│   ├── training/       # Finetuning & hyperparameter tuning (NEW)
│   ├── evaluation/     # Metrics & validation (ENHANCED)
│   ├── export/         # Anki, CSV exporters
│   └── pipeline.py     # Main orchestration
├── scripts/            # Utility scripts (NEW)
│   ├── preprocess_sample_data.py
│   └── test_from_preprocessed.py
├── tests/              # Unit and integration tests
├── data/               # Sample data and outputs
│   ├── training/       # Training data for finetuning
│   └── preprocessed/   # Cached OCR/ASR results
└── results/            # Training and evaluation results
    ├── models/         # Finetuned models
    ├── metrics/        # Evaluation metrics
    └── hparams/        # Hyperparameter search results
```

## 📖 Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete setup from scratch to running
- **[MCP_SERVER.md](MCP_SERVER.md)** - MCP server API and web interface
- **[PROJECT_SPECIFICATION.md](PROJECT_SPECIFICATION.md)** - Pipeline architecture and technical details
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Implementation status and recent fixes

## 💾 System Requirements

**Minimum** (fast, lower quality):
- RAM: 4GB
- Storage: ~3GB
- CPU: Any modern processor

**Recommended** (balanced):
- RAM: 8GB
- Storage: ~6GB
- CPU: 4+ cores
- GPU: Optional (CUDA for faster inference)

**High Quality**:
- RAM: 16GB
- Storage: ~10GB
- GPU: NVIDIA GPU with 8GB+ VRAM

## 🎯 Development Status

✅ **Phase 1 Complete**: Core RAG Pipeline
- PDF/Audio ingestion with OCR and ASR
- Hybrid retrieval (vector + BM25) with reranking
- Content generation (summaries, flashcards, quizzes)
- Export to Anki and CSV
- **100% open-source (no API keys required)**

✅ **Phase 2 Complete**: Advanced Features
- Model finetuning with LoRA/QLoRA (4GB GPU optimized)
- Hyperparameter tuning (grid search + Bayesian optimization)
- Prompting strategies (base, system, one-shot, few-shot)
- Quantitative evaluation metrics (ROUGE, BERTScore, factuality)
- Web search integration for question enrichment

✅ **Phase 3 Complete**: Production MCP Server (Nov 2025)
- RESTful API with 6 endpoints
- Web frontend with drag-and-drop upload
- Session management and caching (58% faster)
- Batch processing support
- Fixed hallucinations (content now based on actual documents)
- Fixed redundant ASR/OCR processing
- Smart chunking for audio transcripts

**See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed status and recent fixes.**

## 🤝 Contributing

Contributions welcome! This project is 100% open-source and community-driven.

## 📄 License

MIT

---

**Made with ❤️ using only open-source tools. No API keys, no costs, no compromises.**

