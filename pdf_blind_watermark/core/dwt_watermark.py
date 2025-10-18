from __future__ import annotations

import numpy as np
import pywt
from typing import Tuple
import cv2


class DWTWatermark:
    """DWT-based watermarking algorithm with high robustness."""

    def __init__(self, wavelet: str = "haar", level: int = 2):
        """
        Initialize DWT watermark engine.

        Args:
            wavelet: Wavelet family to use (haar, db1, db2, etc.)
            level: Level of DWT decomposition (1-3)
        """
        self.wavelet = wavelet
        self.level = level

    def embed(
        self, image: np.ndarray, watermark_bits: np.ndarray, strength: float = 30.0
    ) -> np.ndarray:
        """
        Embed watermark bits into image using DWT.

        Args:
            image: Input image (H, W, 3) in BGR format
            watermark_bits: 2D array of watermark bits (0 or 1)
            strength: Embedding strength (20-50 recommended)

        Returns:
            Watermarked image
        """
        if len(image.shape) == 3:
            yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            y_channel = yuv[:, :, 0].astype(np.float64)
        else:
            y_channel = image.astype(np.float64)

        coeffs = pywt.wavedec2(y_channel, self.wavelet, level=self.level)

        cA = coeffs[0]
        cH, cV, cD = coeffs[1]

        wm_h, wm_w = watermark_bits.shape
        embed_h, embed_w = cH.shape

        if wm_h > embed_h or wm_w > embed_w:
            raise ValueError(
                f"Watermark size {watermark_bits.shape} too large for embedding region {cH.shape}"
            )

        start_h = (embed_h - wm_h) // 2
        start_w = (embed_w - wm_w) // 2

        for i in range(wm_h):
            for j in range(wm_w):
                bit = watermark_bits[i, j]
                if bit > 0:
                    cH[start_h + i, start_w + j] += strength
                else:
                    cH[start_h + i, start_w + j] -= strength

        coeffs[1] = (cH, cV, cD)

        y_watermarked = pywt.waverec2(coeffs, self.wavelet)

        if y_watermarked.shape != y_channel.shape:
            y_watermarked = y_watermarked[: y_channel.shape[0], : y_channel.shape[1]]

        y_watermarked = np.clip(y_watermarked, 0, 255).astype(np.uint8)

        if len(image.shape) == 3:
            yuv[:, :, 0] = y_watermarked
            result = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        else:
            result = y_watermarked

        return result

    def extract(
        self, image: np.ndarray, watermark_shape: Tuple[int, int], threshold: float = 0.0
    ) -> np.ndarray:
        """
        Extract watermark bits from watermarked image.

        Args:
            image: Watermarked image (H, W, 3) in BGR format
            watermark_shape: Expected shape of watermark (h, w)
            threshold: Detection threshold (default 0.0)

        Returns:
            Extracted watermark bits as 2D array
        """
        if len(image.shape) == 3:
            yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            y_channel = yuv[:, :, 0].astype(np.float64)
        else:
            y_channel = image.astype(np.float64)

        coeffs = pywt.wavedec2(y_channel, self.wavelet, level=self.level)

        cH, cV, cD = coeffs[1]

        wm_h, wm_w = watermark_shape
        embed_h, embed_w = cH.shape

        start_h = (embed_h - wm_h) // 2
        start_w = (embed_w - wm_w) // 2

        watermark_bits = np.zeros((wm_h, wm_w), dtype=np.int8)

        for i in range(wm_h):
            for j in range(wm_w):
                value = cH[start_h + i, start_w + j]
                watermark_bits[i, j] = 1 if value > threshold else 0

        return watermark_bits

    def calculate_watermark_capacity(self, image_shape: Tuple[int, int]) -> Tuple[int, int]:
        """
        Calculate maximum watermark size that can be embedded.

        Args:
            image_shape: Shape of the image (height, width)

        Returns:
            Maximum watermark shape (h, w)
        """
        h, w = image_shape[:2]

        test_image = np.zeros((h, w), dtype=np.float64)
        coeffs = pywt.wavedec2(test_image, self.wavelet, level=self.level)
        cH, _, _ = coeffs[1]

        max_h, max_w = cH.shape
        safe_h = int(max_h * 0.8)
        safe_w = int(max_w * 0.8)

        return (safe_h, safe_w)
