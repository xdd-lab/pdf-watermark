from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import fitz


@dataclass
class PageCapacity:
    """Capacity information for a single PDF page."""

    page_number: int
    text_blocks: int
    total_characters: int
    available_positions: int


@dataclass
class PDFCapacity:
    """Capacity information for entire PDF."""

    total_pages: int
    page_capacities: List[PageCapacity]
    total_available_positions: int
    estimated_capacity_bytes: int

    def get_page_capacity(self, page_number: int) -> Optional[PageCapacity]:
        """Get capacity info for specific page."""
        for pc in self.page_capacities:
            if pc.page_number == page_number:
                return pc
        return None


class CapacityAnalyzer:
    """Analyzes PDF capacity for text steganography."""

    def analyze_pdf(self, pdf_path: str, max_pages: Optional[int] = None) -> PDFCapacity:
        """
        Analyze PDF to determine steganography capacity.

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to analyze (None = all)

        Returns:
            PDFCapacity with detailed capacity information
        """
        doc = fitz.open(pdf_path)
        page_capacities = []
        total_positions = 0

        num_pages = len(doc) if max_pages is None else min(len(doc), max_pages)

        for page_num in range(num_pages):
            page = doc[page_num]
            capacity = self._analyze_page(page, page_num)
            page_capacities.append(capacity)
            total_positions += capacity.available_positions

        doc.close()

        estimated_bytes = self._estimate_capacity(total_positions)

        return PDFCapacity(
            total_pages=num_pages,
            page_capacities=page_capacities,
            total_available_positions=total_positions,
            estimated_capacity_bytes=estimated_bytes,
        )

    def _analyze_page(self, page: fitz.Page, page_num: int) -> PageCapacity:
        """Analyze capacity of a single page."""
        text_blocks = page.get_text("blocks")
        total_chars = 0
        available_positions = 0

        for block in text_blocks:
            if len(block) >= 5:
                block_text = block[4]
                if isinstance(block_text, str):
                    char_count = len(block_text)
                    total_chars += char_count
                    available_positions += char_count

        return PageCapacity(
            page_number=page_num,
            text_blocks=len(text_blocks),
            total_characters=total_chars,
            available_positions=available_positions,
        )

    def _estimate_capacity(self, total_positions: int) -> int:
        """
        Estimate capacity in bytes.
        Conservative estimate: 6 ZWC per byte, with ECC and compression overhead.
        """
        if total_positions == 0:
            return 0

        positions_per_byte = 6
        header_overhead = 8
        ecc_overhead = 1.3
        compression_gain = 0.6

        raw_capacity = (total_positions // positions_per_byte) - header_overhead
        capacity_with_ecc = raw_capacity / ecc_overhead
        estimated_capacity = int(capacity_with_ecc * compression_gain)

        return max(0, estimated_capacity)

    def check_capacity(
        self,
        pdf_path: str,
        data_size: int,
        max_pages: Optional[int] = None,
    ) -> bool:
        """
        Check if PDF has sufficient capacity for data.

        Args:
            pdf_path: Path to PDF file
            data_size: Size of data in bytes
            max_pages: Maximum pages to use

        Returns:
            True if sufficient capacity, False otherwise
        """
        capacity = self.analyze_pdf(pdf_path, max_pages)
        return capacity.estimated_capacity_bytes >= data_size
