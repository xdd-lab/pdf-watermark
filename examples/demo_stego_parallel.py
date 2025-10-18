"""
Demo script showcasing text steganography and parallel processing features.
"""
from __future__ import annotations

import time
import tempfile
import numpy as np
from PIL import Image

from pdf_blind_watermark import PDFWatermarker, WatermarkConfig


def create_demo_image(width: int = 1240, height: int = 1754) -> Image.Image:
    """Create a demo image (A4 size at 150 DPI)."""
    x = np.linspace(0, 255, width, dtype=np.uint8)
    y = np.linspace(0, 255, height, dtype=np.uint8)
    xx, yy = np.meshgrid(x, y)
    
    r = xx
    g = yy
    b = (xx + yy) // 2
    
    image = np.stack([r, g, b], axis=2)
    return Image.fromarray(image, mode="RGB")


def demo_combined_watermark_and_stego():
    """Demonstrate combined watermark and steganography."""
    print("=" * 70)
    print("Demo: Combined Watermark + Steganography")
    print("=" * 70)
    
    # Create test image
    image = create_demo_image()
    
    # Configure with both watermark and steganography enabled
    config = WatermarkConfig(
        embed_strength=14.0,
        dpi=150,
        enable_steganography=True,
        stego_ecc_symbols=16
    )
    
    watermarker = PDFWatermarker(config)
    
    # Embed both types of data
    watermark_text = "PUBLIC-WATERMARK-2024"
    stego_text = "Secret metadata: Document ID 12345, User: john@example.com"
    
    print(f"\nEmbedding:")
    print(f"  Watermark (DWT+DCT): {watermark_text}")
    print(f"  Steganography (LSB): {stego_text}")
    
    start = time.time()
    watermarked_image = watermarker.embed_image(
        image, 
        watermark_text, 
        stego_text=stego_text
    )
    embed_time = time.time() - start
    
    print(f"  Embedding time: {embed_time:.3f}s")
    
    # Extract both types of data
    print(f"\nExtracting:")
    start = time.time()
    result = watermarker.extract_from_image(watermarked_image)
    extract_time = time.time() - start
    
    print(f"  Watermark extracted: {result.watermark_text}")
    print(f"  Steganography extracted: {result.stego_text}")
    print(f"  Extraction time: {extract_time:.3f}s")
    
    # Verify
    assert result.watermark_text == watermark_text
    assert result.stego_text == stego_text
    print(f"\n✓ Success! Both data types extracted correctly.")


def demo_parallel_processing():
    """Demonstrate parallel processing for multiple pages."""
    print("\n" + "=" * 70)
    print("Demo: Parallel Processing Performance")
    print("=" * 70)
    
    num_pages = 6
    print(f"\nCreating {num_pages} test images...")
    images = [create_demo_image() for _ in range(num_pages)]
    
    watermark_text = "PERFORMANCE-TEST-2024"
    
    # Sequential processing
    print(f"\n1. Sequential Processing:")
    config_seq = WatermarkConfig(
        embed_strength=12.0,
        enable_parallel=False
    )
    watermarker_seq = PDFWatermarker(config_seq)
    
    start = time.time()
    for img in images:
        watermarker_seq.embed_image(img, watermark_text)
    seq_time = time.time() - start
    
    print(f"   Time: {seq_time:.2f}s ({seq_time/num_pages:.2f}s per page)")
    
    # Parallel processing
    print(f"\n2. Parallel Processing:")
    config_par = WatermarkConfig(
        embed_strength=12.0,
        enable_parallel=True,
        parallel_threshold=3
    )
    watermarker_par = PDFWatermarker(config_par)
    
    start = time.time()
    watermarked = watermarker_par._embed_parallel(images, watermark_text, None)
    par_time = time.time() - start
    
    print(f"   Time: {par_time:.2f}s ({par_time/num_pages:.2f}s per page)")
    
    # Calculate speedup
    speedup = seq_time / par_time
    print(f"\n✓ Speedup: {speedup:.2f}x")
    print(f"   (Parallel is {(1 - par_time/seq_time) * 100:.1f}% faster)")


def demo_extraction_result_api():
    """Demonstrate the new ExtractionResult API."""
    print("\n" + "=" * 70)
    print("Demo: ExtractionResult API")
    print("=" * 70)
    
    image = create_demo_image()
    
    config = WatermarkConfig(
        embed_strength=14.0,
        enable_steganography=True
    )
    watermarker = PDFWatermarker(config)
    
    watermark_text = "WATERMARK-123"
    stego_text = "Hidden payload"
    
    watermarked_image = watermarker.embed_image(image, watermark_text, stego_text=stego_text)
    result = watermarker.extract_from_image(watermarked_image)
    
    print(f"\nExtractionResult object:")
    print(f"  watermark_text: {result.watermark_text}")
    print(f"  stego_text: {result.stego_text}")
    print(f"  watermark_error: {result.watermark_error}")
    print(f"  stego_error: {result.stego_error}")
    
    print(f"\nString representation:")
    print(f"  {result}")
    
    print(f"\n✓ The API provides structured access to all extracted data!")


if __name__ == "__main__":
    demo_combined_watermark_and_stego()
    demo_parallel_processing()
    demo_extraction_result_api()
    
    print("\n" + "=" * 70)
    print("All demos completed successfully!")
    print("=" * 70)
