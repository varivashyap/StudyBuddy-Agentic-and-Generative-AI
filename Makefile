.PHONY: help install test lint format clean run-example preprocess train tune evaluate

# Help
help:
	@echo "Study Assistant - Makefile Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install              Install all dependencies"
	@echo "  make install-dev          Install in development mode"
	@echo "  make setup                Create data directories"
	@echo ""
	@echo "Data Processing:"
	@echo "  make preprocess           Preprocess sample data (OCR + ASR)"
	@echo "  make test-preprocessed    Test using preprocessed data"
	@echo ""
	@echo "Training:"
	@echo "  make train-summary        Finetune model for summaries"
	@echo "  make train-flashcard      Finetune model for flashcards"
	@echo "  make train-quiz           Finetune model for quizzes"
	@echo "  make train-all            Finetune all tasks"
	@echo ""
	@echo "Hyperparameter Tuning:"
	@echo "  make tune-grid            Grid search for hyperparameters"
	@echo "  make tune-bayesian        Bayesian optimization"
	@echo ""
	@echo "Evaluation:"
	@echo "  make evaluate             Evaluate current model"
	@echo "  make evaluate-improvement Compare before/after finetuning"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test                 Run all tests"
	@echo "  make test-fast            Run tests (stop on first failure)"
	@echo "  make lint                 Check code quality"
	@echo "  make format               Format code with black"
	@echo ""
	@echo "Running:"
	@echo "  make run-example          Run basic usage example"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean                Clean cache and temporary files"
	@echo "  make check-setup          Check system setup"
	@echo ""

# Installation
install:
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm

install-dev:
	pip install -r requirements.txt
	pip install -e .

# Data Processing
preprocess:
	@echo "Preprocessing sample data..."
	python scripts/preprocess_sample_data.py

test-preprocessed:
	@echo "Testing with preprocessed data..."
	python scripts/test_from_preprocessed.py

# Training
train-summary:
	@echo "Finetuning model for summaries..."
	python -m src.training.finetune --task summary

train-flashcard:
	@echo "Finetuning model for flashcards..."
	python -m src.training.finetune --task flashcard

train-quiz:
	@echo "Finetuning model for quizzes..."
	python -m src.training.finetune --task quiz

train-all:
	@echo "Finetuning all tasks..."
	python -m src.training.finetune --task all

# Hyperparameter Tuning
tune-grid:
	@echo "Running grid search..."
	python -m src.training.hparam_search --method grid

tune-bayesian:
	@echo "Running Bayesian optimization..."
	python -m src.training.hparam_search --method bayesian

# Evaluation
evaluate:
	@echo "Evaluating model..."
	python -m src.evaluation.improvement_metrics --mode evaluate

evaluate-improvement:
	@echo "Comparing before/after improvements..."
	python scripts/evaluate_improvements.py

# Web Search
test-websearch:
	@echo "Testing web search features..."
	python scripts/test_websearch.py

# MCP Server
setup-mcp:
	@echo "Setting up MCP server..."
	./setup_mcp_server.sh

start-mcp:
	@echo "Starting MCP server..."
	./start_mcp_server.sh

stop-mcp:
	@echo "Stopping MCP server..."
	./stop_mcp_server.sh

test-mcp:
	@echo "Testing MCP server..."
	python test_mcp_server.py

start-frontend:
	@echo "Starting frontend server..."
	./start_frontend.sh

# Testing
test:
	pytest tests/ -v --cov=src --cov-report=html

test-fast:
	pytest tests/ -v -x

# Code quality
lint:
	flake8 src/ tests/ --max-line-length=100
	mypy src/

format:
	black src/ tests/ examples/

# Cleaning
clean:
	@echo "Cleaning cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	rm -rf data/cache/*
	@echo "✓ Cleanup complete"

# Running
run-example:
	python examples/basic_usage.py

# Setup
setup:
	mkdir -p data/uploads data/outputs data/cache data/training data/preprocessed
	mkdir -p results/models results/metrics results/hparams
	@echo "✓ Created data directories"

check-setup:
	@echo "Checking system setup..."
	python check_setup.py

# Documentation
docs:
	@echo "Documentation generation not yet implemented"

# Docker (optional)
docker-build:
	docker build -t study-assistant .

docker-run:
	docker run -it --rm -v $(PWD)/data:/app/data study-assistant

