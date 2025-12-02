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

        # Calculate safe max_tokens for 4GB GPU
        # Each MCQ needs ~150 tokens (question + 4 options + answer)
        # Cap at 1500 tokens total to prevent memory issues
        tokens_per_question = 150
        safe_max_tokens = min(tokens_per_question * num_questions, 1500)

        logger.info(f"Generating {num_questions} questions with max_tokens={safe_max_tokens}")

        # Generate
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=self.temperature,
            max_tokens=safe_max_tokens
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
        # Use simple text format instead of JSON - easier for small models
        if question_type == "mcq":
            prompt = f"""Create {num_questions} multiple choice questions from this text.

Text:
{context}

Format each question like this:

Q1: [question text]
A) [first option]
B) [second option]
C) [third option]
D) [fourth option]
ANSWER: [A/B/C/D]
EXPLANATION: [why this is correct]

Q2: [next question]
...

Generate {num_questions} questions now:

"""
        else:
            # Fallback for other types
            prompt = f"""Generate {num_questions} {question_type} questions from this content.

Content:
{context}

Return valid JSON array only:
["""

        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for quiz generation."""
        return """You are an expert quiz generator. Create high-quality assessment questions.

CRITICAL RULES:
1. Output ONLY valid JSON - no explanatory text before or after
2. Base questions strictly on the provided content
3. Make questions clear and unambiguous
4. For MCQs, create plausible distractors
5. Ensure correct answers are factually accurate
6. Use proper JSON formatting with double quotes
7. No trailing commas in JSON objects"""
    
    def _parse_questions(self, response: str, question_type: str) -> List[Dict[str, any]]:
        """Parse questions from LLM response with robust error handling."""

        # Try text format first (more reliable for small models)
        if question_type == "mcq":
            text_questions = self._parse_text_format(response)
            if text_questions:
                logger.info(f"Successfully parsed {len(text_questions)} questions from text format")
                for q in text_questions:
                    q['type'] = question_type
                return text_questions

        # Fallback to JSON parsing
        try:
            # Extract JSON array
            start = response.find('[')
            end = response.rfind(']') + 1

            if start >= 0 and end > start:
                json_str = response[start:end]

                # Log the raw JSON for debugging
                logger.debug(f"Raw JSON (first 500 chars): {json_str[:500]}")

                # Try to fix common JSON issues
                json_str = self._fix_json_issues(json_str)

                questions = json.loads(json_str)

                # Validate and add type to each question
                valid_questions = []
                for q in questions:
                    if self._validate_question(q, question_type):
                        q['type'] = question_type
                        valid_questions.append(q)
                    else:
                        logger.warning(f"Skipping invalid question: {q}")

                return valid_questions
            else:
                logger.warning("No JSON array found in response")
                logger.debug(f"Response: {response[:500]}...")
                return []

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse questions: {e}")
            # Log the problematic JSON for debugging
            if 'json_str' in locals():
                logger.error(f"Problematic JSON: {json_str}")
                # Try to save it to a file for inspection
                try:
                    with open('/tmp/failed_quiz_json.txt', 'w') as f:
                        f.write(json_str)
                    logger.error("Saved failed JSON to /tmp/failed_quiz_json.txt")
                except:
                    pass
            return []

    def _parse_text_format(self, response: str) -> List[Dict[str, any]]:
        """Parse questions from simple text format (more reliable than JSON)."""
        import re

        questions = []

        # Split by question markers (Q1:, Q2:, etc.)
        question_blocks = re.split(r'Q\d+:', response)[1:]  # Skip first empty split

        for block in question_blocks:
            try:
                # Extract question text (everything before first option)
                question_match = re.search(r'^([^\n]+)', block.strip())
                if not question_match:
                    continue
                question_text = question_match.group(1).strip()

                # Extract options (A), B), C), D))
                options = []
                for letter in ['A', 'B', 'C', 'D']:
                    option_match = re.search(rf'{letter}\)([^\n]+)', block)
                    if option_match:
                        options.append(f"{letter}) {option_match.group(1).strip()}")

                if len(options) < 2:
                    logger.warning(f"Skipping question with insufficient options: {question_text[:50]}")
                    continue

                # Extract answer
                answer_match = re.search(r'ANSWER:\s*([A-D])', block, re.IGNORECASE)
                correct_answer = answer_match.group(1).upper() if answer_match else options[0][0]

                # Extract explanation
                explanation_match = re.search(r'EXPLANATION:\s*(.+?)(?=Q\d+:|$)', block, re.DOTALL | re.IGNORECASE)
                explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided"

                # Clean up explanation (remove extra whitespace)
                explanation = re.sub(r'\s+', ' ', explanation)

                questions.append({
                    'question': question_text,
                    'options': options,
                    'correct_answer': correct_answer,
                    'explanation': explanation
                })

            except Exception as e:
                logger.warning(f"Failed to parse question block: {e}")
                continue

        return questions

    def _fix_json_issues(self, json_str: str) -> str:
        """Fix common JSON formatting issues from LLM output."""
        import re

        # Remove trailing commas before closing brackets/braces
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)

        # Fix single quotes to double quotes (common LLM mistake)
        # Be careful with apostrophes in text
        json_str = json_str.replace("'", '"')

        # Fix common escape issues
        json_str = json_str.replace('\n', ' ')  # Remove newlines in strings
        json_str = json_str.replace('\r', ' ')
        json_str = json_str.replace('\t', ' ')

        # Fix multiple spaces
        json_str = re.sub(r'\s+', ' ', json_str)

        # Fix missing commas between objects (common LLM error)
        json_str = re.sub(r'}\s*{', '},{', json_str)

        # Fix unescaped quotes in strings (very tricky - this is a simple heuristic)
        # Replace \" with ' inside string values to avoid breaking JSON
        json_str = re.sub(r':\s*"([^"]*)"([^"]*)"([^"]*)"', r': "\1\'\2\'\3"', json_str)

        return json_str

    def _validate_question(self, question: Dict, question_type: str) -> bool:
        """Validate that a question has required fields."""
        if question_type == "mcq":
            required = ['question', 'options', 'correct_answer']
            if not all(field in question for field in required):
                return False
            if not isinstance(question.get('options'), list):
                return False
            if len(question.get('options', [])) < 2:
                return False
            return True
        elif question_type == "short_answer":
            return 'question' in question and 'answer' in question
        elif question_type == "numerical":
            return 'question' in question and 'answer' in question
        return 'question' in question
    
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

