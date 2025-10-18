from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple
import multiprocessing

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
from .text_steganography import TextSteganography, SteganographyError


class WatermarkingError(Exception):
    pass


@dataclass
class ExtractionResult:
    """Result of watermark and steganography extraction."""
    watermark_text: str
    stego_text: Optional[str] = None
    watermark_error: Optional[str] = None
    stego_error: Optional[str] = None
    
    def __str__(self) -> str:
        parts = []
        if self.watermark_text:
            parts.append(f"Watermark: {self.watermark_text}")
        if self.watermark_error:
            parts.append(f"Watermark Error: {self.watermark_error}")
        if self.stego_text:
            parts.append(f"Steganography: {self.stego_text}")
        if self.stego_error:
            parts.append(f"Steganography Error: {self.stego_error}")
        return " | ".join(parts) if parts else "No data extracted"


@dataclass
class WatermarkConfig:
    wavelet: str = "haar"
    block_size: int = 8
    embed_strength: float = 12.0
    ecc_symbols: int = 32
    dpi: int = 180
    quality: int = 85
    rectify: bool = True
    enable_steganography: bool = False
    stego_ecc_symbols: int = 16
    enable_parallel: bool = True
    parallel_threshold: int = 3


class PDFWatermarker:
    """High-robustness blind watermarking for PDF and images."""

    def __init__(self, config: Optional[WatermarkConfig] = None):
        self.config = config or WatermarkConfig()
        self.image_processor = ImageProcessor(rectify=self.config.rectify)
        self.pdf_processor = PDFProcessor(dpi=self.config.dpi)
        self.ecc = ErrorCorrection(self.config.ecc_symbols)
        self._block_pair = ((2, 3), (3, 2))  # Mid-frequency coefficients (row, col)
        if self.config.enable_steganography:
            self.steganography = TextSteganography(ecc_symbols=self.config.stego_ecc_symbols)
        else:
            self.steganography = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def embed(
        self,
        input_pdf: str,
        output_pdf: str,
        watermark_text: str,
        max_pages: Optional[int] = None,
        stego_text: Optional[str] = None,
    ) -> None:
        """Embed watermark into PDF.
        
        Args:
            input_pdf: Path to input PDF file
            output_pdf: Path to output PDF file
            watermark_text: Text to embed as frequency-domain watermark
            max_pages: Maximum number of pages to process
            stego_text: Optional text to embed via steganography
        """
        images = self.pdf_processor.read_pages(input_pdf, max_pages=max_pages)
        if not images:
            raise WatermarkingError("No pages found in input PDF.")

        if self.config.enable_parallel and len(images) >= self.config.parallel_threshold:
            watermarked_images = self._embed_parallel(images, watermark_text, stego_text)
        else:
            watermarked_images = []
            for image in images:
                wm_image = self.embed_image(image, watermark_text, stego_text=stego_text)
                watermarked_images.append(wm_image)

        self.pdf_processor.write_pdf(watermarked_images, output_pdf, quality=self.config.quality)

    def embed_image(
        self, 
        image: Image.Image, 
        watermark_text: str, 
        stego_text: Optional[str] = None
    ) -> Image.Image:
        """Embed watermark into a single image.
        
        Args:
            image: PIL Image to embed watermark into
            watermark_text: Text to embed as frequency-domain watermark
            stego_text: Optional text to embed via steganography
            
        Returns:
            Image with embedded watermark (and optional steganography)
        """
        preprocessed = self.image_processor.preprocess_for_embedding(image)
        payload_bits = self._create_payload_bits(watermark_text)
        ycbcr = preprocessed.convert("YCbCr")
        y, cb, cr = ycbcr.split()
        y_channel = np.array(y, dtype=np.float32)

        embedded_y = self._embed_bits_into_channel(y_channel, payload_bits)

        embedded_y = np.clip(embedded_y, 0, 255).astype(np.uint8)
        watermarked = Image.merge("YCbCr", (Image.fromarray(embedded_y), cb, cr)).convert("RGB")
        
        if self.steganography and stego_text:
            try:
                watermarked = self.steganography.embed(watermarked, stego_text)
            except SteganographyError as e:
                raise WatermarkingError(f"Steganography embedding failed: {e}")
        
        return watermarked

    def extract(
        self,
        input_file: str,
        source_type: str = "pdf",
        max_pages: Optional[int] = None,
        return_dict: bool = False,
    ) -> ExtractionResult | str:
        """Extract watermark text from PDF or image.
        
        Args:
            input_file: Path to input file
            source_type: Type of input file ('pdf' or 'image')
            max_pages: Maximum number of pages to process (PDF only)
            return_dict: If True, return ExtractionResult, else return watermark string
            
        Returns:
            ExtractionResult if return_dict=True, otherwise watermark text string
        """
        source_type = source_type.lower()
        if source_type == "pdf":
            images = self.pdf_processor.read_pages(input_file, max_pages=max_pages)
            if not images:
                raise WatermarkingError("No pages found in PDF for extraction.")

            extractions: List[ExtractionResult] = []
            for image in images:
                try:
                    result = self.extract_from_image(image)
                    if result.watermark_text:
                        extractions.append(result)
                except WatermarkingError:
                    continue

            if not extractions:
                raise WatermarkingError("Failed to extract watermark from any page.")

            # Majority vote for robustness
            watermark_counts = Counter([r.watermark_text for r in extractions if r.watermark_text])
            most_common_wm = watermark_counts.most_common(1)[0][0] if watermark_counts else ""
            
            stego_counts = Counter([r.stego_text for r in extractions if r.stego_text])
            most_common_stego = stego_counts.most_common(1)[0][0] if stego_counts else None
            
            result = ExtractionResult(watermark_text=most_common_wm, stego_text=most_common_stego)
            return result if return_dict else result.watermark_text

        elif source_type == "image":
            image = self.image_processor.load(input_file)
            result = self.extract_from_image(image)
            return result if return_dict else result.watermark_text
        else:
            raise ValueError("source_type must be either 'pdf' or 'image'.")

    def extract_from_image(self, image: Image.Image) -> ExtractionResult:
        """Extract watermark text from image.
        
        Args:
            image: PIL Image to extract from
            
        Returns:
            ExtractionResult with watermark and optional steganography data
        """
        preprocessed = self.image_processor.preprocess_for_extraction(image)
        
        watermark_text = ""
        watermark_error = None
        stego_text = None
        stego_error = None
        
        try:
            ycbcr = preprocessed.convert("YCbCr")
            y, _, _ = ycbcr.split()
            y_channel = np.array(y, dtype=np.float32)

            extracted_bits = self._extract_bits_from_channel(y_channel)
            byte_stream = bits_to_bytes(extracted_bits)

            payload = self._decode_payload(byte_stream)
            watermark_text = decode_text(payload)
        except WatermarkingError as e:
            watermark_error = str(e)
            raise
        
        if self.steganography:
            try:
                stego_text = self.steganography.extract(preprocessed)
            except SteganographyError as e:
                stego_error = str(e)
        
        return ExtractionResult(
            watermark_text=watermark_text,
            stego_text=stego_text,
            watermark_error=watermark_error,
            stego_error=stego_error
        )

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

    # ------------------------------------------------------------------
    # Parallel processing helpers
    # ------------------------------------------------------------------
    def _embed_parallel(
        self,
        images: List[Image.Image],
        watermark_text: str,
        stego_text: Optional[str] = None,
    ) -> List[Image.Image]:
        """Embed watermark in parallel across multiple pages."""
        num_workers = min(multiprocessing.cpu_count(), len(images))
        
        results = [None] * len(images)
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(
                    _embed_worker, 
                    image, 
                    watermark_text,
                    stego_text,
                    self.config
                ): idx 
                for idx, image in enumerate(images)
            }
            
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    raise WatermarkingError(f"Parallel embedding failed on page {idx}: {e}")
        
        return results


def _embed_worker(
    image: Image.Image,
    watermark_text: str,
    stego_text: Optional[str],
    config: WatermarkConfig,
) -> Image.Image:
    """Worker function for parallel embedding (must be at module level for pickling)."""
    watermarker = PDFWatermarker(config)
    return watermarker.embed_image(image, watermark_text, stego_text=stego_text)
