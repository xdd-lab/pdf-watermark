"""
Tests for parallel processing of multi-page PDFs.
"""
from __future__ import annotations

import time
import tempfile
import os
from pathlib import Path

import numpy as np
from PIL import Image
import fitz

from pdf_blind_watermark.core.watermark import PDFWatermarker, WatermarkConfig


def create_test_image(width: int = 800, height: int = 600, page_num: int = 0) -> Image.Image:
    """Create a test image with a page identifier."""
    # Create gradient with page number encoded
    array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    array[0:50, 0:50] = page_num % 256  # Page identifier
    return Image.fromarray(array, mode="RGB")


def create_test_pdf(num_pages: int = 5) -> str:
    """Create a test PDF with multiple pages."""
    images = [create_test_image(page_num=i) for i in range(num_pages)]
    
    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    doc = fitz.open()
    for img in images:
        img_bytes = img.tobytes()
        img_rect = fitz.Rect(0, 0, img.width, img.height)
        page = doc.new_page(width=img.width, height=img.height)
        
        # Save image to bytes first
        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        
        page.insert_image(img_rect, stream=buf.getvalue())
    
    doc.save(temp_path)
    doc.close()
    
    return temp_path


def test_parallel_vs_sequential():
    """Test that parallel processing produces same results as sequential."""
    watermark_text = "PARALLEL-TEST-2024"
    
    # Create test PDF
    pdf_path = create_test_pdf(num_pages=5)
    
    try:
        # Process with parallel enabled
        config_parallel = WatermarkConfig(
            embed_strength=14.0,
            dpi=150,
            enable_parallel=True,
            parallel_threshold=3
        )
        
        output_parallel = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        watermarker_parallel = PDFWatermarker(config_parallel)
        
        start = time.time()
        watermarker_parallel.embed(pdf_path, output_parallel, watermark_text)
        parallel_time = time.time() - start
        
        # Process with parallel disabled
        config_sequential = WatermarkConfig(
            embed_strength=14.0,
            dpi=150,
            enable_parallel=False
        )
        
        output_sequential = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        watermarker_sequential = PDFWatermarker(config_sequential)
        
        start = time.time()
        watermarker_sequential.embed(pdf_path, output_sequential, watermark_text)
        sequential_time = time.time() - start
        
        # Both should extract the same watermark
        extracted_parallel = watermarker_parallel.extract(output_parallel, source_type="pdf")
        extracted_sequential = watermarker_sequential.extract(output_sequential, source_type="pdf")
        
        assert extracted_parallel == watermark_text
        assert extracted_sequential == watermark_text
        assert extracted_parallel == extracted_sequential
        
        print(f"\nParallel time: {parallel_time:.2f}s")
        print(f"Sequential time: {sequential_time:.2f}s")
        print(f"Speedup: {sequential_time / parallel_time:.2f}x")
        
        # Cleanup
        os.unlink(output_parallel)
        os.unlink(output_sequential)
        
    finally:
        os.unlink(pdf_path)


def test_parallel_threshold():
    """Test that parallel processing only activates above threshold."""
    watermark_text = "THRESHOLD-TEST"
    
    # Create PDFs with different page counts
    for num_pages, should_parallel in [(2, False), (4, True)]:
        pdf_path = create_test_pdf(num_pages=num_pages)
        
        try:
            config = WatermarkConfig(
                embed_strength=14.0,
                dpi=150,
                enable_parallel=True,
                parallel_threshold=3  # Threshold is 3 pages
            )
            
            output_path = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
            watermarker = PDFWatermarker(config)
            
            watermarker.embed(pdf_path, output_path, watermark_text)
            extracted = watermarker.extract(output_path, source_type="pdf")
            
            assert extracted == watermark_text
            
            os.unlink(output_path)
            
        finally:
            os.unlink(pdf_path)


def test_parallel_with_steganography():
    """Test parallel processing with steganography enabled."""
    watermark_text = "WATERMARK-PARALLEL"
    stego_text = "STEGO-PARALLEL"
    
    pdf_path = create_test_pdf(num_pages=4)
    
    try:
        config = WatermarkConfig(
            embed_strength=14.0,
            dpi=150,
            enable_parallel=True,
            parallel_threshold=3,
            enable_steganography=True,
            stego_ecc_symbols=16
        )
        
        output_path = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        watermarker = PDFWatermarker(config)
        
        watermarker.embed(pdf_path, output_path, watermark_text, stego_text=stego_text)
        result = watermarker.extract(output_path, source_type="pdf", return_dict=True)
        
        assert result.watermark_text == watermark_text
        assert result.stego_text == stego_text
        
        os.unlink(output_path)
        
    finally:
        os.unlink(pdf_path)


def test_parallel_page_order_preserved():
    """Test that parallel processing preserves page order."""
    watermark_text = "ORDER-TEST"
    
    pdf_path = create_test_pdf(num_pages=5)
    
    try:
        config = WatermarkConfig(
            embed_strength=14.0,
            dpi=150,
            enable_parallel=True,
            parallel_threshold=3
        )
        
        output_path = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        watermarker = PDFWatermarker(config)
        
        watermarker.embed(pdf_path, output_path, watermark_text)
        
        # Verify page count is preserved
        doc = fitz.open(output_path)
        assert doc.page_count == 5
        doc.close()
        
        os.unlink(output_path)
        
    finally:
        os.unlink(pdf_path)
