from __future__ import annotations

from typing import Optional

try:
    import reedsolo
except ImportError:
    reedsolo = None


class ErrorCorrection:
    """Wrapper for Reed-Solomon error correction."""

    def __init__(self, ecc_symbols: int = 32):
        """
        Initialize error correction.

        Args:
            ecc_symbols: Number of error correction symbols (more = better correction).
        """
        self.ecc_symbols = ecc_symbols
        if reedsolo is None:
            raise ImportError(
                "reedsolo is required for error correction. "
                "Install it with: pip install reedsolo"
            )
        self.rs = reedsolo.RSCodec(ecc_symbols)
        # By design, RSCodec over GF(2^8) works on chunks of size <= 255 - ecc_symbols.
        self.max_data_length = 255 - ecc_symbols

    def encode(self, data: bytes) -> bytes:
        """Add error correction to data."""
        if len(data) > self.max_data_length:
            raise ValueError(
                f"Data too long for the configured ECC. Maximum length is {self.max_data_length} bytes."
            )
        return bytes(self.rs.encode(data))

    def decode(self, data: bytes) -> Optional[bytes]:
        """Decode and correct errors in data."""
        try:
            decoded = self.rs.decode(data)
            return bytes(decoded)
        except (reedsolo.ReedSolomonError, Exception):
            return None


class SimpleChecksum:
    """Simple checksum-based error detection (no correction)."""

    def __init__(self):
        pass

    def encode(self, data: bytes) -> bytes:
        """Add simple checksum to data."""
        checksum = sum(data) % 256
        return data + bytes([checksum])

    def decode(self, data: bytes) -> Optional[bytes]:
        """Verify checksum and return original data."""
        if len(data) < 1:
            return None
        payload = data[:-1]
        expected_checksum = sum(payload) % 256
        actual_checksum = data[-1]
        if expected_checksum == actual_checksum:
            return payload
        return None
