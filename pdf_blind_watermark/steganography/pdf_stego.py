from __future__ import annotations

import fitz
from typing import Optional
from pathlib import Path

from .text_encoder import TextEncoder
from .metadata import StegoMetadata
from .capacity import CapacityAnalyzer


class PDFSteganography:
    """PDF text steganography using invisible text and zero-width characters."""

    def __init__(
        self,
        use_compression: bool = True,
        use_ecc: bool = True,
        ecc_symbols: int = 32,
    ):
        """
        Initialize PDF steganography engine.

        Args:
            use_compression: Enable zlib compression
            use_ecc: Enable Reed-Solomon error correction
            ecc_symbols: Number of error correction symbols
        """
        self.encoder = TextEncoder(
            use_compression=use_compression,
            use_ecc=use_ecc,
            ecc_symbols=ecc_symbols,
        )
        self.capacity_analyzer = CapacityAnalyzer()

    def embed(
        self,
        input_pdf: str,
        output_pdf: str,
        metadata: StegoMetadata,
        max_pages: Optional[int] = None,
    ) -> bool:
        """
        Embed metadata into PDF using text steganography.

        Args:
            input_pdf: Path to input PDF
            output_pdf: Path to output PDF
            metadata: Metadata to embed
            max_pages: Maximum pages to use (None = all)

        Returns:
            True if successful, False otherwise
        """
        data = metadata.to_bytes()

        capacity = self.capacity_analyzer.analyze_pdf(input_pdf, max_pages)
        if capacity.estimated_capacity_bytes < len(data):
            raise ValueError(
                f"Insufficient capacity. Need {len(data)} bytes, "
                f"but only {capacity.estimated_capacity_bytes} available."
            )

        encoded_text, _ = self.encoder.encode(data)

        doc = fitz.open(input_pdf)
        num_pages = len(doc) if max_pages is None else min(len(doc), max_pages)

        encoded_per_page = len(encoded_text) // num_pages
        remainder = len(encoded_text) % num_pages

        start_idx = 0
        for page_num in range(num_pages):
            page = doc[page_num]
            chunk_size = encoded_per_page + (1 if page_num < remainder else 0)
            chunk = encoded_text[start_idx : start_idx + chunk_size]

            if chunk:
                self._embed_in_page(page, chunk)

            start_idx += chunk_size

        doc.save(output_pdf, garbage=4, deflate=True, clean=True)
        doc.close()

        return True

    def extract(
        self,
        input_pdf: str,
        max_pages: Optional[int] = None,
    ) -> Optional[StegoMetadata]:
        """
        Extract metadata from PDF.

        Args:
            input_pdf: Path to input PDF
            max_pages: Maximum pages to read (None = all)

        Returns:
            Extracted metadata or None if extraction fails
        """
        doc = fitz.open(input_pdf)
        num_pages = len(doc) if max_pages is None else min(len(doc), max_pages)

        encoded_parts = []
        for page_num in range(num_pages):
            page = doc[page_num]
            extracted = self._extract_from_page(page)
            if extracted:
                encoded_parts.append(extracted)

        doc.close()

        if not encoded_parts:
            return None

        full_encoded = "".join(encoded_parts)
        decoded_data = self.encoder.decode(full_encoded)

        if decoded_data is None:
            return None

        try:
            metadata = StegoMetadata.from_bytes(decoded_data)
            return metadata
        except Exception:
            return None

    def _embed_in_page(self, page: fitz.Page, encoded_text: str):
        """
        Embed encoded text into a PDF page using a hidden annotation.

        Strategy: Store ZWC characters in a FreeText annotation with invisible appearance.
        """
        if not encoded_text:
            return

        rect = fitz.Rect(0, 0, 0.1, 0.1)
        
        annot = page.add_freetext_annot(
            rect,
            encoded_text,
            fontsize=1,
            text_color=(1, 1, 1),
            fill_color=(1, 1, 1),
            border_color=None,
        )
        
        annot.set_opacity(0.0)
        annot.update()

    def _extract_from_page(self, page: fitz.Page) -> str:
        """
        Extract zero-width characters from a page's annotations.
        """
        extracted_zwc = []
        
        for annot in page.annots():
            if annot.type[0] == 2:
                info = annot.info
                content = info.get("content", "")
                if content:
                    zwc = self._filter_zwc(content)
                    if zwc:
                        extracted_zwc.append(zwc)
        
        return "".join(extracted_zwc)

    def _filter_zwc(self, text: str) -> str:
        """Filter out only zero-width characters from text."""
        zwc_chars = {"\u200B", "\u200C", "\u200D"}
        return "".join(char for char in text if char in zwc_chars)

    def check_capacity(
        self,
        pdf_path: str,
        metadata: StegoMetadata,
        max_pages: Optional[int] = None,
    ) -> bool:
        """
        Check if PDF has sufficient capacity for metadata.

        Args:
            pdf_path: Path to PDF file
            metadata: Metadata to check
            max_pages: Maximum pages to use

        Returns:
            True if sufficient capacity
        """
        data_size = len(metadata.to_bytes())
        return self.capacity_analyzer.check_capacity(pdf_path, data_size, max_pages)

    def get_capacity_info(
        self,
        pdf_path: str,
        max_pages: Optional[int] = None,
    ):
        """
        Get detailed capacity information for PDF.

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to analyze

        Returns:
            PDFCapacity object with detailed information
        """
        return self.capacity_analyzer.analyze_pdf(pdf_path, max_pages)
