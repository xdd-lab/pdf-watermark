"""
Example usage of PDF text steganography module.

This example demonstrates how to:
1. Check PDF capacity
2. Embed structured metadata
3. Extract and verify metadata
4. Handle multi-page PDFs
"""

from pdf_blind_watermark import PDFSteganography, StegoMetadata


def basic_example():
    """Basic embedding and extraction example."""
    print("=== Basic Steganography Example ===\n")

    stego = PDFSteganography(
        use_compression=True,
        use_ecc=True,
        ecc_symbols=32
    )

    metadata = StegoMetadata.create(
        user_id="user_12345",
        tracking_token="abc123xyz789",
    )

    print(f"Created metadata:")
    print(f"  User ID: {metadata.user_id}")
    print(f"  Tracking Token: {metadata.tracking_token}")
    print(f"  Timestamp: {metadata.timestamp}\n")

    print("Embedding metadata into PDF...")
    stego.embed(
        input_pdf="input.pdf",
        output_pdf="output_with_stego.pdf",
        metadata=metadata
    )
    print("✓ Embedding complete\n")

    print("Extracting metadata from PDF...")
    extracted = stego.extract("output_with_stego.pdf")

    if extracted:
        print("✓ Extraction successful!")
        print(f"  User ID: {extracted.user_id}")
        print(f"  Tracking Token: {extracted.tracking_token}")
        print(f"  Timestamp: {extracted.timestamp}")
    else:
        print("✗ Extraction failed")


def capacity_check_example():
    """Example of checking PDF capacity before embedding."""
    print("\n=== Capacity Check Example ===\n")

    stego = PDFSteganography()

    metadata = StegoMetadata.create(
        user_id="user_12345",
        tracking_token="abc123xyz789",
        custom_fields={
            "department": "Engineering",
            "project": "Alpha",
            "classification": "Confidential"
        }
    )

    pdf_path = "document.pdf"

    print("Checking PDF capacity...")
    capacity_info = stego.get_capacity_info(pdf_path)

    print(f"\nPDF Capacity Analysis:")
    print(f"  Total pages: {capacity_info.total_pages}")
    print(f"  Total positions: {capacity_info.total_available_positions:,}")
    print(f"  Estimated capacity: {capacity_info.estimated_capacity_bytes} bytes")

    print(f"\nPer-page breakdown:")
    for page_cap in capacity_info.page_capacities[:3]:
        print(f"  Page {page_cap.page_number}: "
              f"{page_cap.total_characters} chars, "
              f"{page_cap.text_blocks} blocks")

    has_capacity = stego.check_capacity(pdf_path, metadata)
    if has_capacity:
        print("\n✓ PDF has sufficient capacity for metadata")
    else:
        print("\n✗ PDF does not have sufficient capacity")


def multi_page_example():
    """Example with multi-page PDF."""
    print("\n=== Multi-Page PDF Example ===\n")

    stego = PDFSteganography()

    metadata = StegoMetadata.create(
        user_id="multi_user_789",
        tracking_token="multi_token_456",
    )

    print("Embedding in first 3 pages only...")
    stego.embed(
        input_pdf="large_document.pdf",
        output_pdf="output_multi.pdf",
        metadata=metadata,
        max_pages=3
    )
    print("✓ Embedded\n")

    print("Extracting from first 3 pages...")
    extracted = stego.extract("output_multi.pdf", max_pages=3)

    if extracted:
        print("✓ Successfully extracted from multi-page PDF")
        print(f"  User ID: {extracted.user_id}")


def advanced_metadata_example():
    """Example with complex metadata."""
    print("\n=== Advanced Metadata Example ===\n")

    stego = PDFSteganography(
        use_compression=True,
        use_ecc=True,
        ecc_symbols=64
    )

    metadata = StegoMetadata.create(
        user_id="advanced_user_001",
        tracking_token="secure_token_xyz",
        custom_fields={
            "document_type": "contract",
            "version": "2.1",
            "department": "Legal",
            "confidentiality_level": "high",
            "expiry_date": "2025-12-31",
            "authorized_viewers": ["user1", "user2", "user3"],
            "metadata_version": "1.0",
            "checksum": "sha256:abc123...",
        }
    )

    print("Metadata to embed:")
    print(f"  User ID: {metadata.user_id}")
    print(f"  Tracking Token: {metadata.tracking_token}")
    print(f"  Custom fields: {len(metadata.custom_fields)} items")

    stego.embed(
        input_pdf="contract.pdf",
        output_pdf="contract_tracked.pdf",
        metadata=metadata
    )
    print("\n✓ Advanced metadata embedded")

    extracted = stego.extract("contract_tracked.pdf")
    if extracted and extracted.custom_fields:
        print("\n✓ Extracted custom fields:")
        for key, value in extracted.custom_fields.items():
            print(f"  {key}: {value}")


def error_correction_example():
    """Example demonstrating error correction settings."""
    print("\n=== Error Correction Example ===\n")

    configurations = [
        ("No ECC", False, 16),
        ("Low ECC", True, 16),
        ("Medium ECC", True, 32),
        ("High ECC", True, 64),
    ]

    metadata = StegoMetadata.create(
        user_id="ecc_test_user",
        tracking_token="ecc_test_token",
    )

    for name, use_ecc, ecc_symbols in configurations:
        print(f"\nTesting {name} (ecc_symbols={ecc_symbols})...")

        stego = PDFSteganography(
            use_compression=True,
            use_ecc=use_ecc,
            ecc_symbols=ecc_symbols if use_ecc else 32
        )

        output_file = f"output_{name.lower().replace(' ', '_')}.pdf"

        stego.embed("input.pdf", output_file, metadata)
        extracted = stego.extract(output_file)

        if extracted and extracted.user_id == metadata.user_id:
            print(f"  ✓ Success with {name}")
        else:
            print(f"  ✗ Failed with {name}")


def compression_comparison():
    """Compare with and without compression."""
    print("\n=== Compression Comparison ===\n")

    large_metadata = StegoMetadata.create(
        user_id="compression_test",
        tracking_token="comp_token" * 10,
        custom_fields={f"field_{i}": f"value_{i}" * 5 for i in range(20)}
    )

    for use_compression in [False, True]:
        mode = "WITH" if use_compression else "WITHOUT"
        print(f"\n{mode} compression:")

        stego = PDFSteganography(
            use_compression=use_compression,
            use_ecc=True
        )

        try:
            stego.embed(
                "input.pdf",
                f"output_{'comp' if use_compression else 'no_comp'}.pdf",
                large_metadata
            )
            print(f"  ✓ Successfully embedded large metadata")
        except ValueError as e:
            print(f"  ✗ Failed: {e}")


if __name__ == "__main__":
    print("PDF Text Steganography Examples")
    print("=" * 50)

    print("\nNote: Make sure you have 'input.pdf' in the current directory")
    print("or modify the file paths in the examples.\n")

    basic_example()
