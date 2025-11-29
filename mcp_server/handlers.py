"""
Request handlers for MCP server.
Modular design allows easy addition of new request types.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from src.pipeline import StudyAssistantPipeline
from mcp_server.session_manager import SessionManager, DocumentSession

logger = logging.getLogger(__name__)


class BaseRequestHandler(ABC):
    """Base class for request handlers."""
    
    @abstractmethod
    def handle(self, pipeline: StudyAssistantPipeline, parameters: Dict[str, Any]) -> Any:
        """Handle the request and return results."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this request type."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get description of this request type."""
        pass
    
    @abstractmethod
    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters for this request type."""
        pass


class SummaryRequestHandler(BaseRequestHandler):
    """Handler for summary generation requests."""
    
    def handle(self, pipeline: StudyAssistantPipeline, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary from ingested content."""
        query = parameters.get('query')
        scale = parameters.get('scale', 'paragraph')
        
        logger.info(f"Generating summary with scale={scale}")
        summary = pipeline.generate_summaries(query=query, scale=scale)
        
        return {
            'summary': summary,
            'scale': scale,
            'length': len(summary)
        }
    
    def get_name(self) -> str:
        return 'summary'
    
    def get_description(self) -> str:
        return 'Generate a summary of the document content'
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'query': None,
            'scale': 'paragraph'  # Options: sentence, paragraph, section
        }


class FlashcardsRequestHandler(BaseRequestHandler):
    """Handler for flashcard generation requests."""
    
    def handle(self, pipeline: StudyAssistantPipeline, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate flashcards from ingested content."""
        query = parameters.get('query')
        card_type = parameters.get('card_type', 'definition')
        max_cards = parameters.get('max_cards', 20)
        
        logger.info(f"Generating {max_cards} flashcards of type={card_type}")
        flashcards = pipeline.generate_flashcards(
            query=query,
            card_type=card_type,
            max_cards=max_cards
        )
        
        return {
            'flashcards': flashcards,
            'count': len(flashcards),
            'card_type': card_type
        }
    
    def get_name(self) -> str:
        return 'flashcards'
    
    def get_description(self) -> str:
        return 'Generate flashcards for studying'
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'query': None,
            'card_type': 'definition',  # Options: definition, concept, cloze
            'max_cards': 20
        }


class QuizRequestHandler(BaseRequestHandler):
    """Handler for quiz generation requests."""
    
    def handle(self, pipeline: StudyAssistantPipeline, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quiz questions from ingested content."""
        query = parameters.get('query')
        question_type = parameters.get('question_type', 'mcq')
        num_questions = parameters.get('num_questions', 10)
        
        logger.info(f"Generating {num_questions} questions of type={question_type}")
        questions = pipeline.generate_quizzes(
            query=query,
            question_type=question_type,
            num_questions=num_questions
        )
        
        return {
            'questions': questions,
            'count': len(questions),
            'question_type': question_type
        }
    
    def get_name(self) -> str:
        return 'quiz'
    
    def get_description(self) -> str:
        return 'Generate quiz questions for assessment'
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'query': None,
            'question_type': 'mcq',  # Options: mcq, short_answer, numerical
            'num_questions': 10
        }


class RequestHandler:
    """Main request handler that manages all request types."""

    def __init__(self, model_registry, session_manager: Optional[SessionManager] = None):
        """
        Initialize request handler with model registry and session manager.

        Args:
            model_registry: Registry of available models
            session_manager: Session manager for caching (optional, will create if None)
        """
        self.model_registry = model_registry
        self.session_manager = session_manager or SessionManager()
        self.handlers: Dict[str, BaseRequestHandler] = {}

        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register the default request handlers."""
        self.register_handler(SummaryRequestHandler())
        self.register_handler(FlashcardsRequestHandler())
        self.register_handler(QuizRequestHandler())

    def register_handler(self, handler: BaseRequestHandler):
        """Register a new request handler."""
        name = handler.get_name()
        self.handlers[name] = handler
        logger.info(f"Registered handler: {name}")

    def list_request_types(self) -> List[Dict[str, Any]]:
        """List all available request types."""
        return [
            {
                'name': handler.get_name(),
                'description': handler.get_description(),
                'default_parameters': handler.get_default_parameters()
            }
            for handler in self.handlers.values()
        ]

    def handle_request(
        self,
        file_id: str,
        filepath: str,
        request_type: str,
        model_name: str = 'default',
        parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Handle a request by processing the file and generating content.
        Uses session manager to cache processed documents and avoid redundant ASR/OCR.

        Args:
            file_id: Unique file identifier
            filepath: Path to the uploaded file
            request_type: Type of request (summary, flashcards, quiz)
            model_name: Name of the model to use
            parameters: Request-specific parameters

        Returns:
            Generated content
        """
        if request_type not in self.handlers:
            raise ValueError(f"Unknown request type: {request_type}. Available: {list(self.handlers.keys())}")

        # Get handler
        handler = self.handlers[request_type]

        # Merge with default parameters
        params = handler.get_default_parameters().copy()
        if parameters:
            params.update(parameters)

        # Get or create session (this handles caching)
        session = self.session_manager.get_or_create_session(file_id, filepath)

        # Process document if not already processed (ASR/OCR/embeddings)
        # This will be skipped if we have cached data
        self.session_manager.process_document(session)

        # Get the pipeline with processed data
        pipeline = session.get_pipeline()

        if pipeline is None:
            raise RuntimeError(f"Failed to get pipeline for session {file_id}")

        # Handle request using the cached pipeline
        result = handler.handle(pipeline, params)

        return result

