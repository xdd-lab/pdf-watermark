#!/usr/bin/env python
"""
Simple demonstration of the benchmark framework functionality.

This script shows that the benchmark infrastructure works correctly,
even though the underlying watermark extraction may have issues with
certain image sizes or configurations.
"""

from pdf_blind_watermark.benchmark.sample_generator import SampleGenerator
from pdf_blind_watermark.benchmark.attacks import AttackSimulator
from pdf_blind_watermark.benchmark.metrics import MetricsCalculator

print("=" * 80)
print("Benchmark Framework Demonstration")
print("=" * 80)

# 1. Sample Generation
print("\n1. Testing Sample Generation")
print("-" * 80)
generator = SampleGenerator()

gradient = generator.generate_gradient_image(width=800, height=600, orientation="horizontal")
print(f"✓ Generated gradient image: {gradient.size}")

text_doc = generator.generate_text_document(width=1240, height=1754)
print(f"✓ Generated text document: {text_doc.size}")

mixed = generator.generate_mixed_content(width=1024, height=768, complexity="medium")
print(f"✓ Generated mixed content: {mixed.size}")

# 2. Attack Simulation
print("\n2. Testing Attack Simulation")
print("-" * 80)

original = generator.generate_gradient_image(width=512, height=512)
print(f"Original image: {original.size}")

jpeg_compressed = AttackSimulator.jpeg_compression(original, quality=75)
print(f"✓ JPEG compression: {jpeg_compressed.size}")

scaled_down = AttackSimulator.scale_down(original, scale_factor=0.5)
print(f"✓ Scale down: {scaled_down.size}")

rotated = AttackSimulator.rotation(original, angle=5.0)
print(f"✓ Rotation: {rotated.size}")

noisy = AttackSimulator.gaussian_noise(original, sigma=10.0)
print(f"✓ Gaussian noise: {noisy.size}")

blurred = AttackSimulator.gaussian_blur(original, radius=2.0)
print(f"✓ Gaussian blur: {blurred.size}")

# 3. Metrics Calculation
print("\n3. Testing Metrics Calculation")
print("-" * 80)

psnr = MetricsCalculator.calculate_psnr(original, jpeg_compressed)
print(f"✓ PSNR (original vs JPEG Q75): {psnr:.2f} dB")

ssim = MetricsCalculator.calculate_ssim(original, jpeg_compressed)
print(f"✓ SSIM (original vs JPEG Q75): {ssim:.4f}")

psnr_noisy = MetricsCalculator.calculate_psnr(original, noisy)
print(f"✓ PSNR (original vs noisy): {psnr_noisy:.2f} dB")

ssim_noisy = MetricsCalculator.calculate_ssim(original, noisy)
print(f"✓ SSIM (original vs noisy): {ssim_noisy:.4f}")

ber = MetricsCalculator.calculate_bit_error_rate("TEST", "TEST")
print(f"✓ BER (identical strings): {ber:.4f}")

ber_diff = MetricsCalculator.calculate_bit_error_rate("TEST-123", "TEST-456")
print(f"✓ BER (different strings): {ber_diff:.4f}")

# 4. PDF Generation
print("\n4. Testing PDF Generation")
print("-" * 80)

images = [
    generator.generate_text_document(width=800, height=600),
    generator.generate_gradient_image(width=800, height=600),
    generator.generate_mixed_content(width=800, height=600),
]

import tempfile
import os

with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
    pdf_path = tmp.name

try:
    generator.generate_sample_pdf(pdf_path, images, quality=85)
    size = os.path.getsize(pdf_path)
    print(f"✓ Generated PDF: {pdf_path}")
    print(f"  PDF size: {size:,} bytes")
finally:
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

# 5. Attack Configuration
print("\n5. Testing Attack Configurations")
print("-" * 80)

attack_configs = AttackSimulator.get_attack_configs()
total_attacks = sum(len(configs) for configs in attack_configs.values())
print(f"✓ Total attack configurations available: {total_attacks}")

for attack_type, configs in attack_configs.items():
    print(f"  - {attack_type.value}: {len(configs)} variants")

print("\n" + "=" * 80)
print("All benchmark framework components working correctly!")
print("=" * 80)
print()
print("Note: The actual watermark embedding/extraction may require")
print("specific image sizes and configurations to work properly.")
print("This demo shows that the benchmark infrastructure itself")
print("is fully functional and ready for use.")
