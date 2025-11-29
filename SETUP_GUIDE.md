# Setup Guide - Study Assistant

Complete setup guide from downloading models to running the MCP server and frontend.

---

## 📋 Prerequisites

- **Python 3.10+** (required)
- **4GB+ RAM** (8GB+ recommended)
- **~20GB disk space** (for models and data)
- **CUDA-capable GPU** (optional, for faster processing)
- **Internet connection** (for initial model download only)

---

## 🚀 Quick Setup (Recommended)

### Option 1: MCP Server with Web Interface

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd study-assistant

# 2. Run the setup script (one-time)
./setup_mcp_server.sh

# This will:
# - Check Python version
# - Create virtual environment (aivenv/)
# - Install all dependencies
# - Create necessary directories
# - Generate start/stop scripts

# 3. Start the MCP server
./start_mcp_server.sh

# 4. In a new terminal, start the frontend
./start_frontend.sh

# 5. Open your browser
# Frontend: http://localhost:8080
# API: http://localhost:5000
```

**That's it!** The system is ready to use.

---

## 📥 Model Download

### Automatic Download (Recommended)

Most models download automatically on first use:
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (auto-downloads)
- **Whisper**: openai/whisper-large (auto-downloads)
- **Reranker**: cross-encoder/ms-marco-MiniLM-L-6-v2 (auto-downloads)

### Manual LLM Download (One-time)

The LLM model needs to be downloaded manually:

```bash
# Create models directory
mkdir -p models

# Install HuggingFace CLI
pip install huggingface-hub

# Download Mistral-7B-Instruct (recommended, ~4GB)
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF \
  mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  --local-dir models/ \
  --local-dir-use-symlinks False
```

**Alternative Models** (choose one):

```bash
# Llama-2-7B (good quality, ~4GB)
huggingface-cli download TheBloke/Llama-2-7B-Chat-GGUF \
  llama-2-7b-chat.Q4_K_M.gguf \
  --local-dir models/ --local-dir-use-symlinks False

# Phi-3-Mini (faster, smaller, ~2GB)
huggingface-cli download microsoft/Phi-3-mini-4k-instruct-gguf \
  Phi-3-mini-4k-instruct-q4.gguf \
  --local-dir models/ --local-dir-use-symlinks False

# Gemma-2B (smallest, fastest, ~1.5GB)
huggingface-cli download google/gemma-2b-it-GGUF \
  gemma-2b-it-q4_k_m.gguf \
  --local-dir models/ --local-dir-use-symlinks False
```

### Update Configuration

Edit `config/config.yaml` to match your downloaded model:

```yaml
llm:
  provider: "local"
  local:
    model: "mistral-7b-instruct-v0.2.Q4_K_M"  # Match your downloaded file
    model_path: "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    n_ctx: 4096
    n_gpu_layers: 0  # Set to 35 if you have GPU
```

---

## 🔧 Manual Setup (Alternative)

If you prefer manual setup or the script doesn't work:

### 1. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv aivenv

# Activate it
source aivenv/bin/activate  # On Windows: aivenv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# For GPU support (optional)
pip install faiss-gpu
```

### 3. Create Directories

```bash
# Create necessary directories
mkdir -p data/uploads data/outputs data/cache data/training data/preprocessed
mkdir -p data/cache/sessions
mkdir -p results/models results/metrics results/hparams
mkdir -p models
```

### 4. Download Models

Follow the "Manual LLM Download" section above.

### 5. Test Installation

```bash
# Test basic pipeline
python examples/basic_usage.py

# Test MCP server
python test_mcp_server.py
```

---

## 🌐 Running the System

### MCP Server + Frontend

```bash
# Terminal 1: Start MCP server
./start_mcp_server.sh
# Server runs on http://localhost:5000

# Terminal 2: Start frontend
./start_frontend.sh
# Frontend runs on http://localhost:8080
```

### Python API Only

```python
from src.pipeline import StudyAssistantPipeline

# Initialize
pipeline = StudyAssistantPipeline()

# Ingest documents
pipeline.ingest_pdf("data/uploads/lecture.pdf")
pipeline.ingest_audio("data/uploads/lecture.mp3")

# Generate study materials
summaries = pipeline.generate_summaries()
flashcards = pipeline.generate_flashcards()
quizzes = pipeline.generate_quizzes()

# Export
pipeline.export_anki("output.apkg")
```

---

## ✅ Verification

### Check Installation

```bash
# Activate environment
source aivenv/bin/activate

# Check Python version
python --version  # Should be 3.10+

# Check installed packages
pip list | grep -E "torch|faiss|transformers|llama-cpp"

# Check models directory
ls -lh models/
```

### Test MCP Server

```bash
# Start server
./start_mcp_server.sh

# In another terminal, test health endpoint
curl http://localhost:5000/health

# Should return: {"status": "healthy", ...}
```

### Test Frontend

```bash
# Start frontend
./start_frontend.sh

# Open browser to http://localhost:8080
# You should see the upload interface
```

---

## 🐛 Troubleshooting

### Issue: "Python version too old"

```bash
# Install Python 3.10+
# On Ubuntu/Debian:
sudo apt update
sudo apt install python3.10 python3.10-venv

# On macOS:
brew install python@3.10
```

### Issue: "pip install fails"

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Try installing again
pip install -r requirements.txt
```

### Issue: "Model not found"

```bash
# Check models directory
ls -lh models/

# Re-download model
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF \
  mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  --local-dir models/ --local-dir-use-symlinks False
```

### Issue: "Port 5000 already in use"

```bash
# Find process using port 5000
lsof -i :5000

# Kill it
kill -9 <PID>

# Or use different port
python -m mcp_server.server --port 5001
```

### Issue: "Out of memory"

```bash
# Use smaller model (Phi-3 or Gemma)
# Or reduce batch size in config/config.yaml:
embeddings:
  batch_size: 8  # Reduce from 32
```

### Issue: "CUDA not available"

```bash
# Check CUDA
python -c "import torch; print(torch.cuda.is_available())"

# If False, install CUDA toolkit or use CPU
# Set in config/config.yaml:
system:
  device: "cpu"
```

---

## 📊 System Requirements

### Minimum (CPU only)
- Python 3.10+
- 4GB RAM
- 10GB disk space
- Processing time: ~15-20 min per audio file

### Recommended (with GPU)
- Python 3.10+
- 8GB RAM
- 4GB+ VRAM (NVIDIA GPU)
- 20GB disk space
- Processing time: ~5-10 min per audio file

### High Performance
- Python 3.10+
- 16GB RAM
- 8GB+ VRAM (NVIDIA GPU)
- 30GB disk space
- Processing time: ~2-5 min per audio file

---

## 🎯 Next Steps

After setup is complete:

1. **Test with sample data**: Upload a PDF or audio file via the web interface
2. **Generate study materials**: Try all 3 modes (Summary, Flashcards, Quiz)
3. **Explore the API**: See [MCP_SERVER.md](MCP_SERVER.md) for API documentation
4. **Customize configuration**: Edit `config/config.yaml` to adjust settings
5. **Optional: Finetune models**: See advanced training section in README.md

---

## 📚 Additional Resources

- **[README.md](README.md)** - Project overview
- **[MCP_SERVER.md](MCP_SERVER.md)** - MCP server documentation
- **[PROJECT_SPECIFICATION.md](PROJECT_SPECIFICATION.md)** - Technical details
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Implementation status

---

**Setup complete! Start using the Study Assistant now.** 🚀

