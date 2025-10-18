"""
Tests for integrated watermark + steganography workflow.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from pdf_blind_watermark.core.watermark import PDFWatermarker, WatermarkConfig, ExtractionResult


def create_test_image(size: int = 1024) -> Image.Image:
    """Create a test image with gradient pattern."""
    x = np.linspace(0, 255, size, dtype=np.uint8)
    gradient = np.tile(x, (size, 1))
    image = np.stack([gradient, gradient, gradient], axis=2)
    return Image.fromarray(image, mode="RGB")


def test_watermark_only():
    """Test basic watermark embedding and extraction."""
    image = create_test_image(768)
    config = WatermarkConfig(embed_strength=14.0, dpi=180)
    watermarker = PDFWatermarker(config)

    watermark_text = "CTO.NEW-WATERMARK-123"
    watermarked_image = watermarker.embed_image(image, watermark_text)
    result = watermarker.extract_from_image(watermarked_image)
    
    assert result.watermark_text == watermark_text
    assert result.stego_text is None


def test_watermark_with_steganography():
    """Test combined watermark and steganography embedding and extraction."""
    image = create_test_image(1024)
    config = WatermarkConfig(
        embed_strength=14.0,
        dpi=180,
        enable_steganography=True,
        stego_ecc_symbols=16
    )
    watermarker = PDFWatermarker(config)

    watermark_text = "VISIBLE-WATERMARK-2024"
    stego_text = "Secret hidden message"
    
    watermarked_image = watermarker.embed_image(image, watermark_text, stego_text=stego_text)
    result = watermarker.extract_from_image(watermarked_image)
    
    assert result.watermark_text == watermark_text
    assert result.stego_text == stego_text
    assert result.watermark_error is None
    assert result.stego_error is None


def test_steganography_only():
    """Test steganography without watermark text."""
    image = create_test_image(1024)
    config = WatermarkConfig(
        embed_strength=14.0,
        enable_steganography=True,
        stego_ecc_symbols=16
    )
    watermarker = PDFWatermarker(config)

    watermark_text = "WATERMARK"
    stego_text = "Hidden data"
    
    watermarked_image = watermarker.embed_image(image, watermark_text, stego_text=stego_text)
    result = watermarker.extract_from_image(watermarked_image)
    
    assert result.watermark_text == watermark_text
    assert result.stego_text == stego_text


def test_extraction_result_string():
    """Test ExtractionResult string representation."""
    result1 = ExtractionResult(watermark_text="TEST", stego_text="HIDDEN")
    assert "Watermark: TEST" in str(result1)
    assert "Steganography: HIDDEN" in str(result1)
    
    result2 = ExtractionResult(watermark_text="TEST", stego_error="Failed to decode")
    assert "Watermark: TEST" in str(result2)
    assert "Steganography Error: Failed to decode" in str(result2)


def test_backward_compatibility():
    """Test that extract still returns string by default for backward compatibility."""
    from pdf_blind_watermark.core.watermark import PDFWatermarker, WatermarkConfig
    
    image = create_test_image(768)
    config = WatermarkConfig(embed_strength=14.0)
    watermarker = PDFWatermarker(config)
    
    watermark_text = "COMPAT-TEST"
    watermarked_image = watermarker.embed_image(image, watermark_text)
    
    # Save and load via PIL to test real extraction
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        temp_path = f.name
        watermarked_image.save(temp_path)
    
    try:
        # Default behavior - returns string
        extracted = watermarker.extract(temp_path, source_type="image", return_dict=False)
        assert isinstance(extracted, str)
        assert extracted == watermark_text
        
        # New behavior - returns ExtractionResult
        result = watermarker.extract(temp_path, source_type="image", return_dict=True)
        assert isinstance(result, ExtractionResult)
        assert result.watermark_text == watermark_text
    finally:
        import os
        os.unlink(temp_path)
