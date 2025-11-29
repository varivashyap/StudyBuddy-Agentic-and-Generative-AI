"""Quiz generation module."""

import logging
from typing import List, Dict, Tuple, Optional
import json

from .llm_client import LLMClient
from ..config import get_config

logger = logging.getLogger(__name__)


class QuizGenerator:
    """Generate quiz questions from context."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize quiz generator.
        
        Args:
            llm_client: LLM client instance
        """
        self.llm = llm_client
        self.config = get_config()
        self.temperature = self.config.generation.quiz_temperature
        self.max_tokens = self.config.generation.quiz_max_tokens
        self.question_types = self.config.get("generation.quizzes.types", ["mcq", "short_answer", "numerical"])
        self.difficulty_dist = self.config.get("generation.quizzes.difficulty_distribution", {
            "easy": 0.4,
            "medium": 0.3,
            "hard": 0.3
        })
    
    def generate(
        self,
        context: List[Tuple[Dict, float]],
        question_type: str = "mcq",
        num_questions: int = 10,
        difficulty: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """
        Generate quiz questions from context.
        
        Args:
            context: List of (document, score) tuples
            question_type: Type of question ("mcq", "short_answer", "numerical")
            num_questions: Number of questions to generate
            difficulty: Difficulty level ("easy", "medium", "hard") or None for mixed
            
        Returns:
            List of question dicts
        """
        # Format context
        context_text = self._format_context(context)
        
        # Create prompt
        prompt = self._create_prompt(context_text, question_type, num_questions, difficulty)
        system_prompt = self._get_system_prompt()
        
        # Generate
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens * num_questions
        )
        
        # Parse questions
        questions = self._parse_questions(response, question_type)
        
        # Tag difficulty if not specified
        if difficulty is None:
            questions = self._tag_difficulty(questions)
        else:
            for q in questions:
                q['difficulty'] = difficulty
        
        logger.info(f"Generated {len(questions)} {question_type} questions")
        return questions[:num_questions]
    
    def generate_mixed(
        self,
        context: List[Tuple[Dict, float]],
        total_questions: int = 20
    ) -> List[Dict[str, any]]:
        """
        Generate a mixed quiz with different question types and difficulties.
        
        Args:
            context: List of (document, score) tuples
            total_questions: Total number of questions
            
        Returns:
            List of mixed question dicts
        """
        all_questions = []
        
        # Distribute questions across types
        questions_per_type = total_questions // len(self.question_types)
        
        for qtype in self.question_types:
            questions = self.generate(context, qtype, questions_per_type)
            all_questions.extend(questions)
        
        # Balance difficulty distribution
        all_questions = self._balance_difficulty(all_questions)
        
        return all_questions[:total_questions]
    
    def _format_context(self, context: List[Tuple[Dict, float]]) -> str:
        """Format context documents."""
        context_parts = []
        
        for doc, _ in context:
            text = doc.get('text', '')
            context_parts.append(text)
        
        return "\n\n".join(context_parts)
    
    def _create_prompt(
        self,
        context: str,
        question_type: str,
        num_questions: int,
        difficulty: Optional[str]
    ) -> str:
        """Create prompt for quiz generation."""
        type_instructions = {
            "mcq": """Generate multiple-choice questions with:
- question: The question text
- options: List of 4 options (A, B, C, D)
- correct_answer: The correct option letter
- explanation: Brief explanation of the answer""",
            
            "short_answer": """Generate short-answer questions with:
- question: The question text
- answer: The expected answer (1-2 sentences)
- keywords: Key terms that should appear in the answer""",
            
            "numerical": """Generate numerical questions with:
- question: The question text
- answer: The numerical answer
- unit: The unit of measurement (if applicable)
- tolerance: Acceptable margin of error"""
        }
        
        instruction = type_instructions.get(question_type, type_instructions["mcq"])
        difficulty_note = f"\nDifficulty level: {difficulty}" if difficulty else "\nMix of easy, medium, and hard questions"
        
        prompt = f"""Based on the following content, generate {num_questions} {question_type} questions.

{instruction}{difficulty_note}

Return the questions in JSON format as a list.

Content:
{context}

Questions (JSON):"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for quiz generation."""
        return """You are an expert at creating effective assessment questions.

Rules:
1. Base questions only on the provided content
2. Make questions clear and unambiguous
3. For MCQs, create plausible distractors
4. Ensure correct answers are factually accurate
5. Vary difficulty appropriately
6. Return valid JSON only"""
    
    def _parse_questions(self, response: str, question_type: str) -> List[Dict[str, any]]:
        """Parse questions from LLM response."""
        try:
            # Extract JSON array
            start = response.find('[')
            end = response.rfind(']') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                questions = json.loads(json_str)
                
                # Add type to each question
                for q in questions:
                    q['type'] = question_type
                
                return questions
            else:
                logger.warning("No JSON array found in response")
                return []
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse questions: {e}")
            return []
    
    def _tag_difficulty(self, questions: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Tag questions with difficulty level.
        
        NOTE: This is a stub. Full implementation requires:
        - Difficulty classifier model (e.g., distilbert-base)
        - Training on labeled difficulty data
        - Feature extraction (question complexity, answer length, etc.)
        
        For now, assigns difficulty randomly based on distribution.
        """
        import random
        
        # STUB: Use simple random assignment based on distribution
        difficulties = []
        for diff, ratio in self.difficulty_dist.items():
            count = int(len(questions) * ratio)
            difficulties.extend([diff] * count)
        
        # Fill remaining
        while len(difficulties) < len(questions):
            difficulties.append("medium")
        
        random.shuffle(difficulties)
        
        for i, q in enumerate(questions):
            q['difficulty'] = difficulties[i] if i < len(difficulties) else "medium"
        
        logger.warning("Using random difficulty assignment (classifier not implemented)")
        return questions
    
    def _balance_difficulty(self, questions: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Balance questions according to difficulty distribution."""
        # Group by difficulty
        by_difficulty = {"easy": [], "medium": [], "hard": []}
        
        for q in questions:
            diff = q.get('difficulty', 'medium')
            if diff in by_difficulty:
                by_difficulty[diff].append(q)
        
        # Select according to distribution
        balanced = []
        total = len(questions)
        
        for diff, ratio in self.difficulty_dist.items():
            count = int(total * ratio)
            balanced.extend(by_difficulty[diff][:count])
        
        return balanced

