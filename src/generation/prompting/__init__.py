"""Prompting strategies for LLM generation."""

from .base_prompt import BasePrompt
from .system_prompt import SystemPrompt
from .one_shot import OneShotPrompt
from .few_shot import FewShotPrompt

__all__ = ['BasePrompt', 'SystemPrompt', 'OneShotPrompt', 'FewShotPrompt']

