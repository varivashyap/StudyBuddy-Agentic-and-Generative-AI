"""CSV exporter for flashcards and quizzes."""

import logging
from pathlib import Path
from typing import List, Dict
import csv

from ..config import get_config

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export content to CSV format."""
    
    def __init__(self):
        """Initialize CSV exporter."""
        self.config = get_config()
        self.delimiter = self.config.get("export.csv.delimiter", ",")
        self.include_metadata = self.config.get("export.csv.include_metadata", True)
    
    def export_flashcards(
        self,
        flashcards: List[Dict[str, str]],
        output_path: str
    ):
        """
        Export flashcards to CSV.
        
        Args:
            flashcards: List of flashcard dicts
            output_path: Path to save CSV file
        """
        if not flashcards:
            logger.warning("No flashcards to export")
            return
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine fields
        if self.include_metadata:
            fieldnames = ['type', 'front', 'back']
        else:
            fieldnames = ['front', 'back']
        
        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=self.delimiter)
            writer.writeheader()
            
            for card in flashcards:
                row = {}
                if self.include_metadata:
                    row['type'] = card.get('type', 'unknown')
                row['front'] = card.get('front', '')
                row['back'] = card.get('back', '')
                
                writer.writerow(row)
        
        logger.info(f"Exported {len(flashcards)} flashcards to {output_path}")
    
    def export_quizzes(
        self,
        questions: List[Dict[str, any]],
        output_path: str
    ):
        """
        Export quiz questions to CSV.
        
        Args:
            questions: List of question dicts
            output_path: Path to save CSV file
        """
        if not questions:
            logger.warning("No questions to export")
            return
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine fields based on question types
        fieldnames = ['type', 'difficulty', 'question', 'answer']
        
        # Add type-specific fields
        has_mcq = any(q.get('type') == 'mcq' for q in questions)
        if has_mcq:
            fieldnames.extend(['option_a', 'option_b', 'option_c', 'option_d', 'correct_option'])
        
        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=self.delimiter, extrasaction='ignore')
            writer.writeheader()
            
            for q in questions:
                row = {
                    'type': q.get('type', 'unknown'),
                    'difficulty': q.get('difficulty', 'medium'),
                    'question': q.get('question', ''),
                    'answer': self._format_answer(q)
                }
                
                # Add MCQ options if applicable
                if q.get('type') == 'mcq' and 'options' in q:
                    options = q['options']
                    for i, opt in enumerate(options[:4]):
                        row[f'option_{chr(97+i)}'] = opt  # a, b, c, d
                    row['correct_option'] = q.get('correct_answer', '')
                
                writer.writerow(row)
        
        logger.info(f"Exported {len(questions)} questions to {output_path}")
    
    def export_summaries(
        self,
        summaries: Dict[str, str],
        output_path: str
    ):
        """
        Export summaries to CSV.
        
        Args:
            summaries: Dict mapping scale to summary text
            output_path: Path to save CSV file
        """
        if not summaries:
            logger.warning("No summaries to export")
            return
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['scale', 'summary'], delimiter=self.delimiter)
            writer.writeheader()
            
            for scale, summary in summaries.items():
                writer.writerow({
                    'scale': scale,
                    'summary': summary
                })
        
        logger.info(f"Exported {len(summaries)} summaries to {output_path}")
    
    def _format_answer(self, question: Dict[str, any]) -> str:
        """Format answer based on question type."""
        qtype = question.get('type', 'unknown')
        
        if qtype == 'mcq':
            return question.get('correct_answer', '')
        elif qtype == 'numerical':
            answer = question.get('answer', '')
            unit = question.get('unit', '')
            return f"{answer} {unit}".strip()
        else:
            return str(question.get('answer', ''))

