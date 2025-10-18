"""
Performance benchmarking for the watermark system.
"""

from __future__ import annotations

import time
import os
from PIL import Image
import numpy as np

from pdf_blind_watermark import PDFWatermarker
from pdf_blind_watermark.core.watermark import WatermarkConfig


def create_test_image(width: int, height: int) -> Image.Image:
    """Create a test image with gradient pattern."""
    x = np.linspace(0, 255, width, dtype=np.uint8)
    y = np.linspace(0, 255, height, dtype=np.uint8)
    xx, yy = np.meshgrid(x, y)
    
    r = xx
    g = yy
    b = (xx + yy) // 2
    
    image = np.stack([r, g, b], axis=2)
    return Image.fromarray(image, mode="RGB")


def benchmark_embed(image: Image.Image, watermark_text: str, config: WatermarkConfig) -> float:
    """Benchmark watermark embedding."""
    watermarker = PDFWatermarker(config)
    
    start_time = time.time()
    watermarker.embed_image(image, watermark_text)
    elapsed = time.time() - start_time
    
    return elapsed


def benchmark_extract(image: Image.Image, config: WatermarkConfig) -> float:
    """Benchmark watermark extraction."""
    watermarker = PDFWatermarker(config)
    
    start_time = time.time()
    try:
        watermarker.extract_from_image(image)
    except Exception:
        pass
    elapsed = time.time() - start_time
    
    return elapsed


def run_benchmarks():
    """Run performance benchmarks."""
    print("=" * 60)
    print("Performance Benchmarking - PDF Blind Watermark System")
    print("=" * 60)
    
    test_sizes = [
        (1024, 768, "Small (1024x768)"),
        (1240, 1754, "A4 @ 150dpi"),
        (1754, 2480, "A4 @ 200dpi"),
    ]
    
    configs = [
        (WatermarkConfig(embed_strength=10.0, ecc_symbols=16), "Fast (Strength 10, ECC 16)"),
        (WatermarkConfig(embed_strength=12.0, ecc_symbols=32), "Balanced (Strength 12, ECC 32)"),
        (WatermarkConfig(embed_strength=16.0, ecc_symbols=48), "Robust (Strength 16, ECC 48)"),
    ]
    
    watermark_text = "BENCHMARK-TEST-2024"
    
    for width, height, size_label in test_sizes:
        print(f"\n{size_label}")
        print("-" * 60)
        
        image = create_test_image(width, height)
        
        for config, config_label in configs:
            embed_time = benchmark_embed(image, watermark_text, config)
            print(f"  {config_label:40} | Embed: {embed_time:.3f}s")
    
    print("\n" + "=" * 60)
    print("Benchmark completed.")


if __name__ == "__main__":
    run_benchmarks()
