from __future__ import annotations

import numpy as np
from PIL import Image

from pdf_blind_watermark.core.watermark import PDFWatermarker, WatermarkConfig


def create_test_image(size: int = 1024) -> Image.Image:
    x = np.linspace(0, 255, size, dtype=np.uint8)
    gradient = np.tile(x, (size, 1))
    image = np.stack([gradient, gradient, gradient], axis=2)
    return Image.fromarray(image, mode="RGB")


def test_embed_and_extract_round_trip():
    image = create_test_image(768)
    config = WatermarkConfig(embed_strength=14.0, dpi=180)
    watermarker = PDFWatermarker(config)

    watermark_text = "CTO.NEW-WATERMARK-123"
    watermarked_image = watermarker.embed_image(image, watermark_text)
    extracted_text = watermarker.extract_from_image(watermarked_image)

    assert extracted_text == watermark_text
