"""
Generate sample PDFs with actual text content for steganography testing.
"""

from __future__ import annotations

import fitz


def create_text_pdf(output_path: str, num_pages: int = 1, text_density: str = "medium") -> None:
    """
    Create a PDF with actual text content (not images).

    Args:
        output_path: Output PDF path
        num_pages: Number of pages to create
        text_density: "low", "medium", or "high" text density
    """
    doc = fitz.open()

    lorem_ipsum = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

    lines_per_page = {"low": 10, "medium": 30, "high": 50}
    num_lines = lines_per_page.get(text_density, 30)

    for page_num in range(num_pages):
        page = doc.new_page(width=595, height=842)

        tw = fitz.TextWriter(page.rect)

        y_pos = 50
        line_height = 15

        tw.append((50, y_pos), f"Document Title - Page {page_num + 1}", fontsize=14)
        y_pos += line_height * 2

        for i in range(num_lines):
            if y_pos > 792 - 50:
                break
            tw.append((50, y_pos), lorem_ipsum, fontsize=10)
            y_pos += line_height

        tw.write_text(page)

    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()


def create_minimal_pdf(output_path: str) -> None:
    """Create a minimal PDF with very little text."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    tw = fitz.TextWriter(page.rect)
    tw.append((50, 50), "Minimal PDF for capacity testing.", fontsize=11)
    tw.write_text(page)

    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()


def create_rich_pdf(output_path: str, num_pages: int = 5) -> None:
    """Create a rich PDF with lots of text content."""
    create_text_pdf(output_path, num_pages=num_pages, text_density="high")


if __name__ == "__main__":
    create_text_pdf("test_single_page.pdf", num_pages=1)
    create_text_pdf("test_multi_page.pdf", num_pages=3)
    create_minimal_pdf("test_minimal.pdf")
    create_rich_pdf("test_rich.pdf", num_pages=5)
    print("Test PDFs generated successfully")
