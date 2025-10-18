"""
Example script for running benchmarks and generating reports.

This demonstrates how to:
1. Run performance benchmarks
2. Run robustness tests
3. Generate comprehensive reports
4. Interpret benchmark results
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_blind_watermark.benchmark import BenchmarkSuite, run_full_benchmark
from pdf_blind_watermark.core.watermark import WatermarkConfig


def example_quick_benchmark():
    """Run a quick performance benchmark."""
    print("=" * 80)
    print("Quick Performance Benchmark")
    print("=" * 80)
    
    suite = BenchmarkSuite(output_dir="./benchmark_results")
    
    # Test a single configuration
    config = WatermarkConfig(
        embed_strength=12.0,
        ecc_symbols=32,
        dpi=150,
        quality=85
    )
    
    result = suite.run_performance_benchmark(
        test_name="Standard Configuration",
        config=config,
        image_size=(1240, 1754),  # A4 @ 150dpi
        watermark_text="TEST-BENCHMARK"
    )
    
    print(f"\nResults:")
    print(f"  Embed time: {result.embed_time:.3f}s")
    print(f"  Extract time: {result.extract_time:.3f}s" if result.extract_time else "  Extract: FAILED")
    print(f"  Success: {'✓' if result.match_success else '✗'}")
    
    # Generate a markdown report
    report_path = suite.generate_report("markdown")
    print(f"\n✓ Report generated: {report_path}")


def example_compare_configurations():
    """Compare different configuration profiles."""
    print("\n" + "=" * 80)
    print("Configuration Comparison")
    print("=" * 80)
    
    suite = BenchmarkSuite(output_dir="./benchmark_results")
    
    configurations = [
        ("Fast (Low Security)", WatermarkConfig(
            embed_strength=10.0,
            ecc_symbols=16,
            dpi=120,
            quality=75
        )),
        ("Balanced (Recommended)", WatermarkConfig(
            embed_strength=12.0,
            ecc_symbols=32,
            dpi=150,
            quality=85
        )),
        ("Robust (High Security)", WatermarkConfig(
            embed_strength=16.0,
            ecc_symbols=48,
            dpi=180,
            quality=90
        )),
    ]
    
    print("\nRunning benchmarks for different profiles...\n")
    
    for name, config in configurations:
        print(f"Testing: {name}")
        result = suite.run_performance_benchmark(
            test_name=name,
            config=config,
            image_size=(1240, 1754),
            watermark_text="COMPARE-TEST"
        )
        
        print(f"  Embed: {result.embed_time:.3f}s | Extract: {result.extract_time:.3f}s | "
              f"Success: {'✓' if result.match_success else '✗'}")
    
    # Generate reports
    print("\nGenerating reports...")
    html_report = suite.generate_report("html")
    json_report = suite.generate_report("json")
    
    print(f"  HTML: {html_report}")
    print(f"  JSON: {json_report}")


def example_robustness_analysis():
    """Analyze robustness against various attacks."""
    print("\n" + "=" * 80)
    print("Robustness Analysis")
    print("=" * 80)
    
    suite = BenchmarkSuite(output_dir="./benchmark_results")
    
    # Use a balanced configuration
    config = WatermarkConfig(
        embed_strength=14.0,
        ecc_symbols=32,
        dpi=150,
        quality=85
    )
    
    watermark_text = "ROBUSTNESS-ANALYSIS"
    
    print("\nTesting JPEG compression robustness...")
    for quality in [90, 70, 50, 30]:
        result = suite.run_robustness_test(
            config=config,
            watermark_text=watermark_text,
            attack_type="JPEG Compression",
            attack_func=suite._attack_jpeg_compress,
            attack_params={"quality": quality}
        )
        status = "✓" if result.success else "✗"
        print(f"  {status} Quality {quality:2d}: {result.extracted_text if result.success else 'FAILED'}")
    
    print("\nTesting resize robustness...")
    for scale in [1.0, 0.75, 0.5, 0.25]:
        result = suite.run_robustness_test(
            config=config,
            watermark_text=watermark_text,
            attack_type="Resize",
            attack_func=suite._attack_resize,
            attack_params={"scale": scale}
        )
        status = "✓" if result.success else "✗"
        print(f"  {status} Scale {scale:.2f}: {result.extracted_text if result.success else 'FAILED'}")
    
    print("\nTesting noise robustness...")
    for sigma in [5, 10, 15, 20]:
        result = suite.run_robustness_test(
            config=config,
            watermark_text=watermark_text,
            attack_type="Gaussian Noise",
            attack_func=suite._attack_gaussian_noise,
            attack_params={"sigma": sigma}
        )
        status = "✓" if result.success else "✗"
        print(f"  {status} Sigma {sigma:2d}: {result.extracted_text if result.success else 'FAILED'}")
    
    # Generate report
    report_path = suite.generate_report("html")
    print(f"\n✓ Robustness report: {report_path}")


def example_interpret_results():
    """Example of how to interpret benchmark results."""
    print("\n" + "=" * 80)
    print("Interpreting Benchmark Results")
    print("=" * 80)
    
    print("""
1. PERFORMANCE METRICS
   
   Embed Time:
   - Measures how long it takes to embed a watermark
   - Typical range: 0.3s - 2.0s per page
   - Affected by: DPI, image size, configuration
   
   Extract Time:
   - Measures watermark extraction speed
   - Usually faster than embedding (50-70% of embed time)
   - Affected by: image complexity, noise level
   
   Success Rate:
   - Percentage of successful extractions
   - Should be 100% for clean documents
   - Lower rates indicate configuration issues

2. ROBUSTNESS METRICS
   
   JPEG Compression Resistance:
   - ✓ Quality 90+: Excellent (should always work)
   - ✓ Quality 70-90: Very good (recommended range)
   - ⚠ Quality 50-70: Moderate (may fail occasionally)
   - ✗ Quality <50: Poor (likely to fail)
   
   Resize Resistance:
   - ✓ Scale 0.75+: Excellent
   - ✓ Scale 0.5-0.75: Good
   - ⚠ Scale 0.25-0.5: Moderate
   - ✗ Scale <0.25: Poor
   
   Noise Resistance (Gaussian):
   - ✓ Sigma 0-10: Excellent
   - ⚠ Sigma 10-15: Moderate
   - ✗ Sigma 15+: Poor

3. CONFIGURATION RECOMMENDATIONS
   
   Based on robustness requirements:
   
   LOW (Internal Documents):
   - embed_strength: 10.0
   - ecc_symbols: 16
   - Expected: Fast, 95%+ success on screenshots
   
   MEDIUM (Standard Documents):
   - embed_strength: 12.0-14.0
   - ecc_symbols: 32
   - Expected: Balanced, 90%+ success with compression
   
   HIGH (Confidential Documents):
   - embed_strength: 16.0+
   - ecc_symbols: 48
   - Expected: Robust, 85%+ success with photos/prints

4. COMPLIANCE INTEGRATION
   
   Report Metrics for Audit:
   - Success rate across test suite
   - Average extraction time for incident response
   - Robustness scores for different attack scenarios
   - Configuration parameters used
   
   Recommended Thresholds:
   - Success rate: >95% for production deployment
   - Embed time: <2s per page for user acceptance
   - JPEG Q70 resistance: Must pass for compliance
   
5. TROUBLESHOOTING
   
   Low Success Rate (<90%):
   - Increase embed_strength (+2.0)
   - Increase ecc_symbols (+16)
   - Increase DPI (+30)
   
   High Processing Time (>2s):
   - Decrease DPI (-30)
   - Decrease quality (-10)
   - Reduce ecc_symbols (-16)
   
   Visible Artifacts:
   - Decrease embed_strength (-2.0)
   - Increase quality (+5)
   - Check image compatibility
""")


def main():
    """Main function to run all benchmark examples."""
    print("PDF Blind Watermark - Benchmark Examples")
    print("=" * 80)
    print()
    print("Choose an option:")
    print("1. Quick benchmark")
    print("2. Compare configurations")
    print("3. Robustness analysis")
    print("4. Interpret results (guide)")
    print("5. Run full benchmark suite")
    print()
    
    choice = input("Enter choice (1-5, or 'all' for all): ").strip()
    
    if choice == "1":
        example_quick_benchmark()
    elif choice == "2":
        example_compare_configurations()
    elif choice == "3":
        example_robustness_analysis()
    elif choice == "4":
        example_interpret_results()
    elif choice == "5":
        run_full_benchmark()
    elif choice.lower() == "all":
        example_quick_benchmark()
        example_compare_configurations()
        example_robustness_analysis()
        example_interpret_results()
        print("\n" + "=" * 80)
        print("Running full benchmark suite...")
        print("=" * 80)
        run_full_benchmark()
    else:
        print("Invalid choice. Running quick benchmark...")
        example_quick_benchmark()


if __name__ == "__main__":
    main()
