"""Flashcard generation module."""

import logging
from typing import List, Dict, Tuple, Optional
import json

from .llm_client import LLMClient
from ..config import get_config

logger = logging.getLogger(__name__)


class FlashcardGenerator:
    """Generate flashcards from context."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize flashcard generator.
        
        Args:
            llm_client: LLM client instance
        """
        self.llm = llm_client
        self.config = get_config()
        self.temperature = self.config.generation.flashcard_temperature
        self.max_tokens = self.config.generation.flashcard_max_tokens
        self.max_cards = self.config.generation.flashcard_max_cards
        self.min_similarity = self.config.generation.flashcard_min_similarity
        self.card_types = self.config.get("generation.flashcards.types", ["definition", "concept", "cloze"])
    
    def generate(
        self,
        context: List[Tuple[Dict, float]],
        card_type: str = "definition",
        max_cards: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Generate flashcards from context.
        
        Args:
            context: List of (document, score) tuples
            card_type: Type of flashcard ("definition", "concept", "cloze")
            max_cards: Maximum number of cards (uses config default if None)
            
        Returns:
            List of flashcard dicts with 'front', 'back', and 'type' keys
        """
        if max_cards is None:
            max_cards = self.max_cards
        
        # Format context
        context_text = self._format_context(context)
        
        # Create prompt
        prompt = self._create_prompt(context_text, card_type, max_cards)
        system_prompt = self._get_system_prompt()
        
        # Generate
        actual_max_tokens = self.max_tokens * 3  # Allow for multiple cards
        logger.info(f"Generating flashcards with max_tokens={actual_max_tokens}")
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=self.temperature,
            max_tokens=actual_max_tokens
        )
        logger.debug(f"LLM response length: {len(response)} chars")
        
        # Parse flashcards
        flashcards = self._parse_flashcards(response, card_type)
        
        # Validate flashcards
        flashcards = self._validate_flashcards(flashcards, context)
        
        logger.info(f"Generated {len(flashcards)} {card_type} flashcards")
        return flashcards[:max_cards]
    
    def generate_all_types(
        self,
        context: List[Tuple[Dict, float]],
        max_cards_per_type: Optional[int] = None
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Generate flashcards of all types.
        
        Args:
            context: List of (document, score) tuples
            max_cards_per_type: Max cards per type
            
        Returns:
            Dict mapping card type to list of flashcards
        """
        all_flashcards = {}
        
        for card_type in self.card_types:
            flashcards = self.generate(context, card_type, max_cards_per_type)
            all_flashcards[card_type] = flashcards
        
        return all_flashcards
    
    def _format_context(self, context: List[Tuple[Dict, float]]) -> str:
        """Format context documents."""
        context_parts = []
        
        for doc, _ in context:
            text = doc.get('text', '')
            context_parts.append(text)
        
        return "\n\n".join(context_parts)
    
    def _create_prompt(self, context: str, card_type: str, max_cards: int) -> str:
        """Create prompt for flashcard generation."""
        type_instructions = {
            "definition": """Generate definition flashcards where:
- Front: A term or concept
- Back: Clear, concise definition""",

            "concept": """Generate concept flashcards where:
- Front: A question about a concept
- Back: Explanation or answer""",

            "cloze": """Generate cloze deletion flashcards where:
- Front: A statement with {{c1::hidden text}}
- Back: The complete statement"""
        }

        instruction = type_instructions.get(card_type, type_instructions["definition"])

        prompt = f"""Based on the following content, generate exactly {max_cards} flashcards for studying.

{instruction}

IMPORTANT: You MUST respond with ONLY a valid JSON array. Do not include any explanatory text before or after the JSON.

Example format:
[
  {{"front": "What is photosynthesis?", "back": "The process by which plants convert light energy into chemical energy"}},
  {{"front": "What is the powerhouse of the cell?", "back": "Mitochondria"}}
]

Content:
{context}

Now generate {max_cards} flashcards in JSON format (respond with ONLY the JSON array, nothing else):"""

        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for flashcard generation."""
        return """You are an expert at creating effective study flashcards.

Rules:
1. Extract only factual information from the source
2. Make cards clear and unambiguous
3. Keep answers concise
4. Focus on important concepts
5. Ensure each card tests one specific piece of knowledge
6. Return valid JSON only"""
    
    def _parse_flashcards(self, response: str, card_type: str) -> List[Dict[str, str]]:
        """Parse flashcards from LLM response."""
        try:
            # Debug: Log the raw response
            logger.debug(f"Raw LLM response length: {len(response)} chars")
            logger.debug(f"Raw LLM response (first 500 chars): {response[:500]}")

            # Try to extract JSON from response
            # Look for JSON array
            start = response.find('[')
            end = response.rfind(']') + 1

            # If no closing bracket found, try to fix incomplete JSON
            if start >= 0 and end == 0:
                logger.warning("Incomplete JSON detected - attempting to fix")
                # Try to complete the JSON by adding closing bracket
                json_str = response[start:].strip()
                # Remove any incomplete last item
                last_brace = json_str.rfind('}')
                if last_brace > 0:
                    json_str = json_str[:last_brace+1]
                    # Add closing bracket
                    if not json_str.endswith(']'):
                        json_str += '\n]'
                end = len(json_str)
            elif start >= 0 and end > start:
                json_str = response[start:end]
            else:
                logger.warning("No JSON array found in response")
                logger.warning(f"Response preview: {response[:300]}")
                return []

            logger.debug(f"Extracted JSON string length: {len(json_str)} chars")
            flashcards = json.loads(json_str)

            # Add type to each card
            for card in flashcards:
                card['type'] = card_type

            logger.info(f"Successfully parsed {len(flashcards)} flashcards")
            return flashcards

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse flashcards: {e}")
            logger.error(f"JSON string that failed: {json_str[:200] if 'json_str' in locals() else 'N/A'}")
            return []
    
    def _validate_flashcards(
        self,
        flashcards: List[Dict[str, str]],
        context: List[Tuple[Dict, float]]
    ) -> List[Dict[str, str]]:
        """
        Validate flashcards against source content.
        
        NOTE: This is a stub. Full implementation requires:
        - Embedding-based similarity check
        - Verify answers appear in source (similarity > threshold)
        - Filter out hallucinated content
        
        Args:
            flashcards: List of flashcard dicts
            context: Original context
            
        Returns:
            Validated flashcards
        """
        # STUB: Implement validation
        # For now, just return all flashcards
        logger.warning("Flashcard validation not fully implemented")
        return flashcards

