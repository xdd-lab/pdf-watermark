from .core.watermark import PDFWatermarker
from .benchmark.runner import BenchmarkRunner
from .benchmark.attacks import AttackSimulator, AttackType
from .benchmark.metrics import MetricsCalculator
from .benchmark.sample_generator import SampleGenerator

__version__ = "1.0.0"
__all__ = [
    "PDFWatermarker",
    "BenchmarkRunner",
    "AttackSimulator",
    "AttackType",
    "MetricsCalculator",
    "SampleGenerator",
]
