# Project Specification - Study Assistant

Technical architecture and pipeline specification for the Study Assistant project.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Server (Flask)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Upload     │  │   Process    │  │    Batch     │      │
│  │   Endpoint   │  │   Endpoint   │  │   Endpoint   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │ Session Manager │                        │
│                   │  (Caching)      │                        │
│                   └────────┬────────┘                        │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │ Request Handler │                        │
│                   └────────┬────────┘                        │
└────────────────────────────┼──────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  RAG Pipeline   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐        ┌──────▼──────┐      ┌─────▼─────┐
   │ Ingest  │        │  Retrieval  │      │Generation │
   └────┬────┘        └──────┬──────┘      └─────┬─────┘
        │                    │                    │
   ┌────▼────┐        ┌──────▼──────┐      ┌─────▼─────┐
   │ OCR/ASR │        │ Vector DB   │      │    LLM    │
   │ Chunking│        │ BM25 + FAISS│      │  Mistral  │
   └─────────┘        └─────────────┘      └───────────┘
```

---

## 📦 Core Components

### 1. Ingestion Layer

**Purpose**: Extract and preprocess content from documents

**Components**:
- **PDF Extraction**: PyMuPDF (fitz) for text extraction
- **OCR**: PaddleOCR + Tesseract for scanned documents
- **ASR**: OpenAI Whisper for audio/video transcription
- **Text Cleaning**: Remove noise, normalize whitespace
- **Chunking**: Semantic chunking with overlap

**Key Files**:
- `src/ingestion/pdf_processor.py` - PDF extraction
- `src/ingestion/audio_processor.py` - Audio transcription
- `src/representation/chunker.py` - Text chunking

**Chunking Strategy**:
```python
# Adaptive chunking
if many_short_segments (>50 segments, avg <200 chars):
    # Audio transcripts: combine before chunking
    combined_text = join_all_segments()
    chunks = chunk_text(combined_text, chunk_size=512)
else:
    # Normal documents: chunk individually
    chunks = [chunk_text(doc, chunk_size=512) for doc in documents]
```

### 2. Representation Layer

**Purpose**: Convert text chunks into vector embeddings

**Components**:
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
- **Vector Store**: FAISS (Facebook AI Similarity Search)
- **Metadata**: Track source, page numbers, timestamps

**Key Files**:
- `src/representation/embedder.py` - Generate embeddings
- `src/representation/vector_store.py` - FAISS index management

**Embedding Process**:
```python
# 1. Load model (384-dimensional embeddings)
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Batch encode chunks
embeddings = model.encode(chunks, batch_size=32)

# 3. Build FAISS index
index = faiss.IndexFlatL2(384)
index.add(embeddings)

# 4. Save for caching
faiss.write_index(index, 'index.faiss')
```

### 3. Retrieval Layer

**Purpose**: Find relevant chunks for a given query

**Components**:
- **Vector Retrieval**: FAISS similarity search
- **Keyword Retrieval**: BM25 (Best Matching 25)
- **Hybrid Fusion**: Combine vector + keyword results
- **Reranking**: Cross-encoder for final ranking

**Key Files**:
- `src/retrieval/retriever.py` - Hybrid retrieval
- `src/retrieval/reranker.py` - Cross-encoder reranking

**Retrieval Process**:
```python
# 1. Vector search (top 20)
query_embedding = model.encode(query)
vector_results = faiss_index.search(query_embedding, k=20)

# 2. BM25 search (top 20)
bm25_results = bm25.get_top_n(query, corpus, n=20)

# 3. Hybrid fusion (RRF - Reciprocal Rank Fusion)
combined = reciprocal_rank_fusion(vector_results, bm25_results)

# 4. Rerank with cross-encoder (top 5)
reranked = cross_encoder.rank(query, combined, top_k=5)
```

### 4. Generation Layer

**Purpose**: Generate study materials using LLM

**Components**:
- **LLM**: Mistral-7B-Instruct-v0.2 (GGUF, 4-bit quantized)
- **Prompt Templates**: Task-specific prompts
- **JSON Parsing**: Extract structured output
- **Validation**: Ensure quality and format

**Key Files**:
- `src/generation/llm.py` - LLM interface
- `src/generation/prompts.py` - Prompt templates
- `src/generation/summary_generator.py` - Summary generation
- `src/generation/flashcard_generator.py` - Flashcard generation
- `src/generation/quiz_generator.py` - Quiz generation

**Generation Process**:
```python
# 1. Retrieve relevant context
context = retriever.retrieve(query, top_k=5)

# 2. Build prompt
prompt = f"""
Context: {context}

Task: Generate flashcards based on the context above.

Output format: JSON array of flashcards
[{{"front": "...", "back": "..."}}]
"""

# 3. Generate with LLM
response = llm.generate(prompt, max_tokens=1500)

# 4. Parse JSON (with repair if needed)
flashcards = json_repair.loads(response)
```

---

## 🔄 Pipeline Flow

### Summary Generation

```
1. User uploads document
2. Session manager checks cache
3. If not cached:
   a. Extract text (PDF) or transcribe (audio)
   b. Clean and chunk text
   c. Generate embeddings
   d. Build FAISS index
   e. Save to cache
4. Retrieve relevant chunks for summary
5. Generate summary with LLM
6. Return result
```

### Flashcard Generation

```
1. Load cached pipeline (from summary step)
2. Retrieve chunks covering key concepts
3. Generate flashcards with LLM
4. Parse JSON output
5. Validate and filter
6. Return flashcards
```

### Quiz Generation

```
1. Load cached pipeline (from summary step)
2. Retrieve chunks with factual information
3. Generate quiz questions with LLM
4. Parse JSON output
5. Validate format and difficulty
6. Return quiz
```

---

## 💾 Data Flow & Caching

### Session Management

**Cache Structure**:
```
data/cache/sessions/
└── <file_hash>/
    ├── index.faiss          # Vector embeddings
    ├── documents.pkl        # Chunk metadata
    └── metadata.json        # Session info
```

**Cache Lifecycle**:
```python
# 1. Upload file
file_hash = sha256(file_content)

# 2. Check cache
if cache_exists(file_hash):
    session = load_from_cache(file_hash)
else:
    session = create_new_session(file_hash)
    process_document(session)  # ASR/OCR + embeddings
    save_to_cache(session)

# 3. Reuse for all requests
pipeline = session.get_pipeline()
result = pipeline.generate_summary()
```

**Benefits**:
- ✅ No redundant ASR/OCR processing
- ✅ Instant loading for cached files
- ✅ Persistent across server restarts
- ✅ Automatic deduplication

---

## 🧠 Model Details

### LLM (Mistral-7B-Instruct-v0.2)

- **Size**: ~4GB (Q4_K_M quantization)
- **Context**: 4096 tokens
- **Format**: GGUF (llama.cpp)
- **Inference**: CPU or GPU (CUDA)
- **Speed**: ~10-20 tokens/sec (CPU), ~50-100 tokens/sec (GPU)

**Configuration**:
```yaml
llm:
  provider: "local"
  local:
    model: "mistral-7b-instruct-v0.2.Q4_K_M"
    n_ctx: 4096
    n_gpu_layers: 0  # 35 for GPU
    temperature: 0.7
    top_p: 0.9
    max_tokens: 1500
```

### Embeddings (all-MiniLM-L6-v2)

- **Size**: ~80MB
- **Dimensions**: 384
- **Max sequence**: 256 tokens
- **Speed**: ~1000 sentences/sec (CPU)

### Whisper (Large-v2)

- **Size**: ~3GB
- **Languages**: 99 languages
- **Accuracy**: WER ~3-5% (English)
- **Speed**: ~1x realtime (CPU), ~10x realtime (GPU)

---

## 🔧 Configuration

### Main Config (`config/config.yaml`)

```yaml
system:
  device: "cuda"  # or "cpu"
  log_level: "INFO"

llm:
  provider: "local"
  local:
    model: "mistral-7b-instruct-v0.2.Q4_K_M"
    model_path: "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    n_ctx: 4096
    n_gpu_layers: 0
    temperature: 0.7

embeddings:
  model: "all-MiniLM-L6-v2"
  batch_size: 32
  device: "cuda"

retrieval:
  top_k: 5
  use_reranker: true
  reranker_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"

chunking:
  chunk_size: 512
  chunk_overlap: 50
  min_chunk_size: 100

generation:
  summary:
    max_tokens: 1500
    temperature: 0.7
  flashcards:
    max_tokens: 1500
    max_cards: 20
  quiz:
    max_tokens: 1500
    num_questions: 10
```

---

## 📊 Performance Characteristics

### Processing Times (30-min audio)

| Stage | Time (CPU) | Time (GPU) |
|-------|-----------|-----------|
| ASR (Whisper) | ~8 min | ~2 min |
| Chunking | ~5 sec | ~5 sec |
| Embeddings | ~10 sec | ~3 sec |
| Summary | ~3 min | ~1 min |
| Flashcards | ~4 min | ~1.5 min |
| Quiz | ~4 min | ~1.5 min |
| **Total (first)** | ~19 min | ~6 min |
| **Total (cached)** | ~11 min | ~4 min |

### Memory Usage

| Component | RAM | VRAM (GPU) |
|-----------|-----|-----------|
| LLM | ~4GB | ~4GB |
| Embeddings | ~500MB | ~500MB |
| Whisper | ~3GB | ~3GB |
| FAISS Index | ~100MB | - |
| **Total** | ~8GB | ~8GB |

---

## 🔌 Extension Points

### Adding New Content Types

1. Create processor in `src/ingestion/`
2. Implement `process()` method
3. Register in `StudyAssistantPipeline`

### Adding New Retrieval Methods

1. Create retriever in `src/retrieval/`
2. Implement `retrieve()` method
3. Add to hybrid retriever

### Adding New Generation Tasks

1. Create generator in `src/generation/`
2. Define prompt template
3. Implement parsing logic
4. Register in MCP server

---

## 📚 Additional Resources

- **[README.md](README.md)** - Project overview
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Installation instructions
- **[MCP_SERVER.md](MCP_SERVER.md)** - MCP server documentation
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Implementation status

---

**Technical specification complete!** 🚀

