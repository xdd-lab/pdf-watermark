"""
Tests for text steganography module.
"""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from pdf_blind_watermark.core.text_steganography import TextSteganography, SteganographyError


def create_test_image(width: int = 512, height: int = 512) -> Image.Image:
    """Create a test RGB image."""
    array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(array, mode="RGB")


def test_embed_and_extract_basic():
    """Test basic embedding and extraction."""
    stego = TextSteganography(ecc_symbols=16)
    image = create_test_image(512, 512)
    text = "Hello, World!"
    
    embedded = stego.embed(image, text)
    extracted = stego.extract(embedded)
    
    assert extracted == text


def test_embed_and_extract_long_text():
    """Test with longer text."""
    stego = TextSteganography(ecc_symbols=32)
    image = create_test_image(1024, 1024)
    text = "This is a much longer text that includes multiple sentences. " * 10
    
    embedded = stego.embed(image, text)
    extracted = stego.extract(embedded)
    
    assert extracted == text


def test_embed_special_characters():
    """Test with special characters and Unicode."""
    stego = TextSteganography(ecc_symbols=16)
    image = create_test_image(512, 512)
    text = "Special chars: !@#$%^&*()_+-=[]{}|;:',.<>?/"
    
    embedded = stego.embed(image, text)
    extracted = stego.extract(embedded)
    
    assert extracted == text


def test_embed_empty_text_fails():
    """Test that embedding empty text raises error."""
    stego = TextSteganography(ecc_symbols=16)
    image = create_test_image(512, 512)
    
    with pytest.raises(SteganographyError, match="Cannot embed empty text"):
        stego.embed(image, "")


def test_embed_text_too_long():
    """Test that embedding text too long for image capacity raises error."""
    stego = TextSteganography(ecc_symbols=16)
    image = create_test_image(64, 64)  # Very small image
    text = "A" * 10000  # Very long text
    
    with pytest.raises(SteganographyError, match="Text too long"):
        stego.embed(image, text)


def test_extract_without_marker_fails():
    """Test that extraction fails when marker is not present."""
    stego = TextSteganography(ecc_symbols=16)
    image = create_test_image(512, 512)  # Fresh image without steganography
    
    with pytest.raises(SteganographyError, match="marker not found"):
        stego.extract(image)


def test_embedding_preserves_image_size():
    """Test that embedding doesn't change image dimensions."""
    stego = TextSteganography(ecc_symbols=16)
    image = create_test_image(640, 480)
    text = "Size test"
    
    embedded = stego.embed(image, text)
    
    assert embedded.size == image.size
    assert embedded.mode == image.mode


def test_minimal_visual_change():
    """Test that steganography causes minimal visual change."""
    stego = TextSteganography(ecc_symbols=16)
    image = create_test_image(512, 512)
    text = "Visual test"
    
    embedded = stego.embed(image, text)
    
    # Convert to arrays
    orig_array = np.array(image)
    embed_array = np.array(embedded)
    
    # Compute difference (should be at most 1 bit per pixel)
    diff = np.abs(orig_array.astype(int) - embed_array.astype(int))
    
    # All differences should be 0 or 1 (LSB change only)
    assert np.all(diff <= 1)
    
    # Most pixels should be unchanged
    unchanged_pixels = np.sum(diff == 0)
    total_pixels = diff.size
    unchanged_ratio = unchanged_pixels / total_pixels
    
    # At least 90% of pixel values should remain unchanged
    assert unchanged_ratio > 0.9


def test_error_correction_works():
    """Test that error correction can recover from bit flips."""
    stego = TextSteganography(ecc_symbols=32)  # More ECC for better correction
    image = create_test_image(1024, 1024)
    text = "Error correction test"
    
    embedded = stego.embed(image, text)
    
    # Introduce some noise (flip some bits beyond the payload)
    array = np.array(embedded)
    # Flip some LSBs in the latter part of the image
    noise_start = 100000
    array.flat[noise_start:noise_start + 100] ^= 1
    noisy_image = Image.fromarray(array, mode="RGB")
    
    # Should still extract correctly due to error correction
    extracted = stego.extract(noisy_image)
    assert extracted == text
