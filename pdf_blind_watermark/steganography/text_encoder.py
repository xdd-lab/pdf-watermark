from __future__ import annotations

import zlib
from typing import Tuple, Optional
from ..core.error_correction import ErrorCorrection


ZERO_WIDTH_SPACE = "\u200B"
ZERO_WIDTH_NON_JOINER = "\u200C"
ZERO_WIDTH_JOINER = "\u200D"


class TextEncoder:
    """Encodes binary data into invisible zero-width characters."""

    def __init__(
        self,
        use_compression: bool = True,
        use_ecc: bool = True,
        ecc_symbols: int = 32,
    ):
        """
        Initialize text encoder.

        Args:
            use_compression: Enable zlib compression
            use_ecc: Enable Reed-Solomon error correction
            ecc_symbols: Number of error correction symbols
        """
        self.use_compression = use_compression
        self.use_ecc = use_ecc
        self.ecc_symbols = ecc_symbols
        if use_ecc:
            self.ecc = ErrorCorrection(ecc_symbols)
        else:
            self.ecc = None

    def encode(self, data: bytes) -> Tuple[str, int]:
        """
        Encode binary data into zero-width characters.

        Args:
            data: Binary data to encode

        Returns:
            Tuple of (encoded string, original data length)
        """
        original_length = len(data)

        if self.use_compression:
            data = zlib.compress(data, level=9)

        if self.use_ecc:
            max_chunk_size = self.ecc.max_data_length
            chunks = []
            chunk_count = 0
            for i in range(0, len(data), max_chunk_size):
                chunk = data[i : i + max_chunk_size]
                encoded_chunk = self.ecc.encode(chunk)
                chunks.append(encoded_chunk)
                chunk_count += 1
            data = b"".join(chunks)

        header = self._create_header(original_length, self.use_compression, self.use_ecc)
        full_data = header + data

        encoded = self._bytes_to_zwc(full_data)
        return encoded, original_length

    def decode(self, encoded: str) -> Optional[bytes]:
        """
        Decode zero-width characters back to binary data.

        Args:
            encoded: String containing zero-width characters

        Returns:
            Decoded binary data or None if decoding fails
        """
        try:
            full_data = self._zwc_to_bytes(encoded)
            if len(full_data) < 8:
                return None

            header = full_data[:8]
            original_length, use_compression, use_ecc = self._parse_header(header)

            data = full_data[8:]

            if use_ecc:
                if self.ecc is None:
                    self.ecc = ErrorCorrection(self.ecc_symbols)

                encoded_chunk_size = 255
                decoded_chunks = []
                i = 0
                while i < len(data):
                    chunk = data[i : i + encoded_chunk_size]
                    if len(chunk) == 0:
                        break
                    decoded_chunk = self.ecc.decode(chunk)
                    if decoded_chunk is None:
                        return None
                    decoded_chunks.append(decoded_chunk)
                    i += encoded_chunk_size

                data = b"".join(decoded_chunks)

            if use_compression:
                data = zlib.decompress(data)

            return data

        except Exception:
            return None

    def _create_header(
        self, original_length: int, use_compression: bool, use_ecc: bool
    ) -> bytes:
        """
        Create 8-byte header: [original_length: 4 bytes][flags: 1 byte][reserved: 3 bytes]
        """
        flags = 0
        if use_compression:
            flags |= 0x01
        if use_ecc:
            flags |= 0x02

        header = original_length.to_bytes(4, "big")
        header += bytes([flags])
        header += bytes(3)
        return header

    def _parse_header(self, header: bytes) -> Tuple[int, bool, bool]:
        """Parse header to extract metadata."""
        original_length = int.from_bytes(header[:4], "big")
        flags = header[4]
        use_compression = bool(flags & 0x01)
        use_ecc = bool(flags & 0x02)
        return original_length, use_compression, use_ecc

    def _bytes_to_zwc(self, data: bytes) -> str:
        """
        Convert bytes to zero-width characters using ternary encoding.
        Each byte is converted to base-3 digits, each represented by a ZWC.
        """
        result = []
        for byte in data:
            digits = self._byte_to_ternary(byte)
            for digit in digits:
                if digit == 0:
                    result.append(ZERO_WIDTH_SPACE)
                elif digit == 1:
                    result.append(ZERO_WIDTH_NON_JOINER)
                else:
                    result.append(ZERO_WIDTH_JOINER)
        return "".join(result)

    def _zwc_to_bytes(self, zwc_string: str) -> bytes:
        """Convert zero-width characters back to bytes."""
        digits = []
        for char in zwc_string:
            if char == ZERO_WIDTH_SPACE:
                digits.append(0)
            elif char == ZERO_WIDTH_NON_JOINER:
                digits.append(1)
            elif char == ZERO_WIDTH_JOINER:
                digits.append(2)

        result = []
        i = 0
        while i + 6 <= len(digits):
            byte_val = self._ternary_to_byte(digits[i : i + 6])
            result.append(byte_val)
            i += 6

        return bytes(result)

    def _byte_to_ternary(self, byte: int) -> list:
        """Convert a byte to 6 ternary digits (3^6 = 729 > 256)."""
        digits = []
        value = byte
        for _ in range(6):
            digits.append(value % 3)
            value //= 3
        return list(reversed(digits))

    def _ternary_to_byte(self, digits: list) -> int:
        """Convert 6 ternary digits back to a byte."""
        value = 0
        for digit in digits:
            value = value * 3 + digit
        return value % 256

    def calculate_capacity(self, available_positions: int) -> int:
        """
        Calculate maximum data capacity given available insertion positions.

        Args:
            available_positions: Number of positions where ZWC can be inserted

        Returns:
            Maximum bytes that can be encoded
        """
        positions_per_byte = 6
        overhead = 8

        max_bytes_before_encoding = (available_positions // positions_per_byte) - overhead

        if max_bytes_before_encoding <= 0:
            return 0

        if self.use_ecc:
            max_bytes_before_encoding = (
                max_bytes_before_encoding * self.ecc.max_data_length
            ) // 255

        if self.use_compression:
            max_bytes_before_encoding = int(max_bytes_before_encoding * 2.5)

        return max(0, max_bytes_before_encoding)
