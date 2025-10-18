"""
Performance benchmarking for multi-page processing with optimizations.
"""
from __future__ import annotations

import time
import tempfile
import os
import cProfile
import pstats
from io import StringIO

import numpy as np
from PIL import Image
import fitz

from pdf_blind_watermark import PDFWatermarker
from pdf_blind_watermark.core.watermark import WatermarkConfig


def create_test_image(width: int, height: int) -> Image.Image:
    """Create a test image with gradient pattern."""
    x = np.linspace(0, 255, width, dtype=np.uint8)
    y = np.linspace(0, 255, height, dtype=np.uint8)
    xx, yy = np.meshgrid(x, y)
    
    r = xx
    g = yy
    b = (xx + yy) // 2
    
    image = np.stack([r, g, b], axis=2)
    return Image.fromarray(image, mode="RGB")


def create_multipage_pdf(num_pages: int, width: int = 1240, height: int = 1754) -> str:
    """Create a multi-page test PDF."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    doc = fitz.open()
    for i in range(num_pages):
        img = create_test_image(width, height)
        
        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        
        img_rect = fitz.Rect(0, 0, img.width, img.height)
        page = doc.new_page(width=img.width, height=img.height)
        page.insert_image(img_rect, stream=buf.getvalue())
    
    doc.save(temp_path)
    doc.close()
    
    return temp_path


def benchmark_multipage_embedding(
    num_pages: int,
    config: WatermarkConfig,
    watermark_text: str,
    stego_text: str | None = None,
    profile: bool = False
) -> dict:
    """Benchmark multi-page embedding with optional profiling."""
    
    pdf_path = create_multipage_pdf(num_pages)
    output_path = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
    
    try:
        watermarker = PDFWatermarker(config)
        
        if profile:
            profiler = cProfile.Profile()
            profiler.enable()
        
        start_time = time.time()
        watermarker.embed(pdf_path, output_path, watermark_text, stego_text=stego_text)
        elapsed = time.time() - start_time
        
        if profile:
            profiler.disable()
            
            # Get profile stats
            s = StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(20)
            profile_output = s.getvalue()
        else:
            profile_output = None
        
        # Get file sizes
        input_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
        output_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        
        return {
            'elapsed_time': elapsed,
            'time_per_page': elapsed / num_pages,
            'input_size_mb': input_size,
            'output_size_mb': output_size,
            'profile': profile_output
        }
        
    finally:
        os.unlink(pdf_path)
        os.unlink(output_path)


def run_performance_comparison():
    """Compare performance across different configurations."""
    
    print("=" * 80)
    print("Multi-Page Processing Performance Benchmarks")
    print("=" * 80)
    
    test_configs = [
        ("Sequential (baseline)", WatermarkConfig(
            embed_strength=12.0,
            dpi=150,
            enable_parallel=False,
            enable_steganography=False
        )),
        ("Parallel processing", WatermarkConfig(
            embed_strength=12.0,
            dpi=150,
            enable_parallel=True,
            parallel_threshold=3,
            enable_steganography=False
        )),
        ("Sequential + Stego", WatermarkConfig(
            embed_strength=12.0,
            dpi=150,
            enable_parallel=False,
            enable_steganography=True,
            stego_ecc_symbols=16
        )),
        ("Parallel + Stego", WatermarkConfig(
            embed_strength=12.0,
            dpi=150,
            enable_parallel=True,
            parallel_threshold=3,
            enable_steganography=True,
            stego_ecc_symbols=16
        )),
    ]
    
    page_counts = [3, 5, 10]
    
    for num_pages in page_counts:
        print(f"\n{'=' * 80}")
        print(f"Test: {num_pages} pages (A4 @ 150 DPI)")
        print(f"{'=' * 80}\n")
        
        results = []
        
        for config_name, config in test_configs:
            print(f"Running: {config_name}...")
            
            watermark_text = "BENCHMARK-2024"
            stego_text = "Secret benchmark data" if config.enable_steganography else None
            
            result = benchmark_multipage_embedding(
                num_pages, 
                config, 
                watermark_text,
                stego_text,
                profile=False
            )
            
            results.append((config_name, result))
            
            print(f"  Time: {result['elapsed_time']:.2f}s ({result['time_per_page']:.2f}s/page)")
            print(f"  Output size: {result['output_size_mb']:.2f} MB\n")
        
        # Calculate speedups
        baseline_time = results[0][1]['elapsed_time']
        print(f"Speedup comparison (vs Sequential baseline):")
        for config_name, result in results:
            speedup = baseline_time / result['elapsed_time']
            print(f"  {config_name:30} {speedup:.2f}x")
        print()


def run_profiled_test():
    """Run a profiled test to identify bottlenecks."""
    
    print("\n" + "=" * 80)
    print("Profiling 5-page embedding with parallel + steganography")
    print("=" * 80 + "\n")
    
    config = WatermarkConfig(
        embed_strength=12.0,
        dpi=150,
        enable_parallel=True,
        parallel_threshold=3,
        enable_steganography=True,
        stego_ecc_symbols=16
    )
    
    result = benchmark_multipage_embedding(
        num_pages=5,
        config=config,
        watermark_text="PROFILE-TEST",
        stego_text="Hidden profile data",
        profile=True
    )
    
    print(f"Total time: {result['elapsed_time']:.2f}s")
    print(f"Time per page: {result['time_per_page']:.2f}s")
    print(f"\nTop 20 functions by cumulative time:")
    print("-" * 80)
    print(result['profile'])


if __name__ == "__main__":
    run_performance_comparison()
    run_profiled_test()
