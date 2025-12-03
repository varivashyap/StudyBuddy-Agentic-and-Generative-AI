# CrewAI Integration for Study Assistant

This document explains how to use the CrewAI multi-agent integration with the Study Assistant project.

## 🤖 What is CrewAI Integration?

CrewAI integration adds multi-agent collaboration to the Study Assistant, where specialized AI agents work together to create higher-quality study materials:

- **Research Agent**: Analyzes documents and extracts key concepts
- **Content Generator Agent**: Creates summaries, flashcards, and quizzes based on research insights
- **Quality Reviewer Agent**: Reviews and improves generated content for educational effectiveness

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install CrewAI and related dependencies
pip install -r requirements.txt
```

### 2. Check CrewAI Status

```python
from src.pipeline import StudyAssistantPipeline

pipeline = StudyAssistantPipeline()
print(f"CrewAI available: {pipeline.is_crewai_available()}")
```

### 3. Generate Enhanced Study Materials

```python
# Generate complete study package with CrewAI
result = pipeline.generate_complete_study_package(
    file_path="data/your_lecture.pdf",
    use_crewai=True
)

print(f"Status: {result['status']}")
print(f"Generation method: {result['generation_method']}")
```

## 📋 Available Workflows

### Comprehensive Workflow
```python
result = pipeline.generate_enhanced_study_materials(
    file_path="lecture.pdf",
    content_types=["summaries", "flashcards", "quiz"],
    workflow_type="comprehensive",
    enable_quality_review=True
)
```

### Focused Workflows
```python
# Enhanced summaries only
summaries = pipeline.generate_crewai_summaries("lecture.pdf")

# Enhanced flashcards only
flashcards = pipeline.generate_crewai_flashcards("lecture.pdf")

# Enhanced quiz only
quiz = pipeline.generate_crewai_quiz("lecture.pdf")
```

### Custom Workflow
```python
# Custom content types with specific workflow
result = pipeline.generate_enhanced_study_materials(
    file_path="lecture.pdf",
    content_types=["summaries", "flashcards"],  # Only these
    workflow_type="focused",
    enable_quality_review=True
)
```

## 🌐 API Usage

### Start MCP Server
```bash
python mcp_server/server.py --host 0.0.0.0 --port 5000
```

### CrewAI API Endpoints

#### Check Status
```bash
curl http://localhost:5000/crewai/status
```

#### Comprehensive Processing
```bash
curl -X POST http://localhost:5000/crewai/process \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "uploaded_file_id",
    "workflow_type": "comprehensive",
    "content_types": ["summaries", "flashcards", "quiz"],
    "enable_quality_review": true
  }'
```

#### Enhanced Summaries
```bash
curl -X POST http://localhost:5000/crewai/enhanced-summaries \
  -H "Content-Type: application/json" \
  -d '{"file_id": "uploaded_file_id"}'
```

#### Enhanced Flashcards
```bash
curl -X POST http://localhost:5000/crewai/enhanced-flashcards \
  -H "Content-Type: application/json" \
  -d '{"file_id": "uploaded_file_id"}'
```

#### Enhanced Quiz
```bash
curl -X POST http://localhost:5000/crewai/enhanced-quiz \
  -H "Content-Type: application/json" \
  -d '{"file_id": "uploaded_file_id"}'
```

#### Complete Study Package
```bash
curl -X POST http://localhost:5000/crewai/complete-package \
  -H "Content-Type: application/json" \
  -d '{"file_id": "uploaded_file_id", "use_crewai": true}'
```

#### List Available Workflows
```bash
curl http://localhost:5000/crewai/workflows
```

## 🔧 CLI Usage

### Check Status
```bash
python examples/crewai_cli.py --status
```

### List Workflows
```bash
python examples/crewai_cli.py --list-workflows
```

### Generate Complete Study Package
```bash
python examples/crewai_cli.py --file data/lecture.pdf --complete
```

### Generate Specific Content Types
```bash
python examples/crewai_cli.py --file data/lecture.pdf --content summaries flashcards --workflow focused
```

### Save Results to File
```bash
python examples/crewai_cli.py --file data/lecture.pdf --complete --output results.json
```

## ⚙️ Configuration

CrewAI settings are configured in `config/config.yaml`:

```yaml
crewai:
  enabled: true
  default_workflow: "comprehensive"
  enable_quality_review: true
  
  agents:
    research_agent:
      role: "Research Analyst"
      temperature: 0.3
      max_tokens: 1000
    
    content_generator:
      role: "Educational Content Creator"
      temperature: 0.4
      max_tokens: 1500
    
    quality_reviewer:
      role: "Educational Quality Reviewer"
      temperature: 0.2
      max_tokens: 800
  
  workflows:
    comprehensive:
      content_types: ["summaries", "flashcards", "quiz"]
      enable_quality_review: true
```

## 🎯 Benefits of CrewAI Integration

### Enhanced Quality
- **Multi-agent collaboration**: Different agents specialize in different aspects
- **Quality review**: Dedicated agent reviews and improves content
- **Research-driven**: Content based on thorough document analysis

### Better Educational Value
- **Concept extraction**: Research agent identifies key learning concepts
- **Pedagogical focus**: Content generator optimized for learning
- **Quality assurance**: Reviewer ensures educational effectiveness

### Flexibility
- **Multiple workflows**: Choose the right workflow for your needs
- **Configurable**: Customize agent behavior via configuration
- **Fallback**: Automatically falls back to standard pipeline if CrewAI fails

## 🔄 Workflow Types Explained

### 1. Comprehensive
- Full multi-agent workflow
- All content types (summaries, flashcards, quiz)
- Includes quality review
- Best for complete study packages

### 2. Focused
- Selected content types
- Multi-agent collaboration
- Includes quality review
- Best for specific material types

### 3. Summaries
- Enhanced summary generation
- Research analysis + content generation + review
- Best for high-quality summaries

### 4. Flashcards
- Enhanced flashcard creation
- Concept extraction + card generation + review
- Best for effective flashcards

### 5. Quiz
- Enhanced quiz generation
- Analysis + question creation + validation
- Best for quality assessments

## 🐛 Troubleshooting

### CrewAI Not Available
```python
# Check if dependencies are installed
try:
    import crewai
    import langchain
    print("Dependencies installed")
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install crewai langchain langchain-community")
```

### Performance Issues
- CrewAI workflows are more resource-intensive than standard pipeline
- Consider using focused workflows for faster generation
- Adjust `crewai.performance` settings in config.yaml

### Memory Issues
```yaml
# In config.yaml
crewai:
  performance:
    memory_optimization: true
    parallel_agents: false  # Run agents sequentially
    shared_llm: true       # Share LLM instance
```

### Timeouts
```yaml
# In config.yaml
crewai:
  performance:
    timeout_seconds: 600  # Increase timeout (default: 300)
```

## 📊 Standard vs CrewAI Comparison

| Feature | Standard Pipeline | CrewAI Enhanced |
|---------|------------------|-----------------|
| Speed | Faster | Slower (higher quality) |
| Quality | Good | Excellent |
| Research Analysis | Basic | Comprehensive |
| Quality Review | None | Dedicated agent |
| Collaboration | Single LLM | Multi-agent |
| Configuration | Simple | Advanced |
| Resource Usage | Lower | Higher |
| Fallback | N/A | Auto-fallback to standard |

## 🔗 Integration Points

CrewAI integrates seamlessly with existing Study Assistant features:

- **RAG Pipeline**: Uses existing retrieval and vector store
- **LLM Client**: Shares the same local LLM infrastructure
- **Export Formats**: Works with existing Anki and CSV exporters
- **Configuration**: Extends existing config.yaml
- **MCP Server**: Adds new endpoints alongside existing ones
- **Frontend**: Compatible with existing web interface

## 📝 Example Scripts

Run the example scripts to see CrewAI in action:

```bash
# Basic usage examples
python examples/crewai_examples.py

# Interactive CLI
python examples/crewai_cli.py --help
```

## 🚀 Next Steps

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Test Status**: `python examples/crewai_cli.py --status`
3. **Try Examples**: `python examples/crewai_examples.py`
4. **Use CLI**: `python examples/crewai_cli.py --file your_file.pdf --complete`
5. **API Integration**: Start MCP server and use API endpoints
6. **Customize**: Modify `config/config.yaml` for your needs

For more information, see the main project README and documentation.

