"""Few-shot prompting with multiple examples."""

import logging
import json
from typing import Dict, List, Optional
from pathlib import Path
from .base_prompt import BasePrompt

logger = logging.getLogger(__name__)


class FewShotPrompt(BasePrompt):
    """Few-shot prompting with multiple exemplars."""
    
    def __init__(self, task_type: str, config: Optional[Dict] = None):
        """
        Initialize few-shot prompt.
        
        Args:
            task_type: Type of task (summary, flashcard, quiz)
            config: Optional configuration dictionary
        """
        super().__init__(task_type, config)
        self.num_shots = config.get('num_shots', 3) if config else 3
        
        # Default examples for each task (multiple)
        self.default_examples = {
            'summary': [
                {
                    'input': "Photosynthesis is the process by which plants convert light energy into chemical energy.",
                    'output': "Plants convert light energy to chemical energy through photosynthesis."
                },
                {
                    'input': "The water cycle describes how water evaporates from surfaces, forms clouds, and returns as precipitation.",
                    'output': "The water cycle involves evaporation, cloud formation, and precipitation."
                },
                {
                    'input': "DNA contains genetic instructions for the development and function of living organisms.",
                    'output': "DNA stores genetic instructions for organism development and function."
                }
            ],
            'flashcard': [
                {
                    'input': "The mitochondria produces ATP through cellular respiration.",
                    'output': json.dumps([{'front': 'What does mitochondria produce?', 'back': 'ATP through cellular respiration', 'type': 'definition'}])
                },
                {
                    'input': "Osmosis is the movement of water across a semipermeable membrane.",
                    'output': json.dumps([{'front': 'Define osmosis', 'back': 'Movement of water across a semipermeable membrane', 'type': 'definition'}])
                }
            ],
            'quiz': [
                {
                    'input': "Newton's First Law states that objects in motion stay in motion unless acted upon by a force.",
                    'output': json.dumps([{'question': 'What is Newton\'s First Law?', 'answer': 'Objects in motion stay in motion unless acted upon by a force', 'type': 'short_answer'}])
                },
                {
                    'input': "The speed of light is approximately 299,792,458 meters per second.",
                    'output': json.dumps([{'question': 'What is the speed of light?', 'answer': '299,792,458 m/s', 'type': 'numerical'}])
                }
            ]
        }
    
    def load_examples(self, examples_path: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Load examples from file or use defaults.
        
        Args:
            examples_path: Optional path to examples file
            
        Returns:
            List of example dictionaries
        """
        if examples_path:
            path = Path(examples_path)
            if path.exists():
                with open(path, 'r') as f:
                    examples = json.load(f)
                logger.info(f"Loaded {len(examples)} examples from {examples_path}")
                return examples[:self.num_shots]
            else:
                logger.warning(f"Examples file not found: {examples_path}")
        
        # Use default examples
        examples = self.default_examples.get(self.task_type, [])
        return examples[:self.num_shots]
    
    def get_prompt(self, context: str, **kwargs) -> str:
        """
        Get formatted few-shot prompt with multiple examples.
        
        Args:
            context: The main context/content
            **kwargs: Additional parameters
            
        Returns:
            Formatted few-shot prompt
        """
        # Load examples
        examples_path = self.config.get('examples_path')
        examples = self.load_examples(examples_path)
        
        # Format instruction
        instruction = self.format_prompt("", **kwargs).split('\n\n')[0]  # Get just the instruction part
        
        # Build few-shot prompt
        prompt_parts = [instruction, "\nExamples:"]
        
        for i, example in enumerate(examples, 1):
            prompt_parts.append(f"\nExample {i}:")
            prompt_parts.append(f"Input: {example['input']}")
            prompt_parts.append(f"Output: {example['output']}")
        
        prompt_parts.append("\nNow, apply the same approach to this input:")
        prompt_parts.append(f"Input: {context}")
        prompt_parts.append("Output:")
        
        return '\n'.join(prompt_parts)

