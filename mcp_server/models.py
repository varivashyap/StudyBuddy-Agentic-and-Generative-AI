"""
Model registry for MCP server.
Allows registration and management of multiple models.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.pipeline import StudyAssistantPipeline
from src.config import get_config

logger = logging.getLogger(__name__)


class ModelInfo:
    """Information about a registered model."""
    
    def __init__(
        self,
        name: str,
        description: str,
        model_path: Optional[str] = None,
        lora_adapter: Optional[str] = None,
        config_overrides: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize model info.
        
        Args:
            name: Model name/identifier
            description: Human-readable description
            model_path: Path to model file (if custom)
            lora_adapter: Path to LoRA adapter (if using finetuned model)
            config_overrides: Configuration overrides for this model
        """
        self.name = name
        self.description = description
        self.model_path = model_path
        self.lora_adapter = lora_adapter
        self.config_overrides = config_overrides or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'description': self.description,
            'model_path': self.model_path,
            'lora_adapter': self.lora_adapter,
            'has_custom_config': bool(self.config_overrides)
        }


class ModelRegistry:
    """Registry for managing multiple models."""
    
    def __init__(self):
        """Initialize model registry."""
        self.models: Dict[str, ModelInfo] = {}
        self.pipelines: Dict[str, StudyAssistantPipeline] = {}
        
        # Register default models
        self._register_default_models()
    
    def _register_default_models(self):
        """Register the default models."""
        # Default model (base Mistral)
        self.register_model(ModelInfo(
            name='default',
            description='Default Mistral-7B-Instruct model',
            model_path=None,  # Uses config default
            lora_adapter=None
        ))
        
        # Check for finetuned models
        models_dir = Path(__file__).parent.parent / 'models' / 'lora_adapters'
        
        if (models_dir / 'summary').exists():
            self.register_model(ModelInfo(
                name='summary_finetuned',
                description='Finetuned model for summary generation',
                lora_adapter=str(models_dir / 'summary')
            ))
        
        if (models_dir / 'flashcard').exists():
            self.register_model(ModelInfo(
                name='flashcard_finetuned',
                description='Finetuned model for flashcard generation',
                lora_adapter=str(models_dir / 'flashcard')
            ))
        
        if (models_dir / 'quiz').exists():
            self.register_model(ModelInfo(
                name='quiz_finetuned',
                description='Finetuned model for quiz generation',
                lora_adapter=str(models_dir / 'quiz')
            ))
    
    def register_model(self, model_info: ModelInfo):
        """
        Register a new model.
        
        Args:
            model_info: Model information
        """
        self.models[model_info.name] = model_info
        logger.info(f"Registered model: {model_info.name}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models."""
        return [model.to_dict() for model in self.models.values()]
    
    def get_pipeline(self, model_name: str = 'default') -> StudyAssistantPipeline:
        """
        Get or create a pipeline for the specified model.
        
        Args:
            model_name: Name of the model to use
        
        Returns:
            StudyAssistantPipeline instance
        """
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}. Available: {list(self.models.keys())}")
        
        # Return cached pipeline if exists
        if model_name in self.pipelines:
            # Create new pipeline instance to avoid state issues
            # Each request gets a fresh pipeline
            pass
        
        # Create new pipeline
        model_info = self.models[model_name]
        
        # Apply config overrides if any
        if model_info.config_overrides:
            # TODO: Implement config override mechanism
            logger.warning("Config overrides not yet implemented")
        
        # Create pipeline
        pipeline = StudyAssistantPipeline()
        
        # Apply LoRA adapter if specified
        if model_info.lora_adapter:
            logger.info(f"Loading LoRA adapter: {model_info.lora_adapter}")
            # TODO: Implement LoRA adapter loading
            # This would require modifying the LLMClient to support adapter loading
            logger.warning("LoRA adapter loading not yet implemented in pipeline")
        
        return pipeline

