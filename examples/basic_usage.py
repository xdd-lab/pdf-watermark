"""
Basic usage examples for PDF Blind Watermarking System.
"""

from pdf_blind_watermark import PDFWatermarker
from pdf_blind_watermark.core.watermark import WatermarkConfig

def example_embed():
    """Example: Embed watermark into a PDF."""
    config = WatermarkConfig(
        embed_strength=12.0,
        quality=85,
        dpi=180
    )
    watermarker = PDFWatermarker(config)
    
    watermarker.embed(
        input_pdf="input.pdf",
        output_pdf="watermarked.pdf",
        watermark_text="MyCompany-2024-001"
    )
    print("Watermark embedded successfully!")


def example_extract_from_pdf():
    """Example: Extract watermark from a PDF."""
    watermarker = PDFWatermarker()
    
    watermark = watermarker.extract(
        input_file="watermarked.pdf",
        source_type="pdf"
    )
    print(f"Extracted watermark: {watermark}")


def example_extract_from_image():
    """Example: Extract watermark from a screenshot or photo."""
    config = WatermarkConfig(rectify=True)
    watermarker = PDFWatermarker(config)
    
    watermark = watermarker.extract(
        input_file="screenshot.jpg",
        source_type="image"
    )
    print(f"Extracted watermark: {watermark}")


if __name__ == "__main__":
    print("PDF Blind Watermarking - Basic Usage Examples")
    print("=" * 50)
    
    print("\n1. Embedding watermark...")
    print("   Uncomment the line below to run:")
    print("   # example_embed()")
    
    print("\n2. Extracting from PDF...")
    print("   Uncomment the line below to run:")
    print("   # example_extract_from_pdf()")
    
    print("\n3. Extracting from image...")
    print("   Uncomment the line below to run:")
    print("   # example_extract_from_image()")
