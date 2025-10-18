"""Unit tests for capacity analyzer."""

import pytest
import os
import tempfile

from pdf_blind_watermark.steganography.capacity import CapacityAnalyzer, PageCapacity, PDFCapacity
from tests.generate_stego_test_pdf import create_text_pdf, create_minimal_pdf


class TestCapacityAnalyzer:
    """Test suite for CapacityAnalyzer."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def analyzer(self):
        """Create capacity analyzer instance."""
        return CapacityAnalyzer()

    @pytest.fixture
    def sample_pdf(self, temp_dir):
        """Create a sample PDF for testing."""
        pdf_path = os.path.join(temp_dir, "sample.pdf")
        create_text_pdf(pdf_path, num_pages=3, text_density="medium")
        return pdf_path

    def test_analyze_single_page(self, analyzer, temp_dir):
        """Test analyzing single page PDF."""
        pdf_path = os.path.join(temp_dir, "single.pdf")
        create_text_pdf(pdf_path, num_pages=1, text_density="medium")

        capacity = analyzer.analyze_pdf(pdf_path)

        assert capacity.total_pages == 1
        assert len(capacity.page_capacities) == 1
        assert capacity.total_available_positions > 0
        assert capacity.estimated_capacity_bytes > 0

    def test_analyze_multi_page(self, analyzer, sample_pdf):
        """Test analyzing multi-page PDF."""
        capacity = analyzer.analyze_pdf(sample_pdf)

        assert capacity.total_pages == 3
        assert len(capacity.page_capacities) == 3
        assert capacity.total_available_positions > 0

    def test_analyze_with_max_pages(self, analyzer, sample_pdf):
        """Test analyzing with page limit."""
        capacity = analyzer.analyze_pdf(sample_pdf, max_pages=2)

        assert capacity.total_pages == 2
        assert len(capacity.page_capacities) == 2

    def test_page_capacity_details(self, analyzer, sample_pdf):
        """Test page capacity details."""
        capacity = analyzer.analyze_pdf(sample_pdf)

        for i, page_cap in enumerate(capacity.page_capacities):
            assert page_cap.page_number == i
            assert page_cap.text_blocks >= 0
            assert page_cap.total_characters >= 0
            assert page_cap.available_positions >= 0

    def test_get_page_capacity(self, analyzer, sample_pdf):
        """Test getting specific page capacity."""
        capacity = analyzer.analyze_pdf(sample_pdf)

        page_0_cap = capacity.get_page_capacity(0)
        assert page_0_cap is not None
        assert page_0_cap.page_number == 0

        page_99_cap = capacity.get_page_capacity(99)
        assert page_99_cap is None

    def test_minimal_pdf_capacity(self, analyzer, temp_dir):
        """Test capacity of minimal PDF."""
        pdf_path = os.path.join(temp_dir, "minimal.pdf")
        create_minimal_pdf(pdf_path)

        capacity = analyzer.analyze_pdf(pdf_path)

        assert capacity.total_pages == 1
        assert capacity.total_available_positions >= 0
        assert capacity.estimated_capacity_bytes >= 0

    def test_high_density_pdf(self, analyzer, temp_dir):
        """Test capacity of high-density PDF."""
        pdf_path = os.path.join(temp_dir, "high_density.pdf")
        create_text_pdf(pdf_path, num_pages=2, text_density="high")

        capacity = analyzer.analyze_pdf(pdf_path)

        assert capacity.total_available_positions > 0
        assert capacity.estimated_capacity_bytes > 0

    def test_low_density_pdf(self, analyzer, temp_dir):
        """Test capacity of low-density PDF."""
        pdf_path = os.path.join(temp_dir, "low_density.pdf")
        create_text_pdf(pdf_path, num_pages=2, text_density="low")

        capacity = analyzer.analyze_pdf(pdf_path)

        assert capacity.total_pages == 2
        assert capacity.total_available_positions >= 0

    def test_check_capacity_sufficient(self, analyzer, sample_pdf):
        """Test capacity check with sufficient space."""
        has_capacity = analyzer.check_capacity(sample_pdf, data_size=100)
        assert has_capacity

    def test_check_capacity_insufficient(self, analyzer, temp_dir):
        """Test capacity check with insufficient space."""
        pdf_path = os.path.join(temp_dir, "tiny.pdf")
        create_minimal_pdf(pdf_path)

        has_capacity = analyzer.check_capacity(pdf_path, data_size=10000)
        assert not has_capacity

    def test_estimate_capacity_zero_positions(self, analyzer):
        """Test capacity estimation with zero positions."""
        estimated = analyzer._estimate_capacity(0)
        assert estimated == 0

    def test_estimate_capacity_small_positions(self, analyzer):
        """Test capacity estimation with small number of positions."""
        estimated = analyzer._estimate_capacity(100)
        assert estimated >= 0

    def test_estimate_capacity_large_positions(self, analyzer):
        """Test capacity estimation with large number of positions."""
        estimated = analyzer._estimate_capacity(10000)
        assert estimated > 0

    def test_capacity_increases_with_pages(self, analyzer, temp_dir):
        """Test that capacity increases with more pages."""
        capacities = []

        for num_pages in [1, 2, 5]:
            pdf_path = os.path.join(temp_dir, f"pdf_{num_pages}.pdf")
            create_text_pdf(pdf_path, num_pages=num_pages, text_density="medium")

            capacity = analyzer.analyze_pdf(pdf_path)
            capacities.append(capacity.estimated_capacity_bytes)

        assert capacities[0] < capacities[1] < capacities[2]

    def test_capacity_increases_with_density(self, analyzer, temp_dir):
        """Test that capacity increases with text density."""
        densities = ["low", "medium", "high"]
        capacities = []

        for density in densities:
            pdf_path = os.path.join(temp_dir, f"pdf_{density}.pdf")
            create_text_pdf(pdf_path, num_pages=1, text_density=density)

            capacity = analyzer.analyze_pdf(pdf_path)
            capacities.append(capacity.estimated_capacity_bytes)

        assert capacities[0] <= capacities[1] <= capacities[2]
