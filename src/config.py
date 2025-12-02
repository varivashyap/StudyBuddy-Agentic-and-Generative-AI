"""Configuration management for Study Assistant."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class PDFConfig(BaseSettings):
    """PDF processing configuration."""
    model_config = {"extra": "ignore"}  # Ignore extra fields like layout_parser

    primary_tool: str = Field(default="pdfplumber", alias="tools.primary")
    ocr_fallback: str = Field(default="tesseract", alias="tools.ocr_fallback")
    ocr_confidence_threshold: float = Field(default=0.7, alias="ocr.confidence_threshold")
    max_page_chunk_chars: int = Field(default=3000, alias="ocr.max_page_chunk_chars")


class AudioConfig(BaseSettings):
    """Audio processing configuration."""
    model_config = {"extra": "ignore"}  # Ignore extra fields

    asr_model: str = Field(default="whisper-large", alias="asr.model")
    asr_language: str = Field(default="en", alias="asr.language")
    beam_size: int = Field(default=5, alias="asr.beam_size")
    chunk_length_seconds: int = Field(default=30, alias="asr.chunk_length_seconds")
    diarization_enabled: bool = Field(default=False, alias="diarization.enabled")


class ChunkingConfig(BaseSettings):
    """Text chunking configuration."""
    model_config = {"extra": "ignore"}  # Ignore extra fields

    method: str = "sentence_sliding_window"
    chunk_size_tokens: int = 300
    overlap_tokens: int = 60
    min_chunk_size: int = 100
    max_chunk_size: int = 400


class EmbeddingsConfig(BaseSettings):
    """Embeddings configuration (local models only)."""
    model_config = {"extra": "ignore"}  # Ignore extra fields

    model: str = "all-MiniLM-L6-v2"  # Default to local model
    batch_size: int = 32
    normalize: bool = True
    # dimension is auto-detected from model


class RetrievalConfig(BaseSettings):
    """Retrieval configuration."""
    model_config = {"extra": "ignore"}  # Ignore extra fields

    hybrid_enabled: bool = Field(default=True, alias="hybrid.enabled")
    vector_weight: float = Field(default=0.7, alias="hybrid.vector_weight")
    bm25_weight: float = Field(default=0.3, alias="hybrid.bm25_weight")
    top_k: int = 20
    reranker_enabled: bool = Field(default=True, alias="reranker.enabled")
    reranker_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        alias="reranker.model"
    )
    top_m: int = Field(default=6, alias="reranker.top_m")


class LLMConfig(BaseSettings):
    """LLM configuration (local only - no paid APIs)."""
    model_config = {"extra": "ignore"}  # Ignore extra fields

    provider: str = "local"  # Only "local" supported
    local_model: str = Field(default="mistral-7b-instruct-v0.2.Q4_K_M", alias="local.model")
    local_quantization: str = Field(default="Q4_K_M", alias="local.quantization")


class GenerationConfig(BaseSettings):
    """Generation settings for different output types."""
    model_config = {"extra": "ignore"}  # Ignore extra fields

    summary_temperature: float = Field(default=0.1, alias="summaries.temperature")
    summary_max_tokens: int = Field(default=600, alias="summaries.max_tokens")
    
    flashcard_temperature: float = Field(default=0.25, alias="flashcards.temperature")
    flashcard_max_tokens: int = Field(default=150, alias="flashcards.max_tokens")
    flashcard_max_cards: int = Field(default=200, alias="flashcards.max_cards")
    flashcard_min_similarity: float = Field(default=0.74, alias="flashcards.validation.min_similarity")
    
    quiz_temperature: float = Field(default=0.2, alias="quizzes.temperature")
    quiz_max_tokens: int = Field(default=200, alias="quizzes.max_tokens")


class SystemConfig(BaseSettings):
    """System configuration."""
    model_config = {"extra": "ignore"}  # Ignore extra fields

    device: str = "cpu"
    max_workers: int = 4
    cache_dir: str = "data/cache"
    log_level: str = "INFO"


class Config:
    """Main configuration class (100% open-source, no API keys required)."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from YAML file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self._raw_config = self._load_yaml()

        # Initialize sub-configs
        self.pdf = self._get_nested_config("pdf", PDFConfig)
        self.audio = self._get_nested_config("audio", AudioConfig)
        self.chunking = self._get_nested_config("chunking", ChunkingConfig)
        self.embeddings = self._get_nested_config("embeddings", EmbeddingsConfig)
        self.retrieval = self._get_nested_config("retrieval", RetrievalConfig)
        self.llm = self._get_nested_config("llm", LLMConfig)
        self.generation = self._get_nested_config("generation", GenerationConfig)
        self.system = self._get_nested_config("system", SystemConfig)

        # NO API KEYS - All removed (OpenAI, Anthropic, Google Cloud)
        # This project uses 100% local, open-source models
    
    def _load_yaml(self) -> Dict[str, Any]:
        """Load YAML configuration file."""
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)
    
    def _get_nested_config(self, key: str, config_class: type) -> Any:
        """Get nested configuration section."""
        section = self._raw_config.get(key, {})
        return config_class(**self._flatten_dict(section))
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split(".")
        value = self._raw_config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

