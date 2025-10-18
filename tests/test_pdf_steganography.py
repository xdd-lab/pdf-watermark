"""Integration tests for PDF text steganography."""

import pytest
import os
import tempfile
from pathlib import Path

from pdf_blind_watermark.steganography import PDFSteganography, StegoMetadata
from tests.generate_stego_test_pdf import create_text_pdf, create_minimal_pdf


class TestPDFSteganography:
    """Integration test suite for PDFSteganography."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def single_page_pdf(self, temp_dir):
        """Create a single-page test PDF."""
        pdf_path = os.path.join(temp_dir, "single_page.pdf")
        create_text_pdf(pdf_path, num_pages=1, text_density="medium")
        return pdf_path

    @pytest.fixture
    def multi_page_pdf(self, temp_dir):
        """Create a multi-page test PDF."""
        pdf_path = os.path.join(temp_dir, "multi_page.pdf")
        create_text_pdf(pdf_path, num_pages=3, text_density="medium")
        return pdf_path

    @pytest.fixture
    def minimal_pdf(self, temp_dir):
        """Create a minimal test PDF."""
        pdf_path = os.path.join(temp_dir, "minimal.pdf")
        create_minimal_pdf(pdf_path)
        return pdf_path

    @pytest.fixture
    def rich_pdf(self, temp_dir):
        """Create a rich text PDF."""
        pdf_path = os.path.join(temp_dir, "rich.pdf")
        create_text_pdf(pdf_path, num_pages=5, text_density="high")
        return pdf_path

    def test_embed_extract_single_page(self, single_page_pdf, temp_dir):
        """Test embedding and extracting from single-page PDF."""
        stego = PDFSteganography(use_compression=True, use_ecc=True)
        output_pdf = os.path.join(temp_dir, "output_single.pdf")

        metadata = StegoMetadata.create(
            user_id="user123",
            tracking_token="token456",
        )

        success = stego.embed(single_page_pdf, output_pdf, metadata)
        assert success
        assert os.path.exists(output_pdf)

        extracted = stego.extract(output_pdf)
        assert extracted is not None
        assert extracted.user_id == metadata.user_id
        assert extracted.tracking_token == metadata.tracking_token

    def test_embed_extract_multi_page(self, multi_page_pdf, temp_dir):
        """Test embedding and extracting from multi-page PDF."""
        stego = PDFSteganography(use_compression=True, use_ecc=True)
        output_pdf = os.path.join(temp_dir, "output_multi.pdf")

        metadata = StegoMetadata.create(
            user_id="multipage_user",
            tracking_token="multipage_token",
        )

        success = stego.embed(multi_page_pdf, output_pdf, metadata)
        assert success

        extracted = stego.extract(output_pdf)
        assert extracted is not None
        assert extracted.user_id == "multipage_user"
        assert extracted.tracking_token == "multipage_token"

    def test_embed_with_custom_fields(self, single_page_pdf, temp_dir):
        """Test embedding metadata with custom fields."""
        stego = PDFSteganography()
        output_pdf = os.path.join(temp_dir, "output_custom.pdf")

        custom_fields = {
            "department": "Engineering",
            "priority": "high",
            "version": "1.0",
        }

        metadata = StegoMetadata.create(
            user_id="user123",
            tracking_token="token456",
            custom_fields=custom_fields,
        )

        stego.embed(single_page_pdf, output_pdf, metadata)
        extracted = stego.extract(output_pdf)

        assert extracted is not None
        assert extracted.custom_fields == custom_fields

    def test_without_compression(self, single_page_pdf, temp_dir):
        """Test steganography without compression."""
        stego = PDFSteganography(use_compression=False, use_ecc=True)
        output_pdf = os.path.join(temp_dir, "output_no_comp.pdf")

        metadata = StegoMetadata.create(
            user_id="user_no_comp",
            tracking_token="token_no_comp",
        )

        stego.embed(single_page_pdf, output_pdf, metadata)
        extracted = stego.extract(output_pdf)

        assert extracted is not None
        assert extracted.user_id == "user_no_comp"

    def test_without_ecc(self, single_page_pdf, temp_dir):
        """Test steganography without error correction."""
        stego = PDFSteganography(use_compression=True, use_ecc=False)
        output_pdf = os.path.join(temp_dir, "output_no_ecc.pdf")

        metadata = StegoMetadata.create(
            user_id="user_no_ecc",
            tracking_token="token_no_ecc",
        )

        stego.embed(single_page_pdf, output_pdf, metadata)
        extracted = stego.extract(output_pdf)

        assert extracted is not None
        assert extracted.user_id == "user_no_ecc"

    def test_minimal_configuration(self, single_page_pdf, temp_dir):
        """Test with minimal configuration (no compression, no ECC)."""
        stego = PDFSteganography(use_compression=False, use_ecc=False)
        output_pdf = os.path.join(temp_dir, "output_minimal.pdf")

        metadata = StegoMetadata.create(
            user_id="minimal_user",
            tracking_token="minimal_token",
        )

        stego.embed(single_page_pdf, output_pdf, metadata)
        extracted = stego.extract(output_pdf)

        assert extracted is not None
        assert extracted.user_id == "minimal_user"

    def test_capacity_check_sufficient(self, single_page_pdf):
        """Test capacity check with sufficient space."""
        stego = PDFSteganography()

        metadata = StegoMetadata.create(
            user_id="user123",
            tracking_token="token456",
        )

        has_capacity = stego.check_capacity(single_page_pdf, metadata)
        assert has_capacity

    def test_capacity_info(self, multi_page_pdf):
        """Test getting capacity information."""
        stego = PDFSteganography()

        capacity_info = stego.get_capacity_info(multi_page_pdf)

        assert capacity_info.total_pages == 3
        assert capacity_info.total_available_positions > 0
        assert capacity_info.estimated_capacity_bytes > 0
        assert len(capacity_info.page_capacities) == 3

    def test_max_pages_limit(self, multi_page_pdf, temp_dir):
        """Test limiting the number of pages used."""
        stego = PDFSteganography()
        output_pdf = os.path.join(temp_dir, "output_limited.pdf")

        metadata = StegoMetadata.create(
            user_id="limited_user",
            tracking_token="limited_token",
        )

        stego.embed(multi_page_pdf, output_pdf, metadata, max_pages=2)
        extracted = stego.extract(output_pdf, max_pages=2)

        assert extracted is not None
        assert extracted.user_id == "limited_user"

    def test_unicode_metadata(self, single_page_pdf, temp_dir):
        """Test with unicode characters in metadata."""
        stego = PDFSteganography()
        output_pdf = os.path.join(temp_dir, "output_unicode.pdf")

        metadata = StegoMetadata.create(
            user_id="用户123",
            tracking_token="令牌456",
        )

        stego.embed(single_page_pdf, output_pdf, metadata)
        extracted = stego.extract(output_pdf)

        assert extracted is not None
        assert extracted.user_id == "用户123"
        assert extracted.tracking_token == "令牌456"

    def test_extract_from_unmodified_pdf(self, single_page_pdf):
        """Test extracting from PDF without embedded data."""
        stego = PDFSteganography()

        extracted = stego.extract(single_page_pdf)
        assert extracted is None

    def test_large_metadata(self, rich_pdf, temp_dir):
        """Test embedding large metadata."""
        stego = PDFSteganography()
        output_pdf = os.path.join(temp_dir, "output_large.pdf")

        large_custom = {
            f"field_{i}": f"value_{i}" * 10 for i in range(20)
        }

        metadata = StegoMetadata.create(
            user_id="user_large",
            tracking_token="token_large",
            custom_fields=large_custom,
        )

        success = stego.embed(rich_pdf, output_pdf, metadata)
        assert success

        extracted = stego.extract(output_pdf)
        assert extracted is not None
        assert extracted.user_id == "user_large"

    def test_different_ecc_symbols(self, single_page_pdf, temp_dir):
        """Test with different ECC symbol counts."""
        for ecc_symbols in [16, 32, 64]:
            stego = PDFSteganography(use_ecc=True, ecc_symbols=ecc_symbols)
            output_pdf = os.path.join(temp_dir, f"output_ecc_{ecc_symbols}.pdf")

            metadata = StegoMetadata.create(
                user_id=f"user_ecc{ecc_symbols}",
                tracking_token=f"token_ecc{ecc_symbols}",
            )

            stego.embed(single_page_pdf, output_pdf, metadata)
            extracted = stego.extract(output_pdf)

            assert extracted is not None
            assert extracted.user_id == f"user_ecc{ecc_symbols}"

    def test_roundtrip_accuracy(self, multi_page_pdf, temp_dir):
        """Test round-trip accuracy with multiple embed/extract cycles."""
        stego = PDFSteganography()

        for i in range(3):
            output_pdf = os.path.join(temp_dir, f"output_iter_{i}.pdf")

            metadata = StegoMetadata.create(
                user_id=f"user_iter_{i}",
                tracking_token=f"token_iter_{i}",
                timestamp=f"2024-01-0{i+1}T12:00:00",
            )

            stego.embed(multi_page_pdf, output_pdf, metadata)
            extracted = stego.extract(output_pdf)

            assert extracted is not None
            assert extracted.user_id == f"user_iter_{i}"
            assert extracted.tracking_token == f"token_iter_{i}"
            assert extracted.timestamp == f"2024-01-0{i+1}T12:00:00"

    def test_insufficient_capacity(self, minimal_pdf, temp_dir):
        """Test handling insufficient capacity."""
        stego = PDFSteganography()
        output_pdf = os.path.join(temp_dir, "output_overflow.pdf")

        huge_custom = {f"field_{i}": "x" * 1000 for i in range(100)}

        metadata = StegoMetadata.create(
            user_id="user_overflow",
            tracking_token="token_overflow",
            custom_fields=huge_custom,
        )

        with pytest.raises(ValueError, match="Insufficient capacity"):
            stego.embed(minimal_pdf, output_pdf, metadata)

    def test_page_capacity_details(self, multi_page_pdf):
        """Test detailed page capacity information."""
        stego = PDFSteganography()
        capacity = stego.get_capacity_info(multi_page_pdf)

        for i, page_cap in enumerate(capacity.page_capacities):
            assert page_cap.page_number == i
            assert page_cap.text_blocks >= 0
            assert page_cap.total_characters >= 0
            assert page_cap.available_positions >= 0
