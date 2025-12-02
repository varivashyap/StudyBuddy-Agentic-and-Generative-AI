"""Base prompting class."""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class BasePrompt:
    """Base class for prompting strategies."""
    
    def __init__(self, task_type: str, config: Optional[Dict] = None):
        """
        Initialize base prompt.
        
        Args:
            task_type: Type of task (summary, flashcard, quiz)
            config: Optional configuration dictionary
        """
        self.task_type = task_type
        self.config = config or {}
        
        # Default prompts for each task
        self.default_prompts = {
            'summary': {
                'sentence': 'Summarize the following text in one sentence:\n\n{context}\n\nSummary:',
                'paragraph': 'Summarize the following text in a paragraph:\n\n{context}\n\nSummary:',
                'section': 'Provide a detailed summary of the following text:\n\n{context}\n\nSummary:',
            },
            'flashcard': 'Generate flashcards from the following text:\n\n{context}\n\nFlashcards:',
            'quiz': 'Generate quiz questions from the following text:\n\n{context}\n\nQuestions:',
        }
    
    def format_prompt(self, context: str, **kwargs) -> str:
        """
        Format prompt with context and additional parameters.
        
        Args:
            context: The main context/content
            **kwargs: Additional parameters for formatting
            
        Returns:
            Formatted prompt string
        """
        # Get base prompt template
        if self.task_type == 'summary':
            scale = kwargs.get('scale', 'paragraph')
            template = self.default_prompts['summary'].get(scale, self.default_prompts['summary']['paragraph'])
        else:
            template = self.default_prompts.get(self.task_type, '')
        
        # Format with context and kwargs
        try:
            prompt = template.format(context=context, **kwargs)
        except KeyError as e:
            logger.warning(f"Missing key in template: {e}. Using basic format.")
            prompt = f"{template}\n\n{context}"
        
        return prompt
    
    def load_custom_prompt(self, prompt_path: str) -> str:
        """
        Load custom prompt from file.
        
        Args:
            prompt_path: Path to prompt file
            
        Returns:
            Prompt template string
        """
        path = Path(prompt_path)
        if not path.exists():
            logger.warning(f"Prompt file not found: {prompt_path}")
            return ""
        
        with open(path, 'r') as f:
            prompt = f.read().strip()
        
        logger.info(f"Loaded custom prompt from {prompt_path}")
        return prompt
    
    def get_prompt(self, context: str, **kwargs) -> str:
        """
        Get formatted prompt (can be overridden by subclasses).
        
        Args:
            context: The main context/content
            **kwargs: Additional parameters
            
        Returns:
            Formatted prompt
        """
        # Check for custom prompt path
        prompt_path = self.config.get('prompt_path')
        if prompt_path:
            custom_template = self.load_custom_prompt(prompt_path)
            if custom_template:
                try:
                    return custom_template.format(context=context, **kwargs)
                except KeyError:
                    logger.warning("Custom template formatting failed, using default")
        
        # Use default formatting
        return self.format_prompt(context, **kwargs)

