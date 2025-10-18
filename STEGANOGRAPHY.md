# PDF Text Steganography Module

## Overview

The PDF Text Steganography module provides a robust solution for embedding invisible structured metadata (user ID, timestamp, tracking tokens) inside PDF documents using zero-width characters and invisible text spans. The module leverages PyMuPDF for PDF manipulation and includes optional compression and Reed-Solomon error correction for enhanced reliability.

## Features

- ✅ **Invisible Embedding**: Uses zero-width Unicode characters (ZWSP, ZWJ, ZWNJ) for steganographic encoding
- ✅ **Structured Metadata**: Support for user ID, timestamp, tracking token, and custom fields
- ✅ **Optional Compression**: zlib compression to reduce metadata size
- ✅ **Error Correction**: Reed-Solomon error correction for robustness against document edits
- ✅ **Multi-page Support**: Distribute metadata across multiple pages for better capacity
- ✅ **Capacity Analysis**: Check PDF capacity before embedding
- ✅ **Round-trip Validation**: Accurate extraction with error detection

## Installation

The steganography module is included in the main package:

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from pdf_blind_watermark import PDFSteganography, StegoMetadata

# Initialize steganography engine
stego = PDFSteganography(
    use_compression=True,
    use_ecc=True,
    ecc_symbols=32
)

# Create metadata
metadata = StegoMetadata.create(
    user_id="user_12345",
    tracking_token="abc123xyz789"
)

# Embed metadata
stego.embed(
    input_pdf="original.pdf",
    output_pdf="tracked.pdf",
    metadata=metadata
)

# Extract metadata
extracted = stego.extract("tracked.pdf")
print(f"User: {extracted.user_id}")
print(f"Token: {extracted.tracking_token}")
print(f"Timestamp: {extracted.timestamp}")
```

### Capacity Checking

```python
# Check if PDF has sufficient capacity
has_capacity = stego.check_capacity("document.pdf", metadata)

if has_capacity:
    stego.embed("document.pdf", "output.pdf", metadata)
else:
    print("Insufficient capacity")

# Get detailed capacity information
capacity = stego.get_capacity_info("document.pdf")
print(f"Total pages: {capacity.total_pages}")
print(f"Estimated capacity: {capacity.estimated_capacity_bytes} bytes")
```

### Multi-page PDFs

```python
# Embed using only first 3 pages
stego.embed(
    input_pdf="large_doc.pdf",
    output_pdf="output.pdf",
    metadata=metadata,
    max_pages=3
)

# Extract from first 3 pages
extracted = stego.extract("output.pdf", max_pages=3)
```

### Custom Metadata Fields

```python
metadata = StegoMetadata.create(
    user_id="user_001",
    tracking_token="token_xyz",
    custom_fields={
        "department": "Engineering",
        "project": "Alpha",
        "classification": "Confidential",
        "version": "1.0"
    }
)

stego.embed("input.pdf", "output.pdf", metadata)
```

## API Reference

### PDFSteganography

Main class for PDF text steganography operations.

#### Constructor

```python
PDFSteganography(
    use_compression: bool = True,
    use_ecc: bool = True,
    ecc_symbols: int = 32
)
```

**Parameters:**
- `use_compression`: Enable zlib compression (reduces metadata size)
- `use_ecc`: Enable Reed-Solomon error correction
- `ecc_symbols`: Number of error correction symbols (more = better correction, but larger overhead)

#### Methods

##### embed()

```python
embed(
    input_pdf: str,
    output_pdf: str,
    metadata: StegoMetadata,
    max_pages: Optional[int] = None
) -> bool
```

Embed metadata into PDF.

**Parameters:**
- `input_pdf`: Path to input PDF file
- `output_pdf`: Path to output PDF file
- `metadata`: StegoMetadata object to embed
- `max_pages`: Maximum number of pages to use (None = all pages)

**Returns:** True if successful

**Raises:** ValueError if insufficient capacity

##### extract()

```python
extract(
    input_pdf: str,
    max_pages: Optional[int] = None
) -> Optional[StegoMetadata]
```

Extract metadata from PDF.

**Parameters:**
- `input_pdf`: Path to input PDF file
- `max_pages`: Maximum number of pages to read (None = all pages)

**Returns:** StegoMetadata object or None if extraction fails

##### check_capacity()

```python
check_capacity(
    pdf_path: str,
    metadata: StegoMetadata,
    max_pages: Optional[int] = None
) -> bool
```

Check if PDF has sufficient capacity for metadata.

##### get_capacity_info()

```python
get_capacity_info(
    pdf_path: str,
    max_pages: Optional[int] = None
) -> PDFCapacity
```

Get detailed capacity information for PDF.

### StegoMetadata

Data class representing structured metadata.

#### Constructor

```python
StegoMetadata(
    user_id: str,
    timestamp: str,
    tracking_token: str,
    custom_fields: Optional[Dict[str, Any]] = None
)
```

#### Class Methods

##### create()

```python
@classmethod
create(
    user_id: str,
    tracking_token: str,
    timestamp: Optional[str] = None,
    custom_fields: Optional[Dict[str, Any]] = None
) -> StegoMetadata
```

Create metadata with optional auto-generated timestamp.

#### Methods

- `to_json() -> str`: Convert to JSON string
- `from_json(json_str: str) -> StegoMetadata`: Create from JSON string
- `to_bytes() -> bytes`: Convert to bytes
- `from_bytes(data: bytes) -> StegoMetadata`: Create from bytes

## Technical Details

### Encoding Method

The module uses **ternary encoding** with zero-width Unicode characters:

- `\u200B` (Zero-Width Space) = 0
- `\u200C` (Zero-Width Non-Joiner) = 1
- `\u200D` (Zero-Width Joiner) = 2

Each byte is converted to 6 ternary digits (3^6 = 729 > 256), allowing efficient encoding.

### Data Format

```
[Header: 8 bytes]
  - Original length: 4 bytes
  - Flags: 1 byte (compression, ECC)
  - Reserved: 3 bytes
[Encoded data]
```

### Error Correction

Reed-Solomon error correction over GF(2^8) with configurable symbol count:

- **16 symbols**: Corrects up to 8 byte errors (lightweight)
- **32 symbols**: Corrects up to 16 byte errors (balanced, default)
- **64 symbols**: Corrects up to 32 byte errors (robust)

### Compression

Uses zlib compression at level 9 for optimal size reduction. Typically achieves 40-60% compression for JSON metadata.

### Capacity Estimation

Capacity depends on:
- Number of text characters in PDF
- ECC overhead (varies with ecc_symbols)
- Compression ratio (typically 0.6)
- Encoding overhead (6 ZWC per byte)

Formula:
```
capacity ≈ (positions / 6 - 8) / 1.3 * 0.6
```

Where:
- positions = total character count in PDF
- 6 = positions per byte (ternary encoding)
- 8 = header overhead bytes
- 1.3 = ECC overhead factor
- 0.6 = compression gain factor

## Usage Scenarios

### Document Tracking

Track document distribution and leaks:

```python
metadata = StegoMetadata.create(
    user_id="employee_id_789",
    tracking_token="distribution_batch_2024_q1",
    custom_fields={
        "document_id": "DOC-2024-001",
        "access_level": "confidential",
        "department": "Legal"
    }
)
```

### Watermarking

Invisible watermarking for copyright protection:

```python
metadata = StegoMetadata.create(
    user_id="copyright_owner",
    tracking_token="watermark_v1",
    custom_fields={
        "copyright": "© 2024 Company Inc.",
        "license": "All rights reserved"
    }
)
```

### Audit Trail

Create an audit trail for document access:

```python
metadata = StegoMetadata.create(
    user_id=f"access_{session_id}",
    tracking_token=access_token,
    custom_fields={
        "access_time": datetime.now().isoformat(),
        "ip_address": request_ip,
        "action": "download"
    }
)
```

## Best Practices

1. **Always check capacity** before embedding large metadata
2. **Use compression** for larger metadata structures
3. **Enable ECC** for documents that may be edited
4. **Test extraction** immediately after embedding to verify
5. **Store metadata size limits** appropriate to your use case
6. **Use meaningful tracking tokens** for later identification
7. **Consider multi-page distribution** for large documents

## Limitations

- Requires text content in PDF (doesn't work with image-only PDFs)
- Capacity limited by amount of text in document
- Invisible characters may be lost in some PDF editing operations
- Not resistant to full text extraction and reflow
- Should not be used as sole security mechanism

## Performance

Typical performance on modern hardware:

| Operation | Single Page | Multi-Page (3 pages) |
|-----------|-------------|---------------------|
| Embed     | ~0.1-0.3s   | ~0.3-0.8s          |
| Extract   | ~0.1-0.2s   | ~0.2-0.5s          |
| Capacity  | ~0.05s      | ~0.1-0.2s          |

## Examples

See `examples/steganography_example.py` for comprehensive usage examples including:
- Basic embedding and extraction
- Capacity checking
- Multi-page handling
- Advanced metadata structures
- Error correction configurations
- Compression comparisons

## Testing

Run the test suite:

```bash
# All steganography tests
pytest tests/test_text_encoder.py
pytest tests/test_metadata.py
pytest tests/test_capacity.py
pytest tests/test_pdf_steganography.py

# Specific test
pytest tests/test_pdf_steganography.py::TestPDFSteganography::test_embed_extract_single_page -v
```

## Troubleshooting

### Insufficient Capacity Error

**Problem:** `ValueError: Insufficient capacity`

**Solutions:**
1. Use compression: `use_compression=True`
2. Reduce metadata size
3. Use more pages: increase or remove `max_pages` limit
4. Reduce ECC symbols: use `ecc_symbols=16` instead of 32

### Extraction Returns None

**Problem:** `extract()` returns None

**Possible causes:**
1. No metadata was embedded
2. PDF was heavily edited
3. Wrong page range specified
4. Text was removed or altered

**Solutions:**
1. Verify embedding was successful
2. Enable ECC for better resilience
3. Check capacity before embedding
4. Use higher ECC symbol count

### Unicode Encoding Errors

**Problem:** Errors with non-ASCII characters

**Solution:** Ensure UTF-8 encoding is used (default in module)

## License

MIT License - See LICENSE file for details.
