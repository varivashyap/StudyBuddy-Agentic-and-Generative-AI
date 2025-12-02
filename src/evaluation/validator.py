"""Content validation for generated outputs."""

import logging
from typing import List, Dict, Tuple
import numpy as np

from ..config import get_config

logger = logging.getLogger(__name__)


class ContentValidator:
    """Validate generated content against source material."""
    
    def __init__(self, embedding_model=None):
        """
        Initialize content validator.
        
        Args:
            embedding_model: Embedding model for similarity checks (optional)
        """
        self.config = get_config()
        self.embedding_model = embedding_model
        self.min_source_containment = self.config.get("evaluation.automated_checks.min_source_containment", 0.75)
        self.max_hallucination_rate = self.config.get("evaluation.automated_checks.max_hallucination_rate", 0.1)
    
    def validate_summary(
        self,
        summary: str,
        context: List[Tuple[Dict, float]]
    ) -> Dict[str, any]:
        """
        Validate a summary against source context.
        
        Args:
            summary: Generated summary
            context: Source context documents
            
        Returns:
            Validation results dict
        """
        context_text = self._extract_context_text(context)
        
        # Check source containment
        containment_score = self._check_source_containment(summary, context_text)
        
        # Check for potential hallucinations
        hallucination_score = self._check_hallucinations(summary, context_text)
        
        is_valid = (
            containment_score >= self.min_source_containment and
            hallucination_score <= self.max_hallucination_rate
        )
        
        return {
            "is_valid": is_valid,
            "source_containment": containment_score,
            "hallucination_score": hallucination_score,
            "warnings": self._generate_warnings(containment_score, hallucination_score)
        }
    
    def validate_flashcard(
        self,
        flashcard: Dict[str, str],
        context: List[Tuple[Dict, float]]
    ) -> Dict[str, any]:
        """
        Validate a flashcard against source context.
        
        Args:
            flashcard: Flashcard dict with 'front' and 'back'
            context: Source context documents
            
        Returns:
            Validation results dict
        """
        context_text = self._extract_context_text(context)
        
        # Check if answer appears in source
        answer = flashcard.get('back', '')
        containment_score = self._check_source_containment(answer, context_text)
        
        is_valid = containment_score >= self.min_source_containment
        
        return {
            "is_valid": is_valid,
            "source_containment": containment_score,
            "warnings": [] if is_valid else ["Answer may not be supported by source material"]
        }
    
    def _extract_context_text(self, context: List[Tuple[Dict, float]]) -> str:
        """Extract text from context documents."""
        texts = [doc.get('text', '') for doc, _ in context]
        return " ".join(texts)
    
    def _check_source_containment(self, generated: str, source: str) -> float:
        """
        Check how much of the generated content is contained in source.
        
        NOTE: This is a simplified implementation using word overlap.
        Full implementation should use:
        - Embedding-based semantic similarity
        - Sentence-level alignment
        - Factual consistency checking
        
        Args:
            generated: Generated text
            source: Source text
            
        Returns:
            Containment score (0-1)
        """
        if not generated or not source:
            return 0.0
        
        # Simple word-based overlap
        gen_words = set(generated.lower().split())
        source_words = set(source.lower().split())
        
        if not gen_words:
            return 0.0
        
        overlap = len(gen_words & source_words)
        containment = overlap / len(gen_words)
        
        logger.debug(f"Source containment: {containment:.2f}")
        return containment
    
    def _check_hallucinations(self, generated: str, source: str) -> float:
        """
        Estimate hallucination rate in generated content.
        
        NOTE: This is a stub. Full implementation requires:
        - NLI (Natural Language Inference) model
        - Fact extraction and verification
        - Contradiction detection
        
        Args:
            generated: Generated text
            source: Source text
            
        Returns:
            Estimated hallucination rate (0-1)
        """
        # STUB: Simple inverse of containment as proxy
        containment = self._check_source_containment(generated, source)
        hallucination_estimate = 1.0 - containment
        
        logger.warning("Using simplified hallucination detection")
        return hallucination_estimate
    
    def _generate_warnings(self, containment: float, hallucination: float) -> List[str]:
        """Generate warning messages based on scores."""
        warnings = []
        
        if containment < self.min_source_containment:
            warnings.append(f"Low source containment ({containment:.2f} < {self.min_source_containment})")
        
        if hallucination > self.max_hallucination_rate:
            warnings.append(f"High hallucination risk ({hallucination:.2f} > {self.max_hallucination_rate})")
        
        return warnings

