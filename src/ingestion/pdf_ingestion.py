"""PDF ingestion and extraction module using 100% open-source tools."""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import io

import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from ..config import get_config

logger = logging.getLogger(__name__)


class PDFIngestion:
    """
    Handle PDF text extraction with OCR fallback.

    OPEN-SOURCE ONLY: Uses Tesseract and PaddleOCR (no Google Vision).
    """

    def __init__(self):
        """Initialize PDF ingestion with open-source OCR."""
        self.config = get_config()
        self.primary_tool = self.config.pdf.primary_tool
        self.ocr_threshold = self.config.pdf.ocr_confidence_threshold
        self.max_chunk_chars = self.config.pdf.max_page_chunk_chars
        self.ocr_fallback = self.config.pdf.ocr_fallback

        # Validate no paid OCR services
        if self.ocr_fallback == "google_vision":
            logger.error("Google Vision OCR not supported (paid API)")
            logger.error("Use 'tesseract' or 'paddleocr' instead")
            raise ValueError("Google Vision removed. Use tesseract or paddleocr")

        # Initialize PaddleOCR if selected (optional, falls back to Tesseract)
        self.paddle_ocr = None
        if self.ocr_fallback == "paddleocr":
            try:
                self._init_paddleocr()
            except ImportError as e:
                logger.warning(f"PaddleOCR not available: {e}")
                logger.warning("Falling back to Tesseract OCR")
                self.ocr_fallback = "tesseract"  # Fallback to Tesseract
    
    def extract(self, pdf_path: str) -> List[Dict[str, any]]:
        """
        Extract text from PDF with metadata.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of dicts with keys: text, page, metadata
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        logger.info(f"Extracting text from {pdf_path} using {self.primary_tool}")
        
        if self.primary_tool == "pdfplumber":
            return self._extract_with_pdfplumber(pdf_path)
        elif self.primary_tool == "pymupdf":
            return self._extract_with_pymupdf(pdf_path)
        else:
            raise ValueError(f"Unknown PDF tool: {self.primary_tool}")
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> List[Dict[str, any]]:
        """Extract text using pdfplumber."""
        pages_data = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                
                # Fallback to OCR if text extraction fails
                if not text or len(text.strip()) < 50:
                    logger.warning(f"Page {page_num}: Low text content, using OCR")
                    text = self._ocr_page(page)
                
                pages_data.append({
                    "text": text,
                    "page": page_num,
                    "metadata": {
                        "filename": pdf_path.name,
                        "total_pages": len(pdf.pages),
                        "extraction_method": "pdfplumber"
                    }
                })
        
        logger.info(f"Extracted {len(pages_data)} pages from {pdf_path.name}")
        return pages_data
    
    def _extract_with_pymupdf(self, pdf_path: Path) -> List[Dict[str, any]]:
        """Extract text using PyMuPDF."""
        pages_data = []
        
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Fallback to OCR if needed
            if not text or len(text.strip()) < 50:
                logger.warning(f"Page {page_num + 1}: Low text content, using OCR")
                # Convert page to image for OCR
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img)
            
            pages_data.append({
                "text": text,
                "page": page_num + 1,
                "metadata": {
                    "filename": pdf_path.name,
                    "total_pages": len(doc),
                    "extraction_method": "pymupdf"
                }
            })
        
        doc.close()
        logger.info(f"Extracted {len(pages_data)} pages from {pdf_path.name}")
        return pages_data
    
    def _init_paddleocr(self):
        """Initialize PaddleOCR engine."""
        try:
            from paddleocr import PaddleOCR

            logger.info("Initializing PaddleOCR...")
            self.paddle_ocr = PaddleOCR(
                use_angle_cls=True,  # Enable angle classification
                lang='en',  # Language
                show_log=False,  # Suppress verbose logs
                use_gpu=self.config.system.device == "cuda"
            )
            logger.info("✓ PaddleOCR initialized")

        except ImportError as e:
            logger.warning("PaddleOCR not available - requires paddlepaddle")
            logger.info("To install: pip install paddlepaddle-gpu or paddlepaddle (CPU)")
            logger.info("Falling back to Tesseract OCR")
            raise  # Re-raise to trigger fallback in __init__

    def _ocr_page(self, page) -> str:
        """
        Perform OCR on a pdfplumber page using open-source tools.

        Supports:
        - Tesseract (default, lightweight)
        - PaddleOCR (better accuracy, especially for complex layouts)
        """
        try:
            # Convert page to image
            img = page.to_image(resolution=300)
            pil_img = img.original

            # Perform OCR based on configured method
            if self.ocr_fallback == "paddleocr" and self.paddle_ocr:
                return self._ocr_with_paddleocr(pil_img)
            else:
                return self._ocr_with_tesseract(pil_img)

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def _ocr_with_tesseract(self, image: Image.Image) -> str:
        """Perform OCR using Tesseract."""
        try:
            # Get OCR data with confidence scores
            data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT
            )

            # Filter by confidence threshold
            text_parts = []
            for i, conf in enumerate(data['conf']):
                if conf != -1 and int(conf) >= (self.ocr_threshold * 100):
                    text = data['text'][i]
                    if text.strip():
                        text_parts.append(text)

            result = ' '.join(text_parts)
            logger.debug(f"Tesseract OCR extracted {len(result)} characters")
            return result

        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return ""

    def _ocr_with_paddleocr(self, image: Image.Image) -> str:
        """
        Perform OCR using PaddleOCR (better accuracy than Tesseract).

        PaddleOCR is fully open-source and often outperforms Tesseract,
        especially for complex layouts, tables, and non-Latin scripts.
        """
        try:
            # Convert PIL Image to numpy array
            import numpy as np
            img_array = np.array(image)

            # Run PaddleOCR
            result = self.paddle_ocr.ocr(img_array, cls=True)

            # Extract text from results
            text_parts = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text = line[1][0]  # Extract text
                        confidence = line[1][1]  # Extract confidence

                        # Filter by confidence threshold
                        if confidence >= self.ocr_threshold:
                            text_parts.append(text)

            result_text = ' '.join(text_parts)
            logger.debug(f"PaddleOCR extracted {len(result_text)} characters")
            return result_text

        except Exception as e:
            logger.error(f"PaddleOCR failed: {e}")
            # Fallback to Tesseract
            logger.info("Falling back to Tesseract")
            return self._ocr_with_tesseract(image)
    
    def extract_with_layout(self, pdf_path: str) -> List[Dict[str, any]]:
        """
        Extract text with layout analysis using layout-parser.
        
        NOTE: This is a stub. Full implementation requires:
        - layoutparser library integration
        - Model loading (e.g., PubLayNet)
        - Structure detection (headers, paragraphs, tables, figures)
        - Hierarchical text organization
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of structured content blocks
        """
        # STUB: Implement layout-parser integration
        logger.warning("Layout parsing not implemented - falling back to basic extraction")
        return self.extract(pdf_path)

