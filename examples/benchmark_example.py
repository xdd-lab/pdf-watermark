"""
Example script demonstrating the benchmark suite usage.

This script shows how to:
1. Generate test samples
2. Run benchmarks with custom configurations
3. Analyze and export results
"""

from __future__ import annotations

from pdf_blind_watermark import BenchmarkRunner, SampleGenerator
from pdf_blind_watermark.core.watermark import WatermarkConfig
from pdf_blind_watermark.benchmark.attacks import AttackType


def run_basic_benchmark():
    """Run a basic benchmark with default settings."""
    print("=" * 80)
    print("Running Basic Benchmark")
    print("=" * 80)

    config = WatermarkConfig(embed_strength=12.0)
    runner = BenchmarkRunner(config=config, output_dir="./benchmark_output")

    aggregated = runner.run_quick_benchmark(watermark_text="EXAMPLE-2024", save_results=True)

    print("\nResults:")
    print(f"  Total runs: {aggregated.total_runs}")
    print(f"  Success rate: {aggregated.success_rate:.2%}")
    print(f"  Average PSNR: {aggregated.avg_psnr:.2f} dB" if aggregated.avg_psnr else "  PSNR: N/A")
    print(f"  Average SSIM: {aggregated.avg_ssim:.4f}" if aggregated.avg_ssim else "  SSIM: N/A")


def run_custom_attack_benchmark():
    """Run benchmark with specific attack types."""
    print("\n" + "=" * 80)
    print("Running Custom Attack Benchmark")
    print("=" * 80)

    generator = SampleGenerator()
    image = generator.generate_text_document(width=1024, height=768)

    config = WatermarkConfig(embed_strength=14.0)
    runner = BenchmarkRunner(config=config, output_dir="./benchmark_output")

    attack_types = [
        AttackType.JPEG_COMPRESSION,
        AttackType.SCALE_DOWN,
        AttackType.ROTATION,
        AttackType.GAUSSIAN_NOISE,
        AttackType.GAUSSIAN_BLUR,
    ]

    print(f"Testing {len(attack_types)} attack types...")
    metrics = runner.run_benchmark_suite(
        image, watermark_text="CUSTOM-TEST", attack_types=attack_types, verbose=True
    )

    runner.save_results_json(metrics, "custom_benchmark.json")
    runner.save_results_csv(metrics, "custom_benchmark.csv")
    runner.save_aggregated_report(metrics, "custom_benchmark_report.txt")

    print("\nResults saved to ./benchmark_output/")


def compare_strength_levels():
    """Compare different watermark strength levels."""
    print("\n" + "=" * 80)
    print("Comparing Watermark Strength Levels")
    print("=" * 80)

    generator = SampleGenerator()
    image = generator.generate_mixed_content(complexity="medium")

    strength_levels = [8.0, 12.0, 16.0, 20.0]
    attack_types = [AttackType.JPEG_COMPRESSION, AttackType.GAUSSIAN_NOISE]

    results = {}

    for strength in strength_levels:
        print(f"\nTesting strength: {strength}")
        config = WatermarkConfig(embed_strength=strength)
        runner = BenchmarkRunner(
            config=config, output_dir=f"./benchmark_output/strength_{strength}"
        )

        metrics = runner.run_benchmark_suite(
            image, watermark_text="STRENGTH-TEST", attack_types=attack_types, verbose=False
        )

        from pdf_blind_watermark.benchmark.metrics import MetricsCalculator

        aggregated = MetricsCalculator.aggregate_metrics(metrics)
        results[strength] = aggregated

        print(f"  Success rate: {aggregated.success_rate:.2%}")
        print(f"  Average PSNR: {aggregated.avg_psnr:.2f} dB" if aggregated.avg_psnr else "  PSNR: N/A")

    print("\n" + "=" * 80)
    print("Strength Comparison Summary:")
    print("=" * 80)
    for strength, agg in sorted(results.items()):
        print(f"Strength {strength:4.1f}: Success {agg.success_rate:6.2%}, PSNR {agg.avg_psnr:6.2f} dB")


def generate_test_samples():
    """Generate a suite of test samples."""
    print("\n" + "=" * 80)
    print("Generating Test Sample Suite")
    print("=" * 80)

    generator = SampleGenerator()

    print("Generating gradient images...")
    for orientation in ["horizontal", "vertical", "radial"]:
        img = generator.generate_gradient_image(orientation=orientation)
        img.save(f"./test_samples/gradient_{orientation}.png")
        print(f"  Saved: gradient_{orientation}.png")

    print("\nGenerating text documents...")
    for i in range(3):
        img = generator.generate_text_document()
        img.save(f"./test_samples/document_{i + 1}.png")
        print(f"  Saved: document_{i + 1}.png")

    print("\nGenerating mixed content...")
    for complexity in ["low", "medium", "high"]:
        img = generator.generate_mixed_content(complexity=complexity)
        img.save(f"./test_samples/mixed_{complexity}.png")
        print(f"  Saved: mixed_{complexity}.png")

    print("\nTest samples saved to ./test_samples/")


if __name__ == "__main__":
    import os

    os.makedirs("./benchmark_output", exist_ok=True)
    os.makedirs("./test_samples", exist_ok=True)

    print("PDF Blind Watermark Benchmark Suite Example")
    print("=" * 80)

    run_basic_benchmark()

    run_custom_attack_benchmark()

    compare_strength_levels()

    generate_test_samples()

    print("\n" + "=" * 80)
    print("All examples completed successfully!")
    print("=" * 80)
