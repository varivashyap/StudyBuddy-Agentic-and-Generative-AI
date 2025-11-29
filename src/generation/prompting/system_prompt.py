"""System prompting with role definition."""

import logging
from typing import Dict, Optional
from .base_prompt import BasePrompt

logger = logging.getLogger(__name__)


class SystemPrompt(BasePrompt):
    """System prompting with role and instruction definition."""
    
    def __init__(self, task_type: str, config: Optional[Dict] = None):
        """
        Initialize system prompt.
        
        Args:
            task_type: Type of task (summary, flashcard, quiz)
            config: Optional configuration dictionary
        """
        super().__init__(task_type, config)
        
        # System roles for each task
        self.system_roles = {
            'summary': "You are an expert educational content summarizer. Your task is to create clear, concise, and accurate summaries that capture the key concepts and main ideas.",
            'flashcard': "You are an expert flashcard creator. Your task is to generate effective study flashcards that help students learn and retain key concepts.",
            'quiz': "You are an expert quiz question writer. Your task is to create challenging but fair questions that test understanding of the material.",
        }
    
    def get_system_message(self) -> str:
        """
        Get system message for the task.
        
        Returns:
            System message string
        """
        return self.system_roles.get(self.task_type, "You are a helpful AI assistant.")
    
    def get_prompt(self, context: str, **kwargs) -> str:
        """
        Get formatted prompt with system message.
        
        Args:
            context: The main context/content
            **kwargs: Additional parameters
            
        Returns:
            Formatted prompt with system message
        """
        system_msg = self.get_system_message()
        user_prompt = self.format_prompt(context, **kwargs)
        
        # Format as system + user message
        full_prompt = f"System: {system_msg}\n\nUser: {user_prompt}"
        
        return full_prompt

