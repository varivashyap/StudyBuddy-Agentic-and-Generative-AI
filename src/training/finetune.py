"""
Finetuning module for local LLMs.

Supports supervised finetuning (SFT) on:
- Summaries: (chunk → gold_summary)
- Flashcards: (chunk → gold_flashcards)
- Quizzes: (chunk → gold_questions)

Uses LoRA/QLoRA for efficient 4GB GPU training.
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import torch
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for finetuning."""
    model_name: str
    output_dir: str
    learning_rate: float = 2e-4
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    max_seq_length: int = 2048
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    warmup_steps: int = 100
    logging_steps: int = 10
    save_steps: int = 100
    use_4bit: bool = True  # QLoRA for 4GB GPU
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class ModelFinetuner:
    """Finetune local LLMs using LoRA/QLoRA."""
    
    def __init__(self, config: TrainingConfig):
        """
        Initialize finetuner.
        
        Args:
            config: Training configuration
        """
        self.config = config
        self.model = None
        self.tokenizer = None
        
        logger.info(f"Initializing finetuner for {config.model_name}")
        logger.info(f"Device: {config.device}")
        logger.info(f"4-bit quantization: {config.use_4bit}")
    
    def load_model(self):
        """Load model with LoRA/QLoRA for efficient training."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
            
            logger.info(f"Loading model: {self.config.model_name}")
            
            # Configure 4-bit quantization for 4GB GPU
            if self.config.use_4bit:
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                )
                logger.info("Using 4-bit quantization (QLoRA) for 4GB GPU")
            else:
                bnb_config = None
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                quantization_config=bnb_config,
                device_map="auto" if self.config.device == "cuda" else None,
                trust_remote_code=True,
            )
            
            # Prepare for k-bit training
            if self.config.use_4bit:
                self.model = prepare_model_for_kbit_training(self.model)
            
            # Configure LoRA
            lora_config = LoraConfig(
                r=self.config.lora_r,
                lora_alpha=self.config.lora_alpha,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                lora_dropout=self.config.lora_dropout,
                bias="none",
                task_type="CAUSAL_LM",
            )
            
            # Apply LoRA
            self.model = get_peft_model(self.model, lora_config)
            self.model.print_trainable_parameters()
            
            logger.info("✓ Model loaded successfully with LoRA")
            
        except ImportError as e:
            logger.error(f"Missing dependencies: {e}")
            logger.error("Install with: pip install transformers peft bitsandbytes accelerate")
            raise
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def load_training_data(self, data_dir: str, task_type: str) -> List[Dict]:
        """
        Load training data from JSON files.
        
        Args:
            data_dir: Directory containing training data
            task_type: Type of task (summaries, flashcards, quizzes)
            
        Returns:
            List of training examples
        """
        data_path = Path(data_dir) / f"{task_type}.json"
        
        if not data_path.exists():
            logger.warning(f"Training data not found: {data_path}")
            return []
        
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data)} training examples from {data_path}")
        return data

    def prepare_dataset(self, examples: List[Dict], task_type: str):
        """
        Prepare dataset for training.

        Args:
            examples: List of training examples
            task_type: Type of task (summaries, flashcards, quizzes)

        Returns:
            Prepared dataset
        """
        from datasets import Dataset

        formatted_examples = []

        for example in examples:
            # Format based on task type
            if task_type == "summaries":
                prompt = f"Summarize the following text:\n\n{example['chunk']}\n\nSummary:"
                completion = example['gold_summary']
            elif task_type == "flashcards":
                prompt = f"Generate flashcards from the following text:\n\n{example['chunk']}\n\nFlashcards:"
                completion = json.dumps(example['gold_flashcards'])
            elif task_type == "quizzes":
                prompt = f"Generate quiz questions from the following text:\n\n{example['chunk']}\n\nQuestions:"
                completion = json.dumps(example['gold_questions'])
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            # Create training text
            text = f"{prompt} {completion}{self.tokenizer.eos_token}"
            formatted_examples.append({"text": text})

        dataset = Dataset.from_list(formatted_examples)
        logger.info(f"Prepared dataset with {len(dataset)} examples")

        return dataset

    def train(self, train_dataset, eval_dataset=None):
        """
        Train the model.

        Args:
            train_dataset: Training dataset
            eval_dataset: Optional evaluation dataset
        """
        from transformers import Trainer, TrainingArguments, DataCollatorForLanguageModeling

        # Training arguments optimized for 4GB GPU
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            fp16=True if self.config.device == "cuda" else False,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            warmup_steps=self.config.warmup_steps,
            save_total_limit=3,
            load_best_model_at_end=True if eval_dataset else False,
            evaluation_strategy="steps" if eval_dataset else "no",
            eval_steps=self.config.save_steps if eval_dataset else None,
            gradient_checkpointing=True,  # Save memory
            optim="paged_adamw_8bit" if self.config.use_4bit else "adamw_torch",
            max_grad_norm=0.3,
            report_to="none",  # Disable wandb/tensorboard
        )

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )

        # Tokenize datasets
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=self.config.max_seq_length,
                padding="max_length",
            )

        train_dataset = train_dataset.map(tokenize_function, batched=True)
        if eval_dataset:
            eval_dataset = eval_dataset.map(tokenize_function, batched=True)

        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
        )

        # Train
        logger.info("Starting training...")
        trainer.train()

        # Save final model
        logger.info(f"Saving model to {self.config.output_dir}")
        trainer.save_model()
        self.tokenizer.save_pretrained(self.config.output_dir)

        logger.info("✓ Training completed successfully")

    def finetune_on_task(self, data_dir: str, task_type: str, eval_split: float = 0.1):
        """
        Complete finetuning pipeline for a specific task.

        Args:
            data_dir: Directory containing training data
            task_type: Type of task (summaries, flashcards, quizzes)
            eval_split: Fraction of data to use for evaluation
        """
        # Load model
        if self.model is None:
            self.load_model()

        # Load training data
        examples = self.load_training_data(data_dir, task_type)
        if not examples:
            logger.error(f"No training data found for {task_type}")
            return

        # Prepare dataset
        dataset = self.prepare_dataset(examples, task_type)

        # Split into train/eval
        if eval_split > 0:
            split_dataset = dataset.train_test_split(test_size=eval_split, seed=42)
            train_dataset = split_dataset['train']
            eval_dataset = split_dataset['test']
        else:
            train_dataset = dataset
            eval_dataset = None

        # Train
        self.train(train_dataset, eval_dataset)

        logger.info(f"✓ Finetuning completed for {task_type}")
        logger.info(f"Model saved to: {self.config.output_dir}")

