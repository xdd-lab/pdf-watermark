"""
Generate a sample PDF for testing the watermark system.
"""

from __future__ import annotations

from PIL import Image, ImageDraw
import fitz

def create_sample_page(width: int = 1240, height: int = 1754, page_num: int = 1) -> Image.Image:
    """Create a sample page with text and graphics."""
    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    title = f"Sample Document - Page {page_num}"
    draw.text((width // 2 - 200, 100), title, fill=(0, 0, 0))
    
    y_pos = 200
    for i in range(20):
        line = f"Line {i + 1}: This is sample text for testing the PDF watermark system."
        draw.text((100, y_pos), line, fill=(50, 50, 50))
        y_pos += 40
        if y_pos > height - 200:
            break
    
    for i in range(5):
        x1 = 100 + i * 200
        y1 = height - 300
        x2 = x1 + 150
        y2 = y1 + 100
        draw.rectangle([x1, y1, x2, y2], outline=(100, 100, 200), width=2)
    
    return image


def generate_sample_pdf(output_path: str, num_pages: int = 3) -> None:
    """Generate a sample PDF with multiple pages."""
    doc = fitz.open()
    
    for page_num in range(1, num_pages + 1):
        img = create_sample_page(page_num=page_num)

        page = doc.new_page(width=img.width, height=img.height)

        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        img_rect = fitz.Rect(0, 0, img.width, img.height)
        page.insert_image(img_rect, stream=buf.getvalue())
    
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    print(f"Sample PDF generated: {output_path}")


if __name__ == "__main__":
    generate_sample_pdf("sample_document.pdf", num_pages=3)
