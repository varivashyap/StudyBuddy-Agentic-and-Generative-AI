"""Anki deck exporter."""

import logging
from pathlib import Path
from typing import List, Dict, Optional
import random

import genanki

from ..config import get_config

logger = logging.getLogger(__name__)


class AnkiExporter:
    """Export flashcards to Anki deck format (.apkg)."""
    
    def __init__(self):
        """Initialize Anki exporter."""
        self.config = get_config()
        self.deck_name = self.config.get("export.anki.deck_name", "Study Assistant")
        
        # Create Anki model (card template)
        self.model_id = random.randrange(1 << 30, 1 << 31)
        self.deck_id = random.randrange(1 << 30, 1 << 31)
        
        self._create_models()
    
    def _create_models(self):
        """Create Anki card models for different flashcard types."""
        # Basic model (for definition and concept cards)
        self.basic_model = genanki.Model(
            self.model_id,
            'Study Assistant Basic',
            fields=[
                {'name': 'Front'},
                {'name': 'Back'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '{{Front}}',
                    'afmt': '{{FrontSide}}<hr id="answer">{{Back}}',
                },
            ])
        
        # Cloze model
        self.cloze_model = genanki.Model(
            self.model_id + 1,
            'Study Assistant Cloze',
            fields=[
                {'name': 'Text'},
            ],
            templates=[
                {
                    'name': 'Cloze',
                    'qfmt': '{{cloze:Text}}',
                    'afmt': '{{cloze:Text}}',
                },
            ],
            model_type=genanki.Model.CLOZE)
    
    def export(
        self,
        flashcards: List[Dict[str, str]],
        output_path: str,
        deck_name: Optional[str] = None
    ):
        """
        Export flashcards to Anki deck.
        
        Args:
            flashcards: List of flashcard dicts
            output_path: Path to save .apkg file
            deck_name: Custom deck name (optional)
        """
        if not flashcards:
            logger.warning("No flashcards to export")
            return
        
        deck_name = deck_name or self.deck_name
        
        # Create deck
        deck = genanki.Deck(self.deck_id, deck_name)
        
        # Add cards
        for card in flashcards:
            card_type = card.get('type', 'definition')
            
            if card_type == 'cloze':
                note = self._create_cloze_note(card)
            else:
                note = self._create_basic_note(card)
            
            if note:
                deck.add_note(note)
        
        # Create package and save
        package = genanki.Package(deck)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        package.write_to_file(str(output_path))
        
        logger.info(f"Exported {len(flashcards)} flashcards to {output_path}")
    
    def _create_basic_note(self, card: Dict[str, str]) -> genanki.Note:
        """Create a basic Anki note."""
        front = card.get('front', '')
        back = card.get('back', '')
        
        if not front or not back:
            logger.warning("Skipping card with missing front or back")
            return None
        
        return genanki.Note(
            model=self.basic_model,
            fields=[front, back]
        )
    
    def _create_cloze_note(self, card: Dict[str, str]) -> genanki.Note:
        """Create a cloze deletion Anki note."""
        text = card.get('front', '')
        
        if not text:
            logger.warning("Skipping cloze card with missing text")
            return None
        
        # Ensure cloze format
        if '{{c1::' not in text:
            logger.warning("Cloze card missing {{c1::}} markers")
            return None
        
        return genanki.Note(
            model=self.cloze_model,
            fields=[text]
        )
    
    def export_by_type(
        self,
        flashcards_by_type: Dict[str, List[Dict[str, str]]],
        output_dir: str
    ):
        """
        Export flashcards grouped by type to separate decks.
        
        Args:
            flashcards_by_type: Dict mapping card type to flashcard list
            output_dir: Directory to save deck files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for card_type, cards in flashcards_by_type.items():
            if cards:
                deck_name = f"{self.deck_name} - {card_type.title()}"
                output_path = output_dir / f"{card_type}_deck.apkg"
                self.export(cards, str(output_path), deck_name)

