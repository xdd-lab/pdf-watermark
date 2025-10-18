from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image
from tqdm import tqdm

from ..core.watermark import PDFWatermarker, WatermarkConfig, WatermarkingError
from .attacks import AttackSimulator, AttackType
from .metrics import AggregatedMetrics, BenchmarkMetrics, MetricsCalculator
from .sample_generator import SampleGenerator


class BenchmarkRunner:
    """Run comprehensive robustness and invisibility benchmarks."""

    def __init__(
        self,
        config: Optional[WatermarkConfig] = None,
        output_dir: str = "./benchmark_results",
    ):
        """Initialize benchmark runner.

        Args:
            config: Watermark configuration
            output_dir: Directory to save results
        """
        self.config = config or WatermarkConfig(embed_strength=12.0)
        self.watermarker = PDFWatermarker(self.config)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.attack_simulator = AttackSimulator()
        self.metrics_calculator = MetricsCalculator()
        self.sample_generator = SampleGenerator()

    def run_single_benchmark(
        self,
        image: Image.Image,
        watermark_text: str,
        attack_func: callable,
        attack_params: dict,
        attack_description: str,
    ) -> BenchmarkMetrics:
        """Run a single benchmark with one attack.

        Args:
            image: Original image
            watermark_text: Watermark text to embed
            attack_func: Attack function to apply
            attack_params: Parameters for the attack
            attack_description: Human-readable description

        Returns:
            BenchmarkMetrics with results
        """
        try:
            watermarked_image = self.watermarker.embed_image(image, watermark_text)
        except Exception as e:
            return BenchmarkMetrics(
                attack_type=attack_func.__name__,
                attack_params=attack_description,
                success=False,
                error_message=f"Embedding failed: {str(e)}",
            )

        psnr = self.metrics_calculator.calculate_psnr(image, watermarked_image)
        ssim = self.metrics_calculator.calculate_ssim(image, watermarked_image)

        try:
            attacked_image = attack_func(watermarked_image, **attack_params)
        except Exception as e:
            return BenchmarkMetrics(
                attack_type=attack_func.__name__,
                attack_params=attack_description,
                success=False,
                psnr=psnr,
                ssim=ssim,
                error_message=f"Attack failed: {str(e)}",
            )

        start_time = time.time()
        try:
            extracted_text = self.watermarker.extract_from_image(attacked_image)
            extraction_time = time.time() - start_time

            success = extracted_text == watermark_text
            ber = (
                self.metrics_calculator.calculate_bit_error_rate(watermark_text, extracted_text)
                if extracted_text
                else 1.0
            )

            return BenchmarkMetrics(
                attack_type=attack_func.__name__,
                attack_params=attack_description,
                success=success,
                extracted_text=extracted_text,
                expected_text=watermark_text,
                bit_error_rate=ber,
                psnr=psnr,
                ssim=ssim,
                extraction_time=extraction_time,
            )
        except WatermarkingError as e:
            extraction_time = time.time() - start_time
            return BenchmarkMetrics(
                attack_type=attack_func.__name__,
                attack_params=attack_description,
                success=False,
                expected_text=watermark_text,
                psnr=psnr,
                ssim=ssim,
                extraction_time=extraction_time,
                error_message=str(e),
            )
        except Exception as e:
            extraction_time = time.time() - start_time
            return BenchmarkMetrics(
                attack_type=attack_func.__name__,
                attack_params=attack_description,
                success=False,
                expected_text=watermark_text,
                psnr=psnr,
                ssim=ssim,
                extraction_time=extraction_time,
                error_message=f"Unexpected error: {str(e)}",
            )

    def run_benchmark_suite(
        self,
        image: Image.Image,
        watermark_text: str = "BENCHMARK-TEST-2024",
        attack_types: Optional[List[AttackType]] = None,
        verbose: bool = True,
    ) -> List[BenchmarkMetrics]:
        """Run a full benchmark suite on an image.

        Args:
            image: Test image
            watermark_text: Watermark text to use
            attack_types: List of attack types to test (None = all)
            verbose: Show progress bar

        Returns:
            List of BenchmarkMetrics
        """
        attack_configs = self.attack_simulator.get_attack_configs()

        if attack_types:
            attack_configs = {k: v for k, v in attack_configs.items() if k in attack_types}

        all_metrics = []

        total_attacks = sum(len(configs) for configs in attack_configs.values())

        with tqdm(total=total_attacks, desc="Running benchmarks", disable=not verbose) as pbar:
            for attack_type, configs in attack_configs.items():
                for attack_func, params, description in configs:
                    metrics = self.run_single_benchmark(
                        image, watermark_text, attack_func, params, description
                    )
                    all_metrics.append(metrics)
                    pbar.update(1)

        return all_metrics

    def run_multi_image_benchmark(
        self,
        images: List[Image.Image],
        watermark_text: str = "BENCHMARK-TEST-2024",
        attack_types: Optional[List[AttackType]] = None,
        verbose: bool = True,
    ) -> Dict[int, List[BenchmarkMetrics]]:
        """Run benchmarks on multiple images.

        Args:
            images: List of test images
            watermark_text: Watermark text to use
            attack_types: List of attack types to test
            verbose: Show progress bar

        Returns:
            Dictionary mapping image index to metrics list
        """
        results = {}

        for idx, image in enumerate(images):
            if verbose:
                print(f"\nRunning benchmarks on image {idx + 1}/{len(images)}")
            metrics = self.run_benchmark_suite(
                image, watermark_text, attack_types, verbose=verbose
            )
            results[idx] = metrics

        return results

    def save_results_json(
        self, metrics: List[BenchmarkMetrics], filename: str = "benchmark_results.json"
    ) -> None:
        """Save benchmark results to JSON file.

        Args:
            metrics: List of benchmark metrics
            filename: Output filename
        """
        output_path = self.output_dir / filename

        data = {
            "config": {
                "wavelet": self.config.wavelet,
                "block_size": self.config.block_size,
                "embed_strength": self.config.embed_strength,
                "ecc_symbols": self.config.ecc_symbols,
            },
            "results": [m.to_dict() for m in metrics],
            "aggregated": self.metrics_calculator.aggregate_metrics(metrics).to_dict(),
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Results saved to: {output_path}")

    def save_results_csv(
        self, metrics: List[BenchmarkMetrics], filename: str = "benchmark_results.csv"
    ) -> None:
        """Save benchmark results to CSV file.

        Args:
            metrics: List of benchmark metrics
            filename: Output filename
        """
        output_path = self.output_dir / filename

        fieldnames = [
            "attack_type",
            "attack_params",
            "success",
            "extracted_text",
            "expected_text",
            "bit_error_rate",
            "psnr",
            "ssim",
            "extraction_time",
            "error_message",
        ]

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for metric in metrics:
                writer.writerow(metric.to_dict())

        print(f"Results saved to: {output_path}")

    def save_aggregated_report(
        self, metrics: List[BenchmarkMetrics], filename: str = "benchmark_report.txt"
    ) -> None:
        """Save human-readable aggregated report.

        Args:
            metrics: List of benchmark metrics
            filename: Output filename
        """
        output_path = self.output_dir / filename

        aggregated = self.metrics_calculator.aggregate_metrics(metrics)

        with open(output_path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("WATERMARK ROBUSTNESS BENCHMARK REPORT\n")
            f.write("=" * 80 + "\n\n")

            f.write("Configuration:\n")
            f.write(f"  Wavelet: {self.config.wavelet}\n")
            f.write(f"  Block Size: {self.config.block_size}\n")
            f.write(f"  Embed Strength: {self.config.embed_strength}\n")
            f.write(f"  ECC Symbols: {self.config.ecc_symbols}\n\n")

            f.write("Overall Results:\n")
            f.write(f"  Total Runs: {aggregated.total_runs}\n")
            f.write(f"  Successful Extractions: {aggregated.successful_extractions}\n")
            f.write(f"  Failed Extractions: {aggregated.failed_extractions}\n")
            f.write(f"  Success Rate: {aggregated.success_rate:.2%}\n\n")

            if aggregated.avg_psnr:
                f.write(f"  Average PSNR: {aggregated.avg_psnr:.2f} dB\n")
            if aggregated.avg_ssim:
                f.write(f"  Average SSIM: {aggregated.avg_ssim:.4f}\n")
            if aggregated.avg_ber:
                f.write(f"  Average BER: {aggregated.avg_ber:.4f}\n")
            if aggregated.avg_extraction_time:
                f.write(f"  Average Extraction Time: {aggregated.avg_extraction_time:.3f}s\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write("Results by Attack Type:\n")
            f.write("=" * 80 + "\n\n")

            for attack_key, stats in sorted(aggregated.metrics_by_attack.items()):
                f.write(f"{attack_key}:\n")
                f.write(f"  Success Rate: {stats['success_rate']:.2%} ")
                f.write(f"({stats['successful']}/{stats['total']})\n\n")

        print(f"Report saved to: {output_path}")

    def run_quick_benchmark(
        self, watermark_text: str = "QUICK-TEST-2024", save_results: bool = True
    ) -> AggregatedMetrics:
        """Run a quick benchmark with reduced attack set.

        Args:
            watermark_text: Watermark text to use
            save_results: Whether to save results to files

        Returns:
            AggregatedMetrics with results
        """
        print("Generating test image...")
        image = self.sample_generator.generate_text_document()

        print("Running quick benchmark...")
        attack_types = [
            AttackType.JPEG_COMPRESSION,
            AttackType.SCALE_DOWN,
            AttackType.ROTATION,
            AttackType.GAUSSIAN_NOISE,
        ]

        metrics = self.run_benchmark_suite(image, watermark_text, attack_types, verbose=True)

        aggregated = self.metrics_calculator.aggregate_metrics(metrics)

        if save_results:
            self.save_results_json(metrics, "quick_benchmark.json")
            self.save_results_csv(metrics, "quick_benchmark.csv")
            self.save_aggregated_report(metrics, "quick_benchmark_report.txt")

        return aggregated

    def run_full_benchmark(
        self,
        num_images: int = 3,
        watermark_text: str = "FULL-BENCHMARK-2024",
        save_results: bool = True,
    ) -> Dict[int, AggregatedMetrics]:
        """Run a comprehensive benchmark on multiple generated images.

        Args:
            num_images: Number of test images to generate
            watermark_text: Watermark text to use
            save_results: Whether to save results to files

        Returns:
            Dictionary mapping image index to AggregatedMetrics
        """
        print(f"Generating {num_images} test images...")
        images = [
            self.sample_generator.generate_text_document(),
            self.sample_generator.generate_gradient_image(orientation="horizontal"),
            self.sample_generator.generate_mixed_content(complexity="medium"),
        ][:num_images]

        print(f"\nRunning full benchmark on {len(images)} images...")
        all_results = self.run_multi_image_benchmark(images, watermark_text, verbose=True)

        aggregated_results = {}
        all_metrics = []

        for idx, metrics in all_results.items():
            aggregated = self.metrics_calculator.aggregate_metrics(metrics)
            aggregated_results[idx] = aggregated
            all_metrics.extend(metrics)

        if save_results:
            self.save_results_json(all_metrics, "full_benchmark.json")
            self.save_results_csv(all_metrics, "full_benchmark.csv")
            self.save_aggregated_report(all_metrics, "full_benchmark_report.txt")

        return aggregated_results
