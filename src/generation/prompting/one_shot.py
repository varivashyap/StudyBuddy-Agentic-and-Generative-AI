"""One-shot prompting with a single example."""

import logging
import json
from typing import Dict, Optional
from pathlib import Path
from .base_prompt import BasePrompt

logger = logging.getLogger(__name__)


class OneShotPrompt(BasePrompt):
    """One-shot prompting with a single exemplar."""
    
    def __init__(self, task_type: str, config: Optional[Dict] = None):
        """
        Initialize one-shot prompt.
        
        Args:
            task_type: Type of task (summary, flashcard, quiz)
            config: Optional configuration dictionary
        """
        super().__init__(task_type, config)
        
        # Default examples for each task
        self.default_examples = {
            'summary': {
                'input': "Photosynthesis is the process by which plants convert light energy into chemical energy. Chlorophyll in plant cells absorbs sunlight, which is then used to convert carbon dioxide and water into glucose and oxygen.",
                'output': "Photosynthesis is the process where plants use sunlight, carbon dioxide, and water to produce glucose and oxygen through chlorophyll."
            },
            'flashcard': {
                'input': "The mitochondria is known as the powerhouse of the cell because it produces ATP through cellular respiration.",
                'output': json.dumps([{
                    'front': 'What is the mitochondria known as?',
                    'back': 'The powerhouse of the cell',
                    'type': 'definition'
                }])
            },
            'quiz': {
                'input': "Newton's First Law states that an object at rest stays at rest and an object in motion stays in motion unless acted upon by an external force.",
                'output': json.dumps([{
                    'question': 'What does Newton\'s First Law state?',
                    'answer': 'An object at rest stays at rest and an object in motion stays in motion unless acted upon by an external force.',
                    'type': 'short_answer'
                }])
            }
        }
    
    def load_example(self, example_path: Optional[str] = None) -> Dict[str, str]:
        """
        Load example from file or use default.
        
        Args:
            example_path: Optional path to example file
            
        Returns:
            Dictionary with 'input' and 'output' keys
        """
        if example_path:
            path = Path(example_path)
            if path.exists():
                with open(path, 'r') as f:
                    example = json.load(f)
                logger.info(f"Loaded example from {example_path}")
                return example
            else:
                logger.warning(f"Example file not found: {example_path}")
        
        # Use default example
        return self.default_examples.get(self.task_type, {'input': '', 'output': ''})
    
    def get_prompt(self, context: str, **kwargs) -> str:
        """
        Get formatted one-shot prompt with example.
        
        Args:
            context: The main context/content
            **kwargs: Additional parameters
            
        Returns:
            Formatted one-shot prompt
        """
        # Load example
        example_path = self.config.get('example_path')
        example = self.load_example(example_path)
        
        # Format instruction
        instruction = self.format_prompt("", **kwargs).split('\n\n')[0]  # Get just the instruction part
        
        # Build one-shot prompt
        prompt = f"""{instruction}

Example:
Input: {example['input']}
Output: {example['output']}

Now, apply the same approach to this input:
Input: {context}
Output:"""
        
        return prompt

