from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np
import pywt
from PIL import Image

from ..image.processor import ImageProcessor
from ..pdf.processor import PDFProcessor
from ..utils.helpers import (
    PREAMBLE,
    bytes_to_bits,
    bits_to_bytes,
    chunk_bytes,
    decode_text,
    encode_text,
    find_preamble,
)
from .error_correction import ErrorCorrection


class WatermarkingError(Exception):
    pass


@dataclass
class WatermarkConfig:
    wavelet: str = "haar"
    block_size: int = 8
    embed_strength: float = 12.0
    ecc_symbols: int = 32
    dpi: int = 180
    quality: int = 85
    rectify: bool = True


class PDFWatermarker:
    """High-robustness blind watermarking for PDF and images."""

    def __init__(self, config: Optional[WatermarkConfig] = None):
        self.config = config or WatermarkConfig()
        self.image_processor = ImageProcessor(rectify=self.config.rectify)
        self.pdf_processor = PDFProcessor(dpi=self.config.dpi)
        self.ecc = ErrorCorrection(self.config.ecc_symbols)
        self._block_pair = ((2, 3), (3, 2))  # Mid-frequency coefficients (row, col)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def embed(
        self,
        input_pdf: str,
        output_pdf: str,
        watermark_text: str,
        max_pages: Optional[int] = None,
    ) -> None:
        """Embed watermark into PDF."""
        images = self.pdf_processor.read_pages(input_pdf, max_pages=max_pages)
        if not images:
            raise WatermarkingError("No pages found in input PDF.")

        watermarked_images = []
        for image in images:
            wm_image = self.embed_image(image, watermark_text)
            watermarked_images.append(wm_image)

        self.pdf_processor.write_pdf(watermarked_images, output_pdf, quality=self.config.quality)

    def embed_image(self, image: Image.Image, watermark_text: str) -> Image.Image:
        """Embed watermark into a single image."""
        preprocessed = self.image_processor.preprocess_for_embedding(image)
        payload_bits = self._create_payload_bits(watermark_text)
        ycbcr = preprocessed.convert("YCbCr")
        y, cb, cr = ycbcr.split()
        y_channel = np.array(y, dtype=np.float32)

        embedded_y = self._embed_bits_into_channel(y_channel, payload_bits)

        embedded_y = np.clip(embedded_y, 0, 255).astype(np.uint8)
        watermarked = Image.merge("YCbCr", (Image.fromarray(embedded_y), cb, cr)).convert("RGB")
        return watermarked

    def extract(
        self,
        input_file: str,
        source_type: str = "pdf",
        max_pages: Optional[int] = None,
    ) -> str:
        """Extract watermark text from PDF or image."""
        source_type = source_type.lower()
        if source_type == "pdf":
            images = self.pdf_processor.read_pages(input_file, max_pages=max_pages)
            if not images:
                raise WatermarkingError("No pages found in PDF for extraction.")

            extractions: List[str] = []
            for image in images:
                try:
                    result = self.extract_from_image(image)
                    if result:
                        extractions.append(result)
                except WatermarkingError:
                    continue

            if not extractions:
                raise WatermarkingError("Failed to extract watermark from any page.")

            # Majority vote for robustness
            most_common = Counter(extractions).most_common(1)
            return most_common[0][0]

        elif source_type == "image":
            image = self.image_processor.load(input_file)
            return self.extract_from_image(image)
        else:
            raise ValueError("source_type must be either 'pdf' or 'image'.")

    def extract_from_image(self, image: Image.Image) -> str:
        """Extract watermark text from image."""
        preprocessed = self.image_processor.preprocess_for_extraction(image)
        ycbcr = preprocessed.convert("YCbCr")
        y, _, _ = ycbcr.split()
        y_channel = np.array(y, dtype=np.float32)

        extracted_bits = self._extract_bits_from_channel(y_channel)
        byte_stream = bits_to_bytes(extracted_bits)

        payload = self._decode_payload(byte_stream)
        return decode_text(payload)

    # ------------------------------------------------------------------
    # Payload encoding/decoding
    # ------------------------------------------------------------------
    def _create_payload_bits(self, watermark_text: str) -> List[int]:
        data_bytes = encode_text(watermark_text)
        if len(data_bytes) > 65535:
            raise WatermarkingError("Watermark text too long (max 65,535 bytes).")

        length_bytes = len(data_bytes).to_bytes(2, "big")
        message = length_bytes + data_bytes

        chunk_size = self.ecc.max_data_length
        segments = chunk_bytes(message, chunk_size)
        segment_count = len(segments)
        last_segment_len = len(segments[-1]) if segments else 0

        encoded_segments: List[bytes] = []
        for segment in segments:
            encoded_segments.append(self.ecc.encode(segment))

        encoded_payload = b"".join(encoded_segments)

        header = (
            PREAMBLE
            + self.config.ecc_symbols.to_bytes(1, "big")
            + chunk_size.to_bytes(2, "big")
            + segment_count.to_bytes(2, "big")
            + last_segment_len.to_bytes(2, "big")
        )

        payload_bytes = header + encoded_payload
        return bytes_to_bits(payload_bytes)

    def _decode_payload(self, data: bytes) -> bytes:
        search_start = 0
        preamble_len = len(PREAMBLE)

        while True:
            index = find_preamble(data[search_start:], PREAMBLE)
            if index == -1:
                raise WatermarkingError("Preamble not found in extracted data.")

            absolute_index = search_start + index
            try:
                return self._decode_payload_from_index(data, absolute_index)
            except WatermarkingError:
                search_start = absolute_index + 1
                if search_start >= len(data):
                    raise

    def _decode_payload_from_index(self, data: bytes, index: int) -> bytes:
        preamble_len = len(PREAMBLE)
        pos = index + preamble_len

        if len(data) < pos + 7:
            raise WatermarkingError("Incomplete payload header.")

        ecc_symbols = data[pos]
        chunk_size = int.from_bytes(data[pos + 1 : pos + 3], "big")
        segment_count = int.from_bytes(data[pos + 3 : pos + 5], "big")
        last_segment_len = int.from_bytes(data[pos + 5 : pos + 7], "big")
        pos += 7

        if ecc_symbols == 0 or segment_count == 0:
            raise WatermarkingError("Invalid payload metadata.")

        ecc = ErrorCorrection(ecc_symbols)
        decoded_segments: List[bytes] = []

        for idx in range(segment_count):
            expected_len = chunk_size if idx < segment_count - 1 else last_segment_len
            encoded_len = expected_len + ecc_symbols
            segment_bytes = data[pos : pos + encoded_len]
            if len(segment_bytes) < encoded_len:
                raise WatermarkingError("Encoded segment truncated.")
            decoded = ecc.decode(segment_bytes)
            if decoded is None:
                raise WatermarkingError("Failed to decode segment with error correction.")
            decoded_segments.append(decoded)
            pos += encoded_len

        decoded_payload = b"".join(decoded_segments)
        if len(decoded_payload) < 2:
            raise WatermarkingError("Decoded payload is too short.")

        message_len = int.from_bytes(decoded_payload[:2], "big")
        message_bytes = decoded_payload[2 : 2 + message_len]
        if len(message_bytes) != message_len:
            raise WatermarkingError("Decoded message length mismatch.")
        return message_bytes

    # ------------------------------------------------------------------
    # Embedding helpers
    # ------------------------------------------------------------------
    def _embed_bits_into_channel(self, channel: np.ndarray, bits: Sequence[int]) -> np.ndarray:
        coeffs = pywt.dwt2(channel, self.config.wavelet)
        LL, (LH, HL, HH) = coeffs
        target = LH.astype(np.float32)

        block_size = self.config.block_size
        blocks_h = target.shape[0] // block_size
        blocks_w = target.shape[1] // block_size
        capacity = blocks_h * blocks_w

        if capacity == 0:
            raise WatermarkingError("Image is too small for watermark embedding.")

        bits_len = len(bits)
        if bits_len > capacity:
            raise WatermarkingError(
                f"Watermark payload too large. Capacity: {capacity} bits, required: {bits_len} bits."
            )

        tiled_bits = self._tile_bits(bits, capacity)

        index = 0
        for i in range(blocks_h):
            for j in range(blocks_w):
                bit = tiled_bits[index]
                block = target[
                    i * block_size : (i + 1) * block_size,
                    j * block_size : (j + 1) * block_size,
                ]
                modified = self._embed_bit(block, bit)
                target[
                    i * block_size : (i + 1) * block_size,
                    j * block_size : (j + 1) * block_size,
                ] = modified
                index += 1

        coeffs = (LL, (target, HL, HH))
        reconstructed = pywt.idwt2(coeffs, self.config.wavelet)
        return reconstructed[: channel.shape[0], : channel.shape[1]]

    def _extract_bits_from_channel(self, channel: np.ndarray) -> List[int]:
        coeffs = pywt.dwt2(channel, self.config.wavelet)
        _, (LH, _, _) = coeffs
        target = LH.astype(np.float32)

        block_size = self.config.block_size
        blocks_h = target.shape[0] // block_size
        blocks_w = target.shape[1] // block_size
        capacity = blocks_h * blocks_w

        if capacity == 0:
            raise WatermarkingError("Image is too small for watermark extraction.")

        bits: List[int] = []
        for i in range(blocks_h):
            for j in range(blocks_w):
                block = target[
                    i * block_size : (i + 1) * block_size,
                    j * block_size : (j + 1) * block_size,
                ]
                bit = self._extract_bit(block)
                bits.append(bit)
        return bits

    def _tile_bits(self, bits: Sequence[int], capacity: int) -> List[int]:
        if len(bits) == 0:
            raise WatermarkingError("No bits to embed.")
        repeats = capacity // len(bits)
        remainder = capacity % len(bits)
        tiled = list(bits) * repeats + list(bits[:remainder])
        if len(tiled) < capacity:
            tiled.extend([0] * (capacity - len(tiled)))
        return tiled

    def _embed_bit(self, block: np.ndarray, bit: int) -> np.ndarray:
        dct_block = cv2.dct(block.astype(np.float32))
        (r1, c1), (r2, c2) = self._block_pair
        coeff1 = dct_block[r1, c1]
        coeff2 = dct_block[r2, c2]
        alpha = self.config.embed_strength

        if bit == 1:
            if coeff1 - coeff2 <= alpha:
                adjustment = (alpha - (coeff1 - coeff2)) / 2.0 + 1.0
                coeff1 += adjustment
                coeff2 -= adjustment
        else:
            if coeff2 - coeff1 <= alpha:
                adjustment = (alpha - (coeff2 - coeff1)) / 2.0 + 1.0
                coeff2 += adjustment
                coeff1 -= adjustment

        dct_block[r1, c1] = coeff1
        dct_block[r2, c2] = coeff2

        modified = cv2.idct(dct_block).astype(np.float32)
        return modified

    def _extract_bit(self, block: np.ndarray) -> int:
        dct_block = cv2.dct(block.astype(np.float32))
        (r1, c1), (r2, c2) = self._block_pair
        coeff1 = dct_block[r1, c1]
        coeff2 = dct_block[r2, c2]
        diff = coeff1 - coeff2
        return 1 if diff >= 0 else 0
