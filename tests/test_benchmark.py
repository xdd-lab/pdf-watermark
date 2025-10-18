from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pdf_blind_watermark.benchmark.attacks import AttackSimulator, AttackType
from pdf_blind_watermark.benchmark.metrics import MetricsCalculator
from pdf_blind_watermark.benchmark.runner import BenchmarkRunner
from pdf_blind_watermark.benchmark.sample_generator import SampleGenerator
from pdf_blind_watermark.core.watermark import WatermarkConfig


@pytest.fixture
def test_image():
    """Create a simple test image."""
    x = np.linspace(0, 255, 512, dtype=np.uint8)
    gradient = np.tile(x, (512, 1))
    image = np.stack([gradient, gradient, gradient], axis=2)
    return Image.fromarray(image, mode="RGB")


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestSampleGenerator:
    """Test sample generation utilities."""

    def test_generate_gradient_image(self):
        generator = SampleGenerator()
        image = generator.generate_gradient_image(width=512, height=512, orientation="horizontal")
        assert image.size == (512, 512)
        assert image.mode == "RGB"

    def test_generate_text_document(self):
        generator = SampleGenerator()
        image = generator.generate_text_document(width=800, height=600)
        assert image.size == (800, 600)
        assert image.mode == "RGB"

    def test_generate_mixed_content(self):
        generator = SampleGenerator()
        image = generator.generate_mixed_content(width=800, height=600, complexity="medium")
        assert image.size == (800, 600)
        assert image.mode == "RGB"

    def test_generate_noise_pattern(self):
        generator = SampleGenerator()
        image = generator.generate_noise_pattern(width=512, height=512, noise_type="gaussian")
        assert image.size == (512, 512)
        assert image.mode == "RGB"


class TestAttackSimulator:
    """Test attack simulation functions."""

    def test_jpeg_compression(self, test_image):
        attacked = AttackSimulator.jpeg_compression(test_image, quality=50)
        assert attacked.size == test_image.size
        assert attacked.mode == "RGB"

    def test_scale_down(self, test_image):
        attacked = AttackSimulator.scale_down(test_image, scale_factor=0.5)
        assert attacked.size == (256, 256)

    def test_scale_up(self, test_image):
        attacked = AttackSimulator.scale_up(test_image, scale_factor=2.0)
        assert attacked.size == (1024, 1024)

    def test_rotation(self, test_image):
        attacked = AttackSimulator.rotation(test_image, angle=5.0)
        assert attacked.size == test_image.size
        assert attacked.mode == "RGB"

    def test_crop(self, test_image):
        attacked = AttackSimulator.crop(test_image, crop_ratio=0.1)
        # Crop removes crop_ratio from each side, so remaining is 1 - 2*crop_ratio
        # 512 - 2*(512*0.1) = 512 - 102.4 = 409.6 -> rounds to 410
        assert attacked.width < test_image.width
        assert attacked.height < test_image.height

    def test_gaussian_noise(self, test_image):
        attacked = AttackSimulator.gaussian_noise(test_image, sigma=10.0)
        assert attacked.size == test_image.size
        assert attacked.mode == "RGB"

    def test_salt_pepper_noise(self, test_image):
        attacked = AttackSimulator.salt_pepper_noise(test_image, probability=0.01)
        assert attacked.size == test_image.size
        assert attacked.mode == "RGB"

    def test_gaussian_blur(self, test_image):
        attacked = AttackSimulator.gaussian_blur(test_image, radius=2.0)
        assert attacked.size == test_image.size
        assert attacked.mode == "RGB"

    def test_screenshot_simulation(self, test_image):
        attacked = AttackSimulator.screenshot_simulation(test_image)
        assert attacked.size == test_image.size
        assert attacked.mode == "RGB"

    def test_brightness_change(self, test_image):
        attacked = AttackSimulator.brightness_change(test_image, factor=1.2)
        assert attacked.size == test_image.size
        assert attacked.mode == "RGB"

    def test_contrast_change(self, test_image):
        attacked = AttackSimulator.contrast_change(test_image, factor=1.2)
        assert attacked.size == test_image.size
        assert attacked.mode == "RGB"


class TestMetricsCalculator:
    """Test metrics calculation functions."""

    def test_calculate_psnr_identical(self, test_image):
        psnr = MetricsCalculator.calculate_psnr(test_image, test_image)
        assert psnr == float("inf")

    def test_calculate_psnr_different(self, test_image):
        noisy = AttackSimulator.gaussian_noise(test_image, sigma=10.0)
        psnr = MetricsCalculator.calculate_psnr(test_image, noisy)
        assert 0 < psnr < 100

    def test_calculate_ssim_identical(self, test_image):
        ssim = MetricsCalculator.calculate_ssim(test_image, test_image)
        assert 0.99 <= ssim <= 1.0

    def test_calculate_ssim_different(self, test_image):
        noisy = AttackSimulator.gaussian_noise(test_image, sigma=10.0)
        ssim = MetricsCalculator.calculate_ssim(test_image, noisy)
        assert 0 < ssim < 1.0

    def test_calculate_bit_error_rate_identical(self):
        text = "TEST-WATERMARK"
        ber = MetricsCalculator.calculate_bit_error_rate(text, text)
        assert ber == 0.0

    def test_calculate_bit_error_rate_different(self):
        expected = "TEST-WATERMARK"
        extracted = "TEST-WATERM4RK"
        ber = MetricsCalculator.calculate_bit_error_rate(expected, extracted)
        assert 0 < ber < 1.0


class TestBenchmarkRunner:
    """Test benchmark runner functionality."""

    def test_single_benchmark_success(self, test_image, temp_output_dir):
        config = WatermarkConfig(embed_strength=14.0)
        runner = BenchmarkRunner(config=config, output_dir=temp_output_dir)

        watermark_text = "TEST-BENCHMARK"
        attack_func = AttackSimulator.jpeg_compression
        attack_params = {"quality": 75}
        attack_description = "JPEG Q75"

        metrics = runner.run_single_benchmark(
            test_image, watermark_text, attack_func, attack_params, attack_description
        )

        assert metrics is not None
        assert metrics.attack_type == "jpeg_compression"
        assert metrics.psnr is not None
        assert metrics.ssim is not None

    def test_quick_benchmark(self, temp_output_dir):
        config = WatermarkConfig(embed_strength=14.0)
        runner = BenchmarkRunner(config=config, output_dir=temp_output_dir)

        aggregated = runner.run_quick_benchmark(
            watermark_text="QUICK-TEST", save_results=False
        )

        assert aggregated.total_runs > 0
        assert 0 <= aggregated.success_rate <= 1.0
        assert aggregated.avg_psnr is not None
        assert aggregated.avg_ssim is not None

    def test_benchmark_suite_specific_attacks(self, test_image, temp_output_dir):
        config = WatermarkConfig(embed_strength=14.0)
        runner = BenchmarkRunner(config=config, output_dir=temp_output_dir)

        attack_types = [AttackType.JPEG_COMPRESSION, AttackType.GAUSSIAN_NOISE]
        metrics = runner.run_benchmark_suite(
            test_image, watermark_text="TEST", attack_types=attack_types, verbose=False
        )

        assert len(metrics) > 0
        attack_names = {m.attack_type for m in metrics}
        assert "jpeg_compression" in attack_names or "gaussian_noise" in attack_names

    def test_save_results_json(self, test_image, temp_output_dir):
        config = WatermarkConfig(embed_strength=14.0)
        runner = BenchmarkRunner(config=config, output_dir=temp_output_dir)

        attack_types = [AttackType.JPEG_COMPRESSION]
        metrics = runner.run_benchmark_suite(
            test_image, watermark_text="TEST", attack_types=attack_types, verbose=False
        )

        runner.save_results_json(metrics, "test_results.json")
        output_file = Path(temp_output_dir) / "test_results.json"
        assert output_file.exists()

    def test_save_results_csv(self, test_image, temp_output_dir):
        config = WatermarkConfig(embed_strength=14.0)
        runner = BenchmarkRunner(config=config, output_dir=temp_output_dir)

        attack_types = [AttackType.JPEG_COMPRESSION]
        metrics = runner.run_benchmark_suite(
            test_image, watermark_text="TEST", attack_types=attack_types, verbose=False
        )

        runner.save_results_csv(metrics, "test_results.csv")
        output_file = Path(temp_output_dir) / "test_results.csv"
        assert output_file.exists()

    def test_save_aggregated_report(self, test_image, temp_output_dir):
        config = WatermarkConfig(embed_strength=14.0)
        runner = BenchmarkRunner(config=config, output_dir=temp_output_dir)

        attack_types = [AttackType.JPEG_COMPRESSION]
        metrics = runner.run_benchmark_suite(
            test_image, watermark_text="TEST", attack_types=attack_types, verbose=False
        )

        runner.save_aggregated_report(metrics, "test_report.txt")
        output_file = Path(temp_output_dir) / "test_report.txt"
        assert output_file.exists()


def test_benchmark_workflow_integration(temp_output_dir):
    """Integration test for the complete benchmark workflow."""
    generator = SampleGenerator()
    image = generator.generate_text_document(width=800, height=600)

    config = WatermarkConfig(embed_strength=14.0)
    runner = BenchmarkRunner(config=config, output_dir=temp_output_dir)

    attack_types = [AttackType.JPEG_COMPRESSION, AttackType.SCALE_DOWN]
    metrics = runner.run_benchmark_suite(
        image, watermark_text="INTEGRATION-TEST", attack_types=attack_types, verbose=False
    )

    assert len(metrics) > 0

    runner.save_results_json(metrics)
    runner.save_results_csv(metrics)
    runner.save_aggregated_report(metrics)

    assert (Path(temp_output_dir) / "benchmark_results.json").exists()
    assert (Path(temp_output_dir) / "benchmark_results.csv").exists()
    assert (Path(temp_output_dir) / "benchmark_report.txt").exists()

    aggregated = MetricsCalculator.aggregate_metrics(metrics)
    assert aggregated.total_runs == len(metrics)
    assert 0 <= aggregated.success_rate <= 1.0
