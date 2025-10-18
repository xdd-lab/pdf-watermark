"""
Benchmark suite with report generation for PDF watermarking system.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import numpy as np
from PIL import Image

from .core.watermark import PDFWatermarker, WatermarkConfig, WatermarkingError


@dataclass
class BenchmarkResult:
    """Results from a single benchmark test."""
    test_name: str
    config: Dict[str, Any]
    image_size: tuple[int, int]
    watermark_text: str
    embed_time: float
    extract_time: Optional[float]
    extraction_success: bool
    extracted_text: Optional[str]
    match_success: bool
    error_message: Optional[str] = None


@dataclass
class RobustnessResult:
    """Results from robustness testing."""
    attack_type: str
    attack_params: Dict[str, Any]
    success: bool
    extracted_text: Optional[str]
    error_message: Optional[str] = None


class BenchmarkSuite:
    """Comprehensive benchmark suite for watermarking system."""
    
    def __init__(self, output_dir: str = "./benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
        self.robustness_results: List[RobustnessResult] = []
    
    def create_test_image(self, width: int, height: int) -> Image.Image:
        """Create a test image with gradient pattern."""
        x = np.linspace(0, 255, width, dtype=np.uint8)
        y = np.linspace(0, 255, height, dtype=np.uint8)
        xx, yy = np.meshgrid(x, y)
        
        r = xx
        g = yy
        b = (xx + yy) // 2
        
        image = np.stack([r, g, b], axis=2)
        return Image.fromarray(image, mode="RGB")
    
    def benchmark_embed(
        self,
        config: WatermarkConfig,
        image: Image.Image,
        watermark_text: str
    ) -> tuple[Optional[Image.Image], float]:
        """Benchmark watermark embedding."""
        watermarker = PDFWatermarker(config)
        
        start_time = time.time()
        try:
            watermarked = watermarker.embed_image(image, watermark_text)
            elapsed = time.time() - start_time
            return watermarked, elapsed
        except Exception:
            elapsed = time.time() - start_time
            return None, elapsed
    
    def benchmark_extract(
        self,
        config: WatermarkConfig,
        image: Image.Image
    ) -> tuple[Optional[str], float, bool]:
        """Benchmark watermark extraction."""
        watermarker = PDFWatermarker(config)
        
        start_time = time.time()
        try:
            extracted = watermarker.extract_from_image(image)
            elapsed = time.time() - start_time
            return extracted, elapsed, True
        except WatermarkingError as e:
            elapsed = time.time() - start_time
            return str(e), elapsed, False
    
    def run_performance_benchmark(
        self,
        test_name: str,
        config: WatermarkConfig,
        image_size: tuple[int, int],
        watermark_text: str
    ) -> BenchmarkResult:
        """Run a single performance benchmark."""
        width, height = image_size
        image = self.create_test_image(width, height)
        
        # Embed
        watermarked, embed_time = self.benchmark_embed(config, image, watermark_text)
        
        # Extract
        if watermarked is not None:
            extracted, extract_time, success = self.benchmark_extract(config, watermarked)
            match_success = success and extracted == watermark_text
        else:
            extracted, extract_time, success = None, None, False
            match_success = False
        
        result = BenchmarkResult(
            test_name=test_name,
            config=asdict(config),
            image_size=image_size,
            watermark_text=watermark_text,
            embed_time=embed_time,
            extract_time=extract_time,
            extraction_success=success,
            extracted_text=extracted if success else None,
            match_success=match_success,
            error_message=extracted if not success else None
        )
        
        self.results.append(result)
        return result
    
    def run_robustness_test(
        self,
        config: WatermarkConfig,
        watermark_text: str,
        attack_type: str,
        attack_func,
        attack_params: Dict[str, Any]
    ) -> RobustnessResult:
        """Run a robustness test with a specific attack."""
        # Create and embed watermark
        image = self.create_test_image(1240, 1754)  # A4 @ 150dpi
        watermarker = PDFWatermarker(config)
        
        try:
            watermarked = watermarker.embed_image(image, watermark_text)
            
            # Apply attack
            attacked = attack_func(watermarked, **attack_params)
            
            # Try to extract
            extracted = watermarker.extract_from_image(attacked)
            success = extracted == watermark_text
            
            result = RobustnessResult(
                attack_type=attack_type,
                attack_params=attack_params,
                success=success,
                extracted_text=extracted,
                error_message=None
            )
        except Exception as e:
            result = RobustnessResult(
                attack_type=attack_type,
                attack_params=attack_params,
                success=False,
                extracted_text=None,
                error_message=str(e)
            )
        
        self.robustness_results.append(result)
        return result
    
    def run_standard_suite(self):
        """Run the standard benchmark suite."""
        print("=" * 80)
        print("PDF Blind Watermark - Standard Benchmark Suite")
        print("=" * 80)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        test_sizes = [
            (1024, 768, "Small (1024x768)"),
            (1240, 1754, "A4 @ 150dpi"),
            (1754, 2480, "A4 @ 200dpi"),
        ]
        
        configs = [
            (WatermarkConfig(embed_strength=10.0, ecc_symbols=16, dpi=120, quality=75), "Fast"),
            (WatermarkConfig(embed_strength=12.0, ecc_symbols=32, dpi=150, quality=85), "Balanced"),
            (WatermarkConfig(embed_strength=16.0, ecc_symbols=48, dpi=180, quality=90), "Robust"),
        ]
        
        watermark_text = "BENCHMARK-TEST-2024"
        
        for width, height, size_label in test_sizes:
            print(f"\n{size_label}")
            print("-" * 80)
            
            for config, config_label in configs:
                result = self.run_performance_benchmark(
                    f"{size_label} - {config_label}",
                    config,
                    (width, height),
                    watermark_text
                )
                
                status = "✓" if result.match_success else "✗"
                print(f"  {status} {config_label:12} | "
                      f"Embed: {result.embed_time:.3f}s | "
                      f"Extract: {result.extract_time:.3f}s" if result.extract_time else "Extract: FAILED")
        
        print("\n" + "=" * 80)
        print("Benchmark completed.")
    
    def run_robustness_suite(self):
        """Run robustness tests with various attacks."""
        print("\n" + "=" * 80)
        print("Robustness Testing Suite")
        print("=" * 80)
        
        config = WatermarkConfig(embed_strength=14.0, ecc_symbols=32)
        watermark_text = "ROBUSTNESS-TEST"
        
        # JPEG compression
        print("\n1. JPEG Compression Tests")
        print("-" * 80)
        for quality in [90, 70, 50]:
            result = self.run_robustness_test(
                config,
                watermark_text,
                "JPEG Compression",
                self._attack_jpeg_compress,
                {"quality": quality}
            )
            status = "✓" if result.success else "✗"
            print(f"  {status} Quality {quality}: {result.extracted_text if result.success else result.error_message}")
        
        # Resize
        print("\n2. Resize Tests")
        print("-" * 80)
        for scale in [0.75, 0.5, 0.3]:
            result = self.run_robustness_test(
                config,
                watermark_text,
                "Resize",
                self._attack_resize,
                {"scale": scale}
            )
            status = "✓" if result.success else "✗"
            print(f"  {status} Scale {scale}: {result.extracted_text if result.success else result.error_message}")
        
        # Gaussian noise
        print("\n3. Gaussian Noise Tests")
        print("-" * 80)
        for sigma in [5, 10, 15]:
            result = self.run_robustness_test(
                config,
                watermark_text,
                "Gaussian Noise",
                self._attack_gaussian_noise,
                {"sigma": sigma}
            )
            status = "✓" if result.success else "✗"
            print(f"  {status} Sigma {sigma}: {result.extracted_text if result.success else result.error_message}")
        
        print("\n" + "=" * 80)
    
    @staticmethod
    def _attack_jpeg_compress(image: Image.Image, quality: int) -> Image.Image:
        """Apply JPEG compression attack."""
        from io import BytesIO
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        return Image.open(buffer)
    
    @staticmethod
    def _attack_resize(image: Image.Image, scale: float) -> Image.Image:
        """Apply resize attack."""
        new_size = (int(image.width * scale), int(image.height * scale))
        resized = image.resize(new_size, Image.LANCZOS)
        # Resize back to original
        return resized.resize((image.width, image.height), Image.LANCZOS)
    
    @staticmethod
    def _attack_gaussian_noise(image: Image.Image, sigma: float) -> Image.Image:
        """Apply Gaussian noise attack."""
        img_array = np.array(image, dtype=np.float32)
        noise = np.random.normal(0, sigma, img_array.shape)
        noisy = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy)
    
    def generate_report(self, report_type: str = "html") -> str:
        """Generate a benchmark report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if report_type == "html":
            return self._generate_html_report(timestamp)
        elif report_type == "json":
            return self._generate_json_report(timestamp)
        elif report_type == "markdown":
            return self._generate_markdown_report(timestamp)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
    
    def _generate_json_report(self, timestamp: str) -> str:
        """Generate JSON report."""
        report_path = self.output_dir / f"benchmark_report_{timestamp}.json"
        
        report_data = {
            "timestamp": timestamp,
            "performance_results": [asdict(r) for r in self.results],
            "robustness_results": [asdict(r) for r in self.robustness_results],
            "summary": self._calculate_summary()
        }
        
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)
        
        return str(report_path)
    
    def _generate_markdown_report(self, timestamp: str) -> str:
        """Generate Markdown report."""
        report_path = self.output_dir / f"benchmark_report_{timestamp}.md"
        
        lines = [
            "# PDF Blind Watermark - Benchmark Report",
            f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Performance Results\n"
        ]
        
        if self.results:
            lines.append("| Test Name | Image Size | Embed Time | Extract Time | Success |")
            lines.append("|-----------|------------|------------|--------------|---------|")
            
            for result in self.results:
                status = "✓" if result.match_success else "✗"
                lines.append(
                    f"| {result.test_name} | "
                    f"{result.image_size[0]}x{result.image_size[1]} | "
                    f"{result.embed_time:.3f}s | "
                    f"{result.extract_time:.3f}s if result.extract_time else 'N/A' | "
                    f"{status} |"
                )
        
        if self.robustness_results:
            lines.append("\n## Robustness Results\n")
            lines.append("| Attack Type | Parameters | Success | Extracted Text |")
            lines.append("|-------------|------------|---------|----------------|")
            
            for result in self.robustness_results:
                status = "✓" if result.success else "✗"
                params_str = ", ".join(f"{k}={v}" for k, v in result.attack_params.items())
                lines.append(
                    f"| {result.attack_type} | "
                    f"{params_str} | "
                    f"{status} | "
                    f"{result.extracted_text if result.success else result.error_message} |"
                )
        
        summary = self._calculate_summary()
        lines.append("\n## Summary\n")
        lines.append(f"- **Total Tests:** {summary['total_tests']}")
        lines.append(f"- **Success Rate:** {summary['success_rate']:.1%}")
        lines.append(f"- **Average Embed Time:** {summary['avg_embed_time']:.3f}s")
        lines.append(f"- **Average Extract Time:** {summary['avg_extract_time']:.3f}s")
        
        with open(report_path, "w") as f:
            f.write("\n".join(lines))
        
        return str(report_path)
    
    def _generate_html_report(self, timestamp: str) -> str:
        """Generate HTML report."""
        report_path = self.output_dir / f"benchmark_report_{timestamp}.html"
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PDF Blind Watermark - Benchmark Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2 {{
            color: #333;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .summary {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #34495e;
            color: white;
        }}
        .success {{
            color: #27ae60;
            font-weight: bold;
        }}
        .failure {{
            color: #e74c3c;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PDF Blind Watermark - Benchmark Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""
        
        summary = self._calculate_summary()
        html_content += f"""
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Tests:</strong> {summary['total_tests']}</p>
        <p><strong>Success Rate:</strong> {summary['success_rate']:.1%}</p>
        <p><strong>Average Embed Time:</strong> {summary['avg_embed_time']:.3f}s</p>
        <p><strong>Average Extract Time:</strong> {summary['avg_extract_time']:.3f}s</p>
    </div>
"""
        
        if self.results:
            html_content += """
    <h2>Performance Results</h2>
    <table>
        <tr>
            <th>Test Name</th>
            <th>Image Size</th>
            <th>Embed Time</th>
            <th>Extract Time</th>
            <th>Status</th>
        </tr>
"""
            for result in self.results:
                status_class = "success" if result.match_success else "failure"
                status_text = "✓ Success" if result.match_success else "✗ Failed"
                extract_time = f"{result.extract_time:.3f}s" if result.extract_time else "N/A"
                
                html_content += f"""
        <tr>
            <td>{result.test_name}</td>
            <td>{result.image_size[0]}x{result.image_size[1]}</td>
            <td>{result.embed_time:.3f}s</td>
            <td>{extract_time}</td>
            <td class="{status_class}">{status_text}</td>
        </tr>
"""
            html_content += "    </table>\n"
        
        if self.robustness_results:
            html_content += """
    <h2>Robustness Results</h2>
    <table>
        <tr>
            <th>Attack Type</th>
            <th>Parameters</th>
            <th>Status</th>
            <th>Result</th>
        </tr>
"""
            for result in self.robustness_results:
                status_class = "success" if result.success else "failure"
                status_text = "✓ Success" if result.success else "✗ Failed"
                params_str = ", ".join(f"{k}={v}" for k, v in result.attack_params.items())
                result_text = result.extracted_text if result.success else result.error_message
                
                html_content += f"""
        <tr>
            <td>{result.attack_type}</td>
            <td>{params_str}</td>
            <td class="{status_class}">{status_text}</td>
            <td>{result_text}</td>
        </tr>
"""
            html_content += "    </table>\n"
        
        html_content += """
</body>
</html>
"""
        
        with open(report_path, "w") as f:
            f.write(html_content)
        
        return str(report_path)
    
    def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics."""
        total_tests = len(self.results) + len(self.robustness_results)
        
        successful = sum(1 for r in self.results if r.match_success)
        successful += sum(1 for r in self.robustness_results if r.success)
        
        success_rate = successful / total_tests if total_tests > 0 else 0
        
        avg_embed_time = np.mean([r.embed_time for r in self.results]) if self.results else 0
        avg_extract_time = np.mean([r.extract_time for r in self.results if r.extract_time]) if self.results else 0
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful,
            "success_rate": success_rate,
            "avg_embed_time": avg_embed_time,
            "avg_extract_time": avg_extract_time
        }


def run_full_benchmark():
    """Run the full benchmark suite and generate reports."""
    suite = BenchmarkSuite()
    
    # Run performance benchmarks
    suite.run_standard_suite()
    
    # Run robustness tests
    suite.run_robustness_suite()
    
    # Generate reports
    print("\n" + "=" * 80)
    print("Generating Reports...")
    print("=" * 80)
    
    html_report = suite.generate_report("html")
    print(f"  HTML Report: {html_report}")
    
    json_report = suite.generate_report("json")
    print(f"  JSON Report: {json_report}")
    
    md_report = suite.generate_report("markdown")
    print(f"  Markdown Report: {md_report}")
    
    print("\nBenchmark suite completed successfully!")


if __name__ == "__main__":
    run_full_benchmark()
