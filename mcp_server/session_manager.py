"""
Session manager for caching processed documents.
Prevents redundant ASR/OCR processing and stores embeddings for reuse.
"""

import logging
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

from src.pipeline import StudyAssistantPipeline

logger = logging.getLogger(__name__)


class DocumentSession:
    """Represents a processed document session with cached pipeline."""
    
    def __init__(self, file_id: str, filepath: str, file_hash: str):
        """
        Initialize document session.
        
        Args:
            file_id: Unique file identifier
            filepath: Path to the uploaded file
            file_hash: Hash of the file content
        """
        self.file_id = file_id
        self.filepath = filepath
        self.file_hash = file_hash
        self.pipeline = None
        self.processed = False
        self.cache_path = None
        self.created_at = datetime.utcnow()
        self.metadata = {}
    
    def is_processed(self) -> bool:
        """Check if document has been processed."""
        return self.processed
    
    def get_pipeline(self) -> StudyAssistantPipeline:
        """Get the pipeline instance for this session."""
        return self.pipeline


class SessionManager:
    """
    Manages document processing sessions and caching.
    Ensures each document is only processed once (ASR/OCR/embeddings).
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize session manager.
        
        Args:
            cache_dir: Directory for caching processed documents
        """
        self.sessions: Dict[str, DocumentSession] = {}
        
        # Set cache directory
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / 'data' / 'cache' / 'sessions'
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"SessionManager initialized with cache dir: {self.cache_dir}")
    
    def _compute_file_hash(self, filepath: str) -> str:
        """Compute SHA256 hash of file content."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _get_cache_path(self, file_hash: str) -> Path:
        """Get cache path for a file hash."""
        return self.cache_dir / file_hash
    
    def _save_session_metadata(self, session: DocumentSession):
        """Save session metadata to cache."""
        metadata_path = session.cache_path / 'metadata.json'
        metadata = {
            'file_id': session.file_id,
            'filepath': session.filepath,
            'file_hash': session.file_hash,
            'processed': session.processed,
            'created_at': session.created_at.isoformat(),
            'metadata': session.metadata
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _load_session_metadata(self, cache_path: Path) -> Dict[str, Any]:
        """Load session metadata from cache."""
        metadata_path = cache_path / 'metadata.json'
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return {}
    
    def get_or_create_session(self, file_id: str, filepath: str) -> DocumentSession:
        """
        Get existing session or create new one.
        
        Args:
            file_id: Unique file identifier
            filepath: Path to the uploaded file
            
        Returns:
            DocumentSession instance
        """
        # Check if session already exists in memory
        if file_id in self.sessions:
            logger.info(f"Reusing existing session for {file_id}")
            return self.sessions[file_id]
        
        # Compute file hash
        file_hash = self._compute_file_hash(filepath)
        cache_path = self._get_cache_path(file_hash)
        
        # Create session
        session = DocumentSession(file_id, filepath, file_hash)
        session.cache_path = cache_path
        
        # Check if we have cached data for this file hash
        if cache_path.exists() and (cache_path / 'index.faiss').exists():
            logger.info(f"Found cached data for {file_id} (hash: {file_hash[:8]}...)")
            
            # Load metadata
            metadata = self._load_session_metadata(cache_path)
            session.metadata = metadata.get('metadata', {})
            
            # Create pipeline and load cached index
            session.pipeline = StudyAssistantPipeline()
            session.pipeline.load_index(str(cache_path))
            session.processed = True
            
            logger.info(f"Loaded cached session for {file_id}")
        else:
            logger.info(f"No cache found for {file_id}, will process from scratch")
            session.pipeline = StudyAssistantPipeline()
            session.processed = False
        
        # Store in memory
        self.sessions[file_id] = session
        
        return session
    
    def process_document(self, session: DocumentSession) -> None:
        """
        Process document if not already processed.
        
        Args:
            session: DocumentSession to process
        """
        if session.processed:
            logger.info(f"Document {session.file_id} already processed, skipping")
            return
        
        logger.info(f"Processing document {session.file_id}")
        
        # Determine file type and ingest
        file_path = Path(session.filepath)
        
        if file_path.suffix.lower() == '.pdf':
            logger.info(f"Ingesting PDF: {session.filepath}")
            session.pipeline.ingest_pdf(session.filepath)
            session.metadata['file_type'] = 'pdf'
        elif file_path.suffix.lower() in ['.mp3', '.wav', '.m4a', '.mp4']:
            logger.info(f"Ingesting audio: {session.filepath}")
            session.pipeline.ingest_audio(session.filepath)
            session.metadata['file_type'] = 'audio'
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        # Save to cache
        session.cache_path.mkdir(parents=True, exist_ok=True)
        session.pipeline.save_index(str(session.cache_path))
        session.processed = True
        
        # Save metadata
        self._save_session_metadata(session)
        
        logger.info(f"Document {session.file_id} processed and cached")
    
    def clear_session(self, file_id: str):
        """Remove session from memory (cache remains on disk)."""
        if file_id in self.sessions:
            del self.sessions[file_id]
            logger.info(f"Cleared session {file_id} from memory")
    
    def clear_all_sessions(self):
        """Clear all sessions from memory."""
        self.sessions.clear()
        logger.info("Cleared all sessions from memory")

