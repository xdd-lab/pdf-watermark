# Benchmark Suite Guide

## Overview

The benchmark suite provides comprehensive tools for evaluating the robustness and invisibility of the DCT/DWT watermark pipelines. It includes automated testing of various attack scenarios, quality metrics calculation, and result aggregation.

## Features

- **Sample Generation**: Create controlled test PDFs and images with various patterns
- **Attack Simulation**: Apply scripted attacks (JPEG compression, scaling, rotation, noise, etc.)
- **Metrics Collection**: Calculate PSNR, SSIM, bit error rate, and extraction success rate
- **Result Export**: Save results to JSON, CSV, and human-readable reports
- **CLI Integration**: Run benchmarks from command line
- **Customizable Tests**: Configure attack types, strength levels, and test images

## Quick Start

### CLI Usage

#### Quick Benchmark (Reduced Attack Set)

```bash
python -m pdf_blind_watermark benchmark --mode quick
```

#### Full Benchmark (All Attacks)

```bash
python -m pdf_blind_watermark benchmark --mode full --num-images 3
```

#### Custom Configuration

```bash
python -m pdf_blind_watermark benchmark \
  --mode full \
  --strength 14.0 \
  --watermark "CUSTOM-TEXT" \
  --output ./results \
  --attacks jpeg_compression \
  --attacks gaussian_noise
```

### Python API Usage

```python
from pdf_blind_watermark import BenchmarkRunner, SampleGenerator
from pdf_blind_watermark.core.watermark import WatermarkConfig
from pdf_blind_watermark.benchmark.attacks import AttackType

# Create a test image
generator = SampleGenerator()
image = generator.generate_text_document()

# Configure watermark
config = WatermarkConfig(embed_strength=12.0)

# Run benchmark
runner = BenchmarkRunner(config=config, output_dir="./results")
metrics = runner.run_benchmark_suite(
    image,
    watermark_text="TEST-2024",
    attack_types=[AttackType.JPEG_COMPRESSION, AttackType.SCALE_DOWN],
    verbose=True
)

# Save results
runner.save_results_json(metrics)
runner.save_results_csv(metrics)
runner.save_aggregated_report(metrics)
```

## Attack Types

The benchmark suite supports the following attack types:

### Compression and Encoding
- **JPEG Compression**: Quality levels 90, 75, 50, 30
- **Screenshot Simulation**: Color space conversion + slight blur

### Geometric Transformations
- **Scale Down**: 75%, 50%, 25% of original size
- **Scale Up**: 125%, 150%, 200% of original size
- **Rotation**: ±2°, ±5°, ±10°
- **Crop**: 5%, 10%, 15% from each edge

### Noise and Filtering
- **Gaussian Noise**: σ = 5, 10, 15
- **Salt & Pepper Noise**: p = 0.005, 0.01, 0.02
- **Gaussian Blur**: radius = 1, 2, 3
- **Median Filter**: 3×3, 5×5

### Color and Brightness
- **Brightness Change**: 80%, 120%
- **Contrast Change**: 80%, 120%

## Metrics

### Invisibility Metrics

**PSNR (Peak Signal-to-Noise Ratio)**
- Measures the difference between original and watermarked images
- Higher is better (typically 30-50 dB for invisible watermarks)
- Unit: decibels (dB)

**SSIM (Structural Similarity Index)**
- Measures perceptual similarity between images
- Range: 0-1 (1 = identical)
- Recommended: > 0.95 for invisible watermarks

### Robustness Metrics

**Extraction Success Rate**
- Percentage of successful watermark extractions
- 100% = all attacks survived

**Bit Error Rate (BER)**
- Ratio of incorrect bits in extracted watermark
- Range: 0-1 (0 = perfect extraction)
- Only calculated for successful extractions

**Extraction Time**
- Time taken to extract watermark
- Helps identify performance bottlenecks

## Sample Generators

### Image Types

**Gradient Images**
```python
generator = SampleGenerator()
image = generator.generate_gradient_image(
    width=1024, 
    height=768, 
    orientation="horizontal"  # or "vertical", "radial"
)
```

**Text Documents**
```python
image = generator.generate_text_document(
    width=1240,
    height=1754,  # A4 size at 150 DPI
    num_lines=30
)
```

**Mixed Content**
```python
image = generator.generate_mixed_content(
    width=1240,
    height=1754,
    complexity="medium"  # or "low", "high"
)
```

**Noise Patterns**
```python
image = generator.generate_noise_pattern(
    width=1024,
    height=768,
    noise_type="gaussian"  # or "uniform", "salt_pepper"
)
```

### PDF Generation

```python
images = [
    generator.generate_text_document(),
    generator.generate_gradient_image(),
]
generator.generate_sample_pdf("output.pdf", images, quality=90)
```

## Result Files

### JSON Output
Contains detailed metrics for each run plus aggregated statistics:
```json
{
  "config": {
    "embed_strength": 12.0,
    "ecc_symbols": 32,
    ...
  },
  "results": [
    {
      "attack_type": "jpeg_compression",
      "attack_params": "JPEG Q75",
      "success": true,
      "psnr": 42.5,
      "ssim": 0.985,
      ...
    }
  ],
  "aggregated": {
    "total_runs": 50,
    "success_rate": 0.94,
    "avg_psnr": 41.2,
    ...
  }
}
```

### CSV Output
Tabular format suitable for analysis in Excel or Python:
```csv
attack_type,attack_params,success,psnr,ssim,ber,extraction_time
jpeg_compression,JPEG Q75,True,42.5,0.985,0.0,0.234
...
```

### Text Report
Human-readable summary:
```
================================================================================
WATERMARK ROBUSTNESS BENCHMARK REPORT
================================================================================

Configuration:
  Wavelet: haar
  Block Size: 8
  Embed Strength: 12.0
  ECC Symbols: 32

Overall Results:
  Total Runs: 50
  Successful Extractions: 47
  Failed Extractions: 3
  Success Rate: 94.00%

  Average PSNR: 41.23 dB
  Average SSIM: 0.9821
  Average BER: 0.0021
  Average Extraction Time: 0.234s

================================================================================
Results by Attack Type:
================================================================================

jpeg_compression:JPEG Q90:
  Success Rate: 100.00% (4/4)

jpeg_compression:JPEG Q75:
  Success Rate: 100.00% (4/4)
...
```

## Advanced Usage

### Testing DWT-Only Pipeline

```python
from pdf_blind_watermark.core.dwt_watermark import DWTWatermark
import numpy as np

# Generate watermark bits
watermark_bits = np.random.randint(0, 2, (32, 32))

# Create DWT watermarker
dwt = DWTWatermark(wavelet="haar", level=2)

# Embed and test
image_array = np.array(image)
watermarked = dwt.embed(image_array, watermark_bits, strength=30.0)

# Apply attacks and extract
attacked = attack_func(Image.fromarray(watermarked))
extracted_bits = dwt.extract(np.array(attacked), (32, 32))

# Calculate accuracy
accuracy = np.mean(watermark_bits == extracted_bits)
```

### Batch Testing Multiple Configurations

```python
configs = [
    WatermarkConfig(embed_strength=8.0, ecc_symbols=16),
    WatermarkConfig(embed_strength=12.0, ecc_symbols=32),
    WatermarkConfig(embed_strength=16.0, ecc_symbols=48),
]

for i, config in enumerate(configs):
    runner = BenchmarkRunner(
        config=config, 
        output_dir=f"./results/config_{i}"
    )
    aggregated = runner.run_quick_benchmark(save_results=True)
    print(f"Config {i}: Success rate = {aggregated.success_rate:.2%}")
```

### Custom Attack Implementation

```python
from pdf_blind_watermark.benchmark.attacks import AttackSimulator

class CustomAttackSimulator(AttackSimulator):
    @staticmethod
    def my_custom_attack(image, param1, param2):
        """Apply custom attack."""
        # Your attack logic here
        return modified_image

# Use in benchmark
attack_func = CustomAttackSimulator.my_custom_attack
metrics = runner.run_single_benchmark(
    image, 
    watermark_text="TEST",
    attack_func=attack_func,
    attack_params={"param1": value1, "param2": value2},
    attack_description="Custom Attack"
)
```

## Performance Considerations

### Image Size Impact
- Larger images provide more embedding capacity
- Extraction time scales linearly with image area
- Recommended minimum: 800×600 pixels

### Watermark Strength vs. Invisibility Trade-off
| Strength | PSNR (dB) | Success Rate | Use Case |
|----------|-----------|--------------|----------|
| 8.0      | 45-50     | 70-80%       | Maximum invisibility |
| 12.0     | 40-45     | 85-95%       | Balanced (recommended) |
| 16.0     | 35-40     | 95-99%       | High robustness |
| 20.0     | 30-35     | 98-100%      | Maximum robustness |

### ECC Symbols Impact
- More ECC symbols = better error correction
- Each ECC symbol adds ~1 byte to payload
- Recommended: 32 symbols for normal use, 48+ for hostile environments

## Troubleshooting

### Low Success Rate
- Increase `embed_strength` (try 14.0-16.0)
- Increase `ecc_symbols` (try 48 or 64)
- Check if image size is sufficient (>800×600)
- Verify DPI settings for PDF processing

### Poor Invisibility (Low PSNR/SSIM)
- Decrease `embed_strength` (try 8.0-10.0)
- Check image quality settings
- Ensure YCbCr color space is properly handled

### Extraction Failures
- Verify preamble is not corrupted
- Check if attack is too severe (e.g., extreme compression)
- Increase redundancy in payload
- Enable perspective correction for photos

## Integration Tests

Run the full test suite:

```bash
pytest tests/test_benchmark.py -v
```

Run specific test:

```bash
pytest tests/test_benchmark.py::test_benchmark_workflow_integration -v
```

## Examples

See `examples/benchmark_example.py` for comprehensive usage examples:

```bash
python examples/benchmark_example.py
```

This will:
1. Run a basic benchmark with default settings
2. Test specific attack types
3. Compare different watermark strengths
4. Generate test sample images

## Contributing

To add new attack types:

1. Add the attack to `AttackType` enum in `attacks.py`
2. Implement the attack method in `AttackSimulator` class
3. Add configuration to `get_attack_configs()`
4. Add tests in `tests/test_benchmark.py`

## References

- Cox, I. J., et al. (2007). Digital Watermarking and Steganography.
- Wang, Z., et al. (2004). "Image Quality Assessment: From Error Visibility to Structural Similarity." IEEE TIP.
- Reed, I. S., & Solomon, G. (1960). "Polynomial Codes Over Certain Finite Fields."
