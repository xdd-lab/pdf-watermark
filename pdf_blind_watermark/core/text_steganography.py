from __future__ import annotations

import struct
from typing import Optional

import numpy as np
from PIL import Image

from ..utils.helpers import encode_text, decode_text
from .error_correction import ErrorCorrection


class SteganographyError(Exception):
    pass


STEGO_MARKER = b"STEG"
MARKER_LEN = len(STEGO_MARKER)


class TextSteganography:
    """LSB-based text steganography for images.
    
    This module uses Least Significant Bit embedding to hide text data
    in the spatial domain of images. It complements the frequency-domain
    watermarking by operating in a different transform space.
    """
    
    def __init__(self, ecc_symbols: int = 16):
        """Initialize text steganography.
        
        Args:
            ecc_symbols: Number of Reed-Solomon error correction symbols
        """
        self.ecc = ErrorCorrection(ecc_symbols)
        self.ecc_symbols = ecc_symbols
    
    def embed(self, image: Image.Image, text: str) -> Image.Image:
        """Embed text into image using LSB steganography.
        
        Args:
            image: PIL Image to embed text into
            text: Text to embed
            
        Returns:
            Image with embedded text
            
        Raises:
            SteganographyError: If text is too long for image capacity
        """
        if not text:
            raise SteganographyError("Cannot embed empty text")
        
        img_array = np.array(image, dtype=np.uint8).copy()
        if len(img_array.shape) != 3:
            raise SteganographyError("Image must be RGB format")
        
        h, w, channels = img_array.shape
        
        text_bytes = encode_text(text)
        
        # Chunk data if it's too long for ECC
        chunk_size = self.ecc.max_data_length
        if len(text_bytes) > chunk_size:
            chunks = [text_bytes[i:i+chunk_size] for i in range(0, len(text_bytes), chunk_size)]
            encoded_chunks = [self.ecc.encode(chunk) for chunk in chunks]
            encoded_data = b''.join(encoded_chunks)
            num_chunks = len(chunks)
        else:
            encoded_data = self.ecc.encode(text_bytes)
            num_chunks = 1
        
        # Pack: MARKER (4 bytes) + num_chunks (2 bytes) + data_length (4 bytes) + encoded_data
        length_bytes = struct.pack(">I", len(text_bytes))
        num_chunks_bytes = struct.pack(">H", num_chunks)
        payload = STEGO_MARKER + num_chunks_bytes + length_bytes + encoded_data
        
        total_bits = len(payload) * 8
        
        capacity = h * w * channels
        
        if total_bits > capacity:
            raise SteganographyError(
                f"Text too long for image. Need {total_bits} bits, capacity is {capacity} bits."
            )
        
        payload_bits = self._bytes_to_bits(payload)
        
        flat_img = img_array.reshape(-1)
        
        for i, bit in enumerate(payload_bits):
            flat_img[i] = (flat_img[i] & 0xFE) | bit
        
        result_array = flat_img.reshape(h, w, channels)
        
        return Image.fromarray(result_array, mode=image.mode)
    
    def extract(self, image: Image.Image) -> str:
        """Extract text from image using LSB steganography.
        
        Args:
            image: PIL Image with embedded text
            
        Returns:
            Extracted text
            
        Raises:
            SteganographyError: If extraction fails
        """
        img_array = np.array(image, dtype=np.uint8)
        if len(img_array.shape) != 3:
            raise SteganographyError("Image must be RGB format")
        
        flat_img = img_array.reshape(-1)
        
        # Read marker
        marker_bits_count = MARKER_LEN * 8
        marker_bits = [int(flat_img[i] & 1) for i in range(marker_bits_count)]
        marker_bytes = self._bits_to_bytes(marker_bits)
        
        if marker_bytes != STEGO_MARKER:
            raise SteganographyError("Steganography marker not found")
        
        # Read num_chunks
        pos = marker_bits_count
        num_chunks_bits_count = 2 * 8
        num_chunks_bits = [
            int(flat_img[i] & 1)
            for i in range(pos, pos + num_chunks_bits_count)
        ]
        num_chunks_bytes = self._bits_to_bytes(num_chunks_bits)
        num_chunks = struct.unpack(">H", num_chunks_bytes)[0]
        
        if num_chunks == 0 or num_chunks > 1000:
            raise SteganographyError("Invalid number of chunks in steganography payload")
        
        # Read original data length
        pos += num_chunks_bits_count
        length_bits_count = 4 * 8
        length_bits = [
            int(flat_img[i] & 1) 
            for i in range(pos, pos + length_bits_count)
        ]
        length_bytes = self._bits_to_bytes(length_bits)
        original_data_length = struct.unpack(">I", length_bytes)[0]
        
        if original_data_length == 0 or original_data_length > 10000000:
            raise SteganographyError("Invalid data length in steganography payload")
        
        # Read encoded data
        pos += length_bits_count
        
        # Calculate encoded data length based on chunks
        chunk_size = self.ecc.max_data_length
        encoded_chunk_size = chunk_size + self.ecc_symbols
        
        if num_chunks == 1:
            # Single chunk
            encoded_length = original_data_length + self.ecc_symbols
        else:
            # Multiple chunks
            full_chunks = original_data_length // chunk_size
            last_chunk_size = original_data_length % chunk_size
            if last_chunk_size > 0:
                encoded_length = full_chunks * encoded_chunk_size + last_chunk_size + self.ecc_symbols
            else:
                encoded_length = full_chunks * encoded_chunk_size
        
        data_bits_count = encoded_length * 8
        
        if pos + data_bits_count > len(flat_img) * 8:
            raise SteganographyError("Embedded data extends beyond image capacity")
        
        data_bits = [
            int(flat_img[i] & 1)
            for i in range(pos, pos + data_bits_count)
        ]
        encoded_data = self._bits_to_bytes(data_bits)
        
        # Decode chunks
        decoded_chunks = []
        offset = 0
        for chunk_idx in range(num_chunks):
            if chunk_idx < num_chunks - 1:
                # Full chunk
                chunk_data = encoded_data[offset:offset + encoded_chunk_size]
                offset += encoded_chunk_size
            else:
                # Last chunk (might be partial)
                last_data_size = original_data_length - (chunk_idx * chunk_size)
                chunk_data = encoded_data[offset:offset + last_data_size + self.ecc_symbols]
            
            decoded_chunk = self.ecc.decode(chunk_data)
            if decoded_chunk is None:
                raise SteganographyError(f"Failed to decode chunk {chunk_idx} with error correction")
            decoded_chunks.append(decoded_chunk)
        
        decoded_data = b''.join(decoded_chunks)
        
        # Verify length
        if len(decoded_data) != original_data_length:
            raise SteganographyError(f"Decoded data length mismatch: expected {original_data_length}, got {len(decoded_data)}")
        
        return decode_text(decoded_data)
    
    def _bytes_to_bits(self, data: bytes) -> list[int]:
        """Convert bytes to list of bits."""
        bits = []
        for byte in data:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        return bits
    
    def _bits_to_bytes(self, bits: list[int]) -> bytes:
        """Convert list of bits to bytes."""
        byte_list = []
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            if len(byte_bits) < 8:
                byte_bits.extend([0] * (8 - len(byte_bits)))
            byte_val = 0
            for bit in byte_bits:
                byte_val = (byte_val << 1) | bit
            byte_list.append(byte_val)
        return bytes(byte_list)
