"""Summary generation module."""

import logging
from typing import List, Dict, Tuple

from .llm_client import LLMClient
from ..config import get_config

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """Generate multi-scale summaries from context."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize summary generator.
        
        Args:
            llm_client: LLM client instance
        """
        self.llm = llm_client
        self.config = get_config()
        self.temperature = self.config.generation.summary_temperature
        self.max_tokens = self.config.generation.summary_max_tokens
        self.scales = self.config.get("generation.summaries.scales", ["sentence", "paragraph", "section"])
    
    def generate(
        self,
        context: List[Tuple[Dict, float]],
        scale: str = "paragraph"
    ) -> str:
        """
        Generate summary from retrieved context.
        
        Args:
            context: List of (document, score) tuples from retrieval
            scale: Summary scale ("sentence", "paragraph", or "section")
            
        Returns:
            Generated summary
        """
        if scale not in self.scales:
            logger.warning(f"Unknown scale {scale}, using 'paragraph'")
            scale = "paragraph"
        
        # Combine context
        context_text = self._format_context(context)
        
        # Create prompt
        prompt = self._create_prompt(context_text, scale)
        system_prompt = self._get_system_prompt()
        
        # Generate
        summary = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        logger.info(f"Generated {scale} summary ({len(summary)} chars)")
        return summary.strip()
    
    def generate_multi_scale(
        self,
        context: List[Tuple[Dict, float]]
    ) -> Dict[str, str]:
        """
        Generate summaries at all scales.
        
        Args:
            context: List of (document, score) tuples
            
        Returns:
            Dict mapping scale to summary
        """
        summaries = {}
        
        for scale in self.scales:
            summaries[scale] = self.generate(context, scale)
        
        return summaries
    
    def _format_context(self, context: List[Tuple[Dict, float]]) -> str:
        """Format context documents into a single string."""
        context_parts = []
        
        for i, (doc, score) in enumerate(context, 1):
            text = doc.get('text', '')
            context_parts.append(f"[{i}] {text}")
        
        return "\n\n".join(context_parts)
    
    def _create_prompt(self, context: str, scale: str) -> str:
        """Create prompt for summary generation."""
        scale_instructions = {
            "sentence": "Create a single-sentence summary that captures the main point.",
            "paragraph": "Create a concise paragraph (3-5 sentences) summarizing the key information.",
            "section": "Create a comprehensive summary (1-2 paragraphs) covering all important details."
        }
        
        instruction = scale_instructions.get(scale, scale_instructions["paragraph"])
        
        prompt = f"""Based on the following context, generate a summary.

{instruction}

Context:
{context}

Summary:"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for summary generation."""
        return """You are an expert at creating accurate, factual summaries from source material.

Rules:
1. Only include information explicitly stated in the context
2. Do not add external knowledge or assumptions
3. Be concise and clear
4. Maintain factual accuracy
5. Use objective language"""

