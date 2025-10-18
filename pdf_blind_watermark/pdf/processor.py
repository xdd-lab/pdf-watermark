from __future__ import annotations

import io
from typing import List, Optional

import fitz
from PIL import Image
from tqdm import tqdm


class PDFProcessor:
    """Processor for reading and writing PDFs using PyMuPDF."""

    def __init__(self, dpi: int = 150, use_multiprocess: bool = True):
        """
        Initialize PDF processor.

        Args:
            dpi: Resolution for rendering PDF pages (default 150, higher = better quality)
            use_multiprocess: Whether to use multiprocessing for batch operations
        """
        self.dpi = dpi
        self.use_multiprocess = use_multiprocess

    def read_pages(self, pdf_path: str, max_pages: Optional[int] = None) -> List[Image.Image]:
        """
        Read PDF and return list of page images.

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to read (None = all)

        Returns:
            List of PIL Images
        """
        doc = fitz.open(pdf_path)
        total_pages = min(doc.page_count, max_pages) if max_pages else doc.page_count

        images = []
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)

        doc.close()
        return images

    def write_pdf(self, images: List[Image.Image], output_path: str, quality: int = 85) -> None:
        """
        Write list of images to PDF file.

        Args:
            images: List of PIL Images
            output_path: Output PDF file path
            quality: JPEG quality for compression (70-95)
        """
        doc = fitz.open()

        for idx, img in enumerate(tqdm(images, desc="Writing PDF pages")):
            img_bytes = self._image_to_bytes(img, quality)

            img_rect = fitz.Rect(0, 0, img.width, img.height)
            page = doc.new_page(width=img.width, height=img.height)
            page.insert_image(img_rect, stream=img_bytes)

        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()

    def _image_to_bytes(self, image: Image.Image, quality: int = 85) -> bytes:
        """Convert PIL Image to compressed JPEG bytes."""
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()

    def get_page_count(self, pdf_path: str) -> int:
        """Get the total number of pages in a PDF."""
        doc = fitz.open(pdf_path)
        count = doc.page_count
        doc.close()
        return count

    def read_page(self, pdf_path: str, page_num: int) -> Image.Image:
        """Read a single page from PDF."""
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img
