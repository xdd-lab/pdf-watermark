from __future__ import annotations

import math
from typing import Iterable, List


PREAMBLE = b"\xAA\x55\xAA\x55"


def bytes_to_bits(data: bytes) -> List[int]:
    """Convert bytes to a list of bits (MSB first)."""
    bits: List[int] = []
    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def bits_to_bytes(bits: Iterable[int]) -> bytes:
    """Convert iterable of bits (MSB first) into bytes."""
    bit_list = list(bits)
    length = len(bit_list)
    if length % 8 != 0:
        padding = 8 - (length % 8)
        bit_list.extend([0] * padding)
    output = bytearray()
    for i in range(0, len(bit_list), 8):
        value = 0
        for bit in bit_list[i : i + 8]:
            value = (value << 1) | (bit & 1)
        output.append(value)
    return bytes(output)


def encode_text(text: str, encoding: str = "utf-8") -> bytes:
    return text.encode(encoding)


def decode_text(data: bytes, encoding: str = "utf-8") -> str:
    return data.decode(encoding)


def chunk_bytes(data: bytes, size: int) -> List[bytes]:
    return [data[i : i + size] for i in range(0, len(data), size)]


def find_preamble(data: bytes, preamble: bytes = PREAMBLE) -> int:
    """Find the first occurrence of the preamble.

    Returns the index of the preamble or -1 if not found.
    """
    return data.find(preamble)


def ceil_div(a: int, b: int) -> int:
    return int(math.ceil(a / b))
