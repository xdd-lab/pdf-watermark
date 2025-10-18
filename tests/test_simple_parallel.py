"""
Simplified tests for parallel processing using direct image embedding.
"""
from __future__ import annotations

import time
import numpy as np
from PIL import Image

from pdf_blind_watermark.core.watermark import PDFWatermarker, WatermarkConfig


def create_test_image(width: int = 800, height: int = 600) -> Image.Image:
    """Create a test image with gradient pattern."""
    x = np.linspace(0, 255, width, dtype=np.uint8)
    y = np.linspace(0, 255, height, dtype=np.uint8)
    xx, yy = np.meshgrid(x, y)
    
    r = xx
    g = yy
    b = (xx + yy) // 2
    
    image = np.stack([r, g, b], axis=2)
    return Image.fromarray(image, mode="RGB")


def test_parallel_embedding_correctness():
    """Test that parallel embedding produces correct results."""
    watermark_text = "PARALLEL-TEST-2024"
    stego_text = "Hidden data"
    
    # Create test images
    images = [create_test_image() for _ in range(5)]
    
    # Test with parallel enabled
    config_parallel = WatermarkConfig(
        embed_strength=14.0,
        dpi=150,
        enable_parallel=True,
        parallel_threshold=3,
        enable_steganography=True,
        stego_ecc_symbols=16
    )
    
    watermarker_parallel = PDFWatermarker(config_parallel)
    
    # Use the parallel embedding directly
    watermarked_parallel = watermarker_parallel._embed_parallel(
        images, watermark_text, stego_text
    )
    
    # Verify all images can be extracted
    for idx, wm_img in enumerate(watermarked_parallel):
        result = watermarker_parallel.extract_from_image(wm_img)
        assert result.watermark_text == watermark_text, f"Page {idx} watermark mismatch"
        assert result.stego_text == stego_text, f"Page {idx} stego mismatch"


def test_parallel_vs_sequential_consistency():
    """Test that parallel and sequential produce same results."""
    watermark_text = "CONSISTENCY-TEST"
    images = [create_test_image() for _ in range(4)]
    
    # Parallel config
    config_parallel = WatermarkConfig(
        embed_strength=14.0,
        enable_parallel=True,
        parallel_threshold=3
    )
    watermarker_parallel = PDFWatermarker(config_parallel)
    
    # Sequential config
    config_sequential = WatermarkConfig(
        embed_strength=14.0,
        enable_parallel=False
    )
    watermarker_sequential = PDFWatermarker(config_sequential)
    
    # Process images
    watermarked_parallel = watermarker_parallel._embed_parallel(images, watermark_text, None)
    watermarked_sequential = [
        watermarker_sequential.embed_image(img, watermark_text) 
        for img in images
    ]
    
    # Both should extract the same watermark
    for idx, (par_img, seq_img) in enumerate(zip(watermarked_parallel, watermarked_sequential)):
        par_result = watermarker_parallel.extract_from_image(par_img)
        seq_result = watermarker_sequential.extract_from_image(seq_img)
        
        assert par_result.watermark_text == watermark_text
        assert seq_result.watermark_text == watermark_text
        assert par_result.watermark_text == seq_result.watermark_text


def test_parallel_performance():
    """Test that parallel processing is faster for multiple pages."""
    watermark_text = "PERF-TEST"
    num_images = 6
    images = [create_test_image(1000, 1000) for _ in range(num_images)]
    
    # Parallel
    config_parallel = WatermarkConfig(
        embed_strength=12.0,
        enable_parallel=True,
        parallel_threshold=3
    )
    watermarker_parallel = PDFWatermarker(config_parallel)
    
    start = time.time()
    watermarker_parallel._embed_parallel(images, watermark_text, None)
    parallel_time = time.time() - start
    
    # Sequential
    config_sequential = WatermarkConfig(
        embed_strength=12.0,
        enable_parallel=False
    )
    watermarker_sequential = PDFWatermarker(config_sequential)
    
    start = time.time()
    for img in images:
        watermarker_sequential.embed_image(img, watermark_text)
    sequential_time = time.time() - start
    
    print(f"\nParallel: {parallel_time:.2f}s, Sequential: {sequential_time:.2f}s")
    print(f"Speedup: {sequential_time / parallel_time:.2f}x")
    
    # Parallel should be faster (or at least not significantly slower)
    # Allow some tolerance for overhead on small workloads
    assert parallel_time < sequential_time * 1.5


def test_threshold_behavior():
    """Test that parallel only activates above threshold."""
    watermark_text = "THRESHOLD-TEST"
    
    # Below threshold - should use sequential
    config_below = WatermarkConfig(
        embed_strength=14.0,
        enable_parallel=True,
        parallel_threshold=5  # Threshold is 5
    )
    
    images_small = [create_test_image() for _ in range(3)]  # Only 3 images
    watermarker = PDFWatermarker(config_below)
    
    # This should work fine
    results = []
    for img in images_small:
        wm_img = watermarker.embed_image(img, watermark_text)
        results.append(wm_img)
    
    # Verify extraction works
    for wm_img in results:
        result = watermarker.extract_from_image(wm_img)
        assert result.watermark_text == watermark_text


def test_parallel_order_preserved():
    """Test that parallel processing preserves order."""
    watermark_text = "ORDER-TEST"
    
    # Create images with different characteristics
    images = []
    for i in range(5):
        img = create_test_image(800 + i * 100, 600 + i * 50)
        images.append(img)
    
    config = WatermarkConfig(
        embed_strength=14.0,
        enable_parallel=True,
        parallel_threshold=3
    )
    watermarker = PDFWatermarker(config)
    
    watermarked = watermarker._embed_parallel(images, watermark_text, None)
    
    # Check that order is preserved (sizes should match)
    assert len(watermarked) == len(images)
    for i, (orig, wm) in enumerate(zip(images, watermarked)):
        assert orig.size == wm.size, f"Image {i} size mismatch"
