"""Audio/video ingestion and transcription module."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import whisper
import torch

from ..config import get_config

logger = logging.getLogger(__name__)


class AudioIngestion:
    """Handle audio/video transcription using Whisper."""
    
    def __init__(self):
        """Initialize audio ingestion."""
        self.config = get_config()
        self.model_name = self.config.audio.asr_model
        self.language = self.config.audio.asr_language
        self.beam_size = self.config.audio.beam_size
        self.chunk_length = self.config.audio.chunk_length_seconds
        self.device = self.config.system.device  # Fixed: was config.device

        self.model = None
    
    def load_model(self):
        """Load Whisper model."""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            
            # Extract model size from name (e.g., "whisper-large" -> "large")
            model_size = self.model_name.replace("whisper-", "")
            
            self.model = whisper.load_model(
                model_size,
                device=self.device
            )
            logger.info(f"Whisper model loaded on {self.device}")
    
    def transcribe(self, audio_path: str) -> List[Dict[str, any]]:
        """
        Transcribe audio/video file.
        
        Args:
            audio_path: Path to audio/video file
            
        Returns:
            List of transcript segments with timestamps
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        self.load_model()
        
        logger.info(f"Transcribing {audio_path.name}")
        
        result = self.model.transcribe(
            str(audio_path),
            language=self.language,
            beam_size=self.beam_size,
            verbose=False
        )
        
        # Process segments
        segments = []
        for segment in result["segments"]:
            segments.append({
                "text": segment["text"].strip(),
                "start": segment["start"],
                "end": segment["end"],
                "metadata": {
                    "filename": audio_path.name,
                    "language": result.get("language", self.language),
                    "extraction_method": "whisper"
                }
            })
        
        logger.info(f"Transcribed {len(segments)} segments from {audio_path.name}")
        return segments
    
    def transcribe_with_diarization(self, audio_path: str) -> List[Dict[str, any]]:
        """
        Transcribe with speaker diarization.
        
        NOTE: This is a stub. Full implementation requires:
        - pyannote.audio integration
        - Speaker embedding model
        - Alignment of diarization with transcription
        - Speaker labeling
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            List of segments with speaker labels
        """
        # STUB: Implement diarization
        logger.warning("Speaker diarization not implemented - using basic transcription")
        segments = self.transcribe(audio_path)
        
        # Add placeholder speaker field
        for segment in segments:
            segment["speaker"] = "SPEAKER_00"
        
        return segments
    
    def preprocess_audio(self, audio_path: str, output_path: Optional[str] = None) -> str:
        """
        Preprocess audio with denoising.
        
        NOTE: This is a stub. Full implementation requires:
        - noisereduce library for RNNoise
        - Audio loading with librosa or soundfile
        - Noise reduction processing
        - Saving cleaned audio
        
        Args:
            audio_path: Path to input audio
            output_path: Path to save cleaned audio (optional)
            
        Returns:
            Path to preprocessed audio
        """
        # STUB: Implement audio preprocessing
        logger.warning("Audio preprocessing not implemented - using original file")
        return audio_path

