from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import cv2
import numpy as np
from PIL import Image


@dataclass
class BenchmarkMetrics:
    """Metrics for a single benchmark run."""

    attack_type: str
    attack_params: str
    success: bool
    extracted_text: Optional[str] = None
    expected_text: Optional[str] = None
    bit_error_rate: Optional[float] = None
    psnr: Optional[float] = None
    ssim: Optional[float] = None
    extraction_time: Optional[float] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert metrics to dictionary."""
        return {
            "attack_type": self.attack_type,
            "attack_params": self.attack_params,
            "success": self.success,
            "extracted_text": self.extracted_text,
            "expected_text": self.expected_text,
            "bit_error_rate": self.bit_error_rate,
            "psnr": self.psnr,
            "ssim": self.ssim,
            "extraction_time": self.extraction_time,
            "error_message": self.error_message,
        }


@dataclass
class AggregatedMetrics:
    """Aggregated metrics across multiple runs."""

    total_runs: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    success_rate: float = 0.0
    avg_psnr: Optional[float] = None
    avg_ssim: Optional[float] = None
    avg_ber: Optional[float] = None
    avg_extraction_time: Optional[float] = None
    metrics_by_attack: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert aggregated metrics to dictionary."""
        return {
            "total_runs": self.total_runs,
            "successful_extractions": self.successful_extractions,
            "failed_extractions": self.failed_extractions,
            "success_rate": self.success_rate,
            "avg_psnr": self.avg_psnr,
            "avg_ssim": self.avg_ssim,
            "avg_ber": self.avg_ber,
            "avg_extraction_time": self.avg_extraction_time,
            "metrics_by_attack": self.metrics_by_attack,
        }


class MetricsCalculator:
    """Calculate image quality and extraction metrics."""

    @staticmethod
    def calculate_psnr(original: Image.Image, modified: Image.Image) -> float:
        """Calculate Peak Signal-to-Noise Ratio.

        Args:
            original: Original image
            modified: Modified image

        Returns:
            PSNR value in dB (higher is better)
        """
        if original.size != modified.size:
            modified = modified.resize(original.size, Image.LANCZOS)

        orig_array = np.array(original, dtype=np.float64)
        mod_array = np.array(modified, dtype=np.float64)

        mse = np.mean((orig_array - mod_array) ** 2)
        if mse == 0:
            return float("inf")

        max_pixel = 255.0
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
        return float(psnr)

    @staticmethod
    def calculate_ssim(original: Image.Image, modified: Image.Image) -> float:
        """Calculate Structural Similarity Index.

        Args:
            original: Original image
            modified: Modified image

        Returns:
            SSIM value (0-1, higher is better)
        """
        if original.size != modified.size:
            modified = modified.resize(original.size, Image.LANCZOS)

        orig_gray = cv2.cvtColor(np.array(original), cv2.COLOR_RGB2GRAY)
        mod_gray = cv2.cvtColor(np.array(modified), cv2.COLOR_RGB2GRAY)

        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2

        orig_gray = orig_gray.astype(np.float64)
        mod_gray = mod_gray.astype(np.float64)

        mu1 = cv2.GaussianBlur(orig_gray, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(mod_gray, (11, 11), 1.5)

        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2

        sigma1_sq = cv2.GaussianBlur(orig_gray ** 2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(mod_gray ** 2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(orig_gray * mod_gray, (11, 11), 1.5) - mu1_mu2

        ssim_map = ((2 * mu1_mu2 + c1) * (2 * sigma12 + c2)) / (
            (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2)
        )

        return float(ssim_map.mean())

    @staticmethod
    def calculate_bit_error_rate(expected: str, extracted: str) -> float:
        """Calculate bit error rate between expected and extracted text.

        Args:
            expected: Expected text
            extracted: Extracted text

        Returns:
            BER (0-1, lower is better)
        """
        expected_bytes = expected.encode("utf-8")
        extracted_bytes = extracted.encode("utf-8")

        max_len = max(len(expected_bytes), len(extracted_bytes))
        expected_bytes = expected_bytes.ljust(max_len, b"\x00")
        extracted_bytes = extracted_bytes.ljust(max_len, b"\x00")

        total_bits = max_len * 8
        error_bits = 0

        for e_byte, x_byte in zip(expected_bytes, extracted_bytes):
            xor = e_byte ^ x_byte
            error_bits += bin(xor).count("1")

        return error_bits / total_bits if total_bits > 0 else 0.0

    @staticmethod
    def aggregate_metrics(metrics_list: List[BenchmarkMetrics]) -> AggregatedMetrics:
        """Aggregate metrics from multiple benchmark runs.

        Args:
            metrics_list: List of BenchmarkMetrics

        Returns:
            AggregatedMetrics with aggregated statistics
        """
        if not metrics_list:
            return AggregatedMetrics()

        total_runs = len(metrics_list)
        successful = sum(1 for m in metrics_list if m.success)
        failed = total_runs - successful

        psnr_values = [m.psnr for m in metrics_list if m.psnr is not None]
        ssim_values = [m.ssim for m in metrics_list if m.ssim is not None]
        ber_values = [m.bit_error_rate for m in metrics_list if m.bit_error_rate is not None]
        time_values = [m.extraction_time for m in metrics_list if m.extraction_time is not None]

        metrics_by_attack = {}
        for metric in metrics_list:
            attack_key = f"{metric.attack_type}:{metric.attack_params}"
            if attack_key not in metrics_by_attack:
                metrics_by_attack[attack_key] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "success_rate": 0.0,
                }
            metrics_by_attack[attack_key]["total"] += 1
            if metric.success:
                metrics_by_attack[attack_key]["successful"] += 1
            else:
                metrics_by_attack[attack_key]["failed"] += 1

        for attack_key in metrics_by_attack:
            stats = metrics_by_attack[attack_key]
            stats["success_rate"] = stats["successful"] / stats["total"] if stats["total"] > 0 else 0.0

        return AggregatedMetrics(
            total_runs=total_runs,
            successful_extractions=successful,
            failed_extractions=failed,
            success_rate=successful / total_runs if total_runs > 0 else 0.0,
            avg_psnr=sum(psnr_values) / len(psnr_values) if psnr_values else None,
            avg_ssim=sum(ssim_values) / len(ssim_values) if ssim_values else None,
            avg_ber=sum(ber_values) / len(ber_values) if ber_values else None,
            avg_extraction_time=sum(time_values) / len(time_values) if time_values else None,
            metrics_by_attack=metrics_by_attack,
        )
