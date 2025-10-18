from __future__ import annotations

from pdf_blind_watermark.core.error_correction import ErrorCorrection


def test_error_correction_encode_decode():
    ecc = ErrorCorrection(ecc_symbols=16)
    data = b"Hello, World!"
    
    encoded = ecc.encode(data)
    assert len(encoded) == len(data) + 16
    
    decoded = ecc.decode(encoded)
    assert decoded == data


def test_error_correction_with_corruption():
    ecc = ErrorCorrection(ecc_symbols=32)
    data = b"Test message for error correction"
    
    encoded = ecc.encode(data)
    
    encoded_list = bytearray(encoded)
    encoded_list[10] ^= 0xFF
    encoded_list[20] ^= 0xFF
    encoded_list[30] ^= 0xFF
    corrupted = bytes(encoded_list)
    
    decoded = ecc.decode(corrupted)
    assert decoded == data


def test_error_correction_too_much_corruption():
    ecc = ErrorCorrection(ecc_symbols=16)
    data = b"Test"
    
    encoded = ecc.encode(data)
    
    encoded_list = bytearray(encoded)
    for i in range(0, len(encoded_list), 2):
        encoded_list[i] ^= 0xFF
    corrupted = bytes(encoded_list)
    
    decoded = ecc.decode(corrupted)
    assert decoded is None
