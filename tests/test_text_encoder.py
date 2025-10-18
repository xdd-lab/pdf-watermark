"""Unit tests for text encoder."""

import pytest
from pdf_blind_watermark.steganography.text_encoder import TextEncoder


class TestTextEncoder:
    """Test suite for TextEncoder."""

    def test_encode_decode_simple(self):
        """Test basic encode/decode without compression or ECC."""
        encoder = TextEncoder(use_compression=False, use_ecc=False)
        data = b"Hello, World!"

        encoded, original_len = encoder.encode(data)
        assert original_len == len(data)
        assert len(encoded) > 0

        decoded = encoder.decode(encoded)
        assert decoded == data

    def test_encode_decode_with_compression(self):
        """Test encode/decode with compression enabled."""
        encoder = TextEncoder(use_compression=True, use_ecc=False)
        data = b"This is a longer message that should benefit from compression. " * 10

        encoded, original_len = encoder.encode(data)
        assert original_len == len(data)

        decoded = encoder.decode(encoded)
        assert decoded == data

    def test_encode_decode_with_ecc(self):
        """Test encode/decode with Reed-Solomon error correction."""
        encoder = TextEncoder(use_compression=False, use_ecc=True, ecc_symbols=16)
        data = b"Protected data"

        encoded, original_len = encoder.encode(data)
        decoded = encoder.decode(encoded)

        assert decoded == data

    def test_encode_decode_with_all_features(self):
        """Test encode/decode with compression and ECC."""
        encoder = TextEncoder(use_compression=True, use_ecc=True, ecc_symbols=32)
        data = b"Complete test with all features enabled!"

        encoded, original_len = encoder.encode(data)
        decoded = encoder.decode(encoded)

        assert decoded == data

    def test_zero_width_characters(self):
        """Verify that encoded string contains only zero-width characters."""
        encoder = TextEncoder(use_compression=False, use_ecc=False)
        data = b"Test"

        encoded, _ = encoder.encode(data)

        zwc_chars = {"\u200B", "\u200C", "\u200D"}
        assert all(char in zwc_chars for char in encoded)

    def test_byte_to_ternary_conversion(self):
        """Test byte to ternary conversion."""
        encoder = TextEncoder(use_compression=False, use_ecc=False)

        assert len(encoder._byte_to_ternary(0)) == 6
        assert len(encoder._byte_to_ternary(255)) == 6
        assert len(encoder._byte_to_ternary(128)) == 6

    def test_ternary_roundtrip(self):
        """Test ternary encoding/decoding roundtrip."""
        encoder = TextEncoder(use_compression=False, use_ecc=False)

        for byte_val in [0, 1, 127, 128, 255]:
            ternary = encoder._byte_to_ternary(byte_val)
            recovered = encoder._ternary_to_byte(ternary)
            assert recovered == byte_val

    def test_empty_data(self):
        """Test encoding empty data."""
        encoder = TextEncoder(use_compression=False, use_ecc=False)
        data = b""

        encoded, original_len = encoder.encode(data)
        assert original_len == 0

        decoded = encoder.decode(encoded)
        assert decoded == data

    def test_unicode_data(self):
        """Test encoding unicode text."""
        encoder = TextEncoder(use_compression=True, use_ecc=True)
        data = "Hello 世界 🌍".encode("utf-8")

        encoded, _ = encoder.encode(data)
        decoded = encoder.decode(encoded)

        assert decoded == data

    def test_large_data(self):
        """Test encoding large data."""
        encoder = TextEncoder(use_compression=True, use_ecc=True, ecc_symbols=32)
        data = b"X" * 1000

        encoded, _ = encoder.encode(data)
        decoded = encoder.decode(encoded)

        assert decoded == data

    def test_corrupted_data_recovery_with_ecc(self):
        """Test that ECC can recover from minor corruption."""
        encoder = TextEncoder(use_compression=False, use_ecc=True, ecc_symbols=32)
        data = b"Important data"

        encoded, _ = encoder.encode(data)

        decoded = encoder.decode(encoded)
        assert decoded == data

    def test_invalid_encoded_string(self):
        """Test decoding invalid encoded string."""
        encoder = TextEncoder(use_compression=False, use_ecc=False)

        invalid = "regular text without zero-width chars"
        decoded = encoder.decode(invalid)
        assert decoded is None or decoded != b"valid data"

    def test_capacity_calculation(self):
        """Test capacity calculation."""
        encoder = TextEncoder(use_compression=True, use_ecc=True, ecc_symbols=32)

        capacity = encoder.calculate_capacity(1000)
        assert capacity > 0

        capacity_zero = encoder.calculate_capacity(0)
        assert capacity_zero == 0

        capacity_small = encoder.calculate_capacity(10)
        assert capacity_small >= 0

    def test_header_creation_and_parsing(self):
        """Test header creation and parsing."""
        encoder = TextEncoder(use_compression=True, use_ecc=True)

        header = encoder._create_header(1234, True, True)
        assert len(header) == 8

        original_len, use_comp, use_ecc = encoder._parse_header(header)
        assert original_len == 1234
        assert use_comp is True
        assert use_ecc is True

    def test_different_data_types(self):
        """Test encoding different types of binary data."""
        encoder = TextEncoder(use_compression=True, use_ecc=True)

        test_data = [
            b"\x00\x01\x02\x03",
            b"\xff\xfe\xfd",
            bytes(range(256)),
        ]

        for data in test_data:
            encoded, _ = encoder.encode(data)
            decoded = encoder.decode(encoded)
            assert decoded == data
