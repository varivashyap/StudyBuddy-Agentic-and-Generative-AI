"""LLM client for generating content using 100% open-source local models."""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from ..config import get_config

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for interacting with local LLM models.

    OPEN-SOURCE ONLY: Uses llama-cpp-python for local inference.
    Supports GGUF quantized models from Kaggle/HuggingFace.

    NO PAID APIS: OpenAI and Anthropic support removed.
    """

    def __init__(self):
        """Initialize local LLM client."""
        self.config = get_config()
        self.provider = self.config.llm.provider

        if self.provider != "local":
            logger.error(f"Only 'local' provider supported. Got: {self.provider}")
            logger.error("OpenAI and Anthropic have been removed (paid APIs)")
            raise ValueError("Only local LLM provider is supported. Set llm.provider='local' in config.yaml")

        self.client = None
        self.model_path = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the local LLM client using llama-cpp-python."""
        logger.info("Initializing local LLM client (llama-cpp-python)")

        # Get model configuration
        self.model_name = self.config.llm.local_model
        self.quantization = self.config.llm.local_quantization

        # Construct model path
        models_dir = Path("models")
        self.model_path = models_dir / f"{self.model_name}.gguf"

        if not self.model_path.exists():
            logger.error(f"Model not found: {self.model_path}")
            logger.error("Please download a GGUF model from Kaggle or HuggingFace")
            logger.error("Example: models/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}\n"
                f"Download GGUF models from:\n"
                f"  - Kaggle: https://www.kaggle.com/models\n"
                f"  - HuggingFace: https://huggingface.co/models?library=gguf\n"
                f"Place in: {models_dir}/"
            )

        # Load model with llama-cpp-python
        try:
            from llama_cpp import Llama

            # Determine device
            use_gpu = self.config.system.device == "cuda"
            n_gpu_layers = -1 if use_gpu else 0  # -1 = offload all layers to GPU

            logger.info(f"Loading model: {self.model_path}")
            logger.info(f"GPU acceleration: {use_gpu}")

            self.client = Llama(
                model_path=str(self.model_path),
                n_ctx=4096,  # Context window
                n_gpu_layers=n_gpu_layers,
                n_threads=self.config.system.max_workers,
                verbose=False
            )

            logger.info(f"✓ Local LLM loaded successfully: {self.model_name}")

        except ImportError:
            logger.error("llama-cpp-python not installed")
            logger.error("Install with: pip install llama-cpp-python")
            raise
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 500,
        **kwargs
    ) -> str:
        """
        Generate text using local LLM.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters (top_p, top_k, repeat_penalty, etc.)

        Returns:
            Generated text
        """
        return self._generate_local(prompt, system_prompt, temperature, max_tokens, **kwargs)

    def _generate_local(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """
        Generate using local LLM with llama-cpp-python.

        Supports various prompt formats (ChatML, Llama, Mistral, etc.)
        """
        # Format prompt based on model type
        formatted_prompt = self._format_prompt(prompt, system_prompt)

        # Extract generation parameters
        top_p = kwargs.get('top_p', 0.9)
        top_k = kwargs.get('top_k', 40)
        repeat_penalty = kwargs.get('repeat_penalty', 1.1)

        logger.debug(f"Generating with temp={temperature}, max_tokens={max_tokens}")

        try:
            # Generate using llama-cpp-python
            response = self.client(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=self._get_stop_tokens(),
                echo=False
            )

            # Extract generated text
            generated_text = response['choices'][0]['text'].strip()

            logger.debug(f"Generated {len(generated_text)} characters")
            return generated_text

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    def _format_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Format prompt for the specific model architecture.

        Supports:
        - Llama 2/3 format
        - Mistral/Mixtral format
        - ChatML format
        - Alpaca format
        """
        model_lower = self.model_name.lower()

        # Llama 2/3 format
        if 'llama-2' in model_lower or 'llama2' in model_lower:
            if system_prompt:
                return f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{prompt} [/INST]"
            else:
                return f"<s>[INST] {prompt} [/INST]"

        # Llama 3 format
        elif 'llama-3' in model_lower or 'llama3' in model_lower:
            if system_prompt:
                return f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
            else:
                return f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

        # Mistral/Mixtral format
        elif 'mistral' in model_lower or 'mixtral' in model_lower:
            if system_prompt:
                return f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
            else:
                return f"<s>[INST] {prompt} [/INST]"

        # ChatML format (default for many models)
        elif 'chatml' in model_lower or 'openchat' in model_lower:
            if system_prompt:
                return f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
            else:
                return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

        # Alpaca format
        elif 'alpaca' in model_lower:
            if system_prompt:
                return f"### Instruction:\n{system_prompt}\n\n### Input:\n{prompt}\n\n### Response:\n"
            else:
                return f"### Instruction:\n{prompt}\n\n### Response:\n"

        # Generic format (fallback)
        else:
            logger.warning(f"Unknown model format for {self.model_name}, using generic format")
            if system_prompt:
                return f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant:"
            else:
                return f"User: {prompt}\n\nAssistant:"

    def _get_stop_tokens(self) -> list:
        """Get stop tokens based on model type."""
        model_lower = self.model_name.lower()

        if 'llama-3' in model_lower or 'llama3' in model_lower:
            return ["<|eot_id|>", "<|end_of_text|>"]
        elif 'mistral' in model_lower or 'mixtral' in model_lower:
            return ["</s>", "[/INST]"]
        elif 'chatml' in model_lower or 'openchat' in model_lower:
            return ["<|im_end|>"]
        elif 'alpaca' in model_lower:
            return ["###"]
        else:
            return ["</s>", "\n\n\n"]

