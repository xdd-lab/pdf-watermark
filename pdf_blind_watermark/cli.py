from __future__ import annotations

import os
from pathlib import Path

import click

from .core.watermark import PDFWatermarker, WatermarkConfig, WatermarkingError
from .benchmark.runner import BenchmarkRunner
from .benchmark.attacks import AttackType


@click.group()
def cli():
    """PDF全盲水印系统 - 嵌入和提取水印"""
    pass


@cli.command()
@click.option("-i", "--input", "input_pdf", required=True, type=click.Path(exists=True), help="输入PDF文件路径")
@click.option("-o", "--output", "output_pdf", required=True, type=click.Path(), help="输出PDF文件路径")
@click.option("-w", "--watermark", "watermark_text", required=True, help="水印文本内容")
@click.option("--strength", default=12.0, type=float, help="水印强度 (8-20, 默认12)")
@click.option("--quality", default=85, type=int, help="输出质量 (70-95, 默认85)")
@click.option("--dpi", default=180, type=int, help="DPI分辨率 (默认180)")
@click.option("--max-pages", default=None, type=int, help="最大处理页数 (默认全部)")
def embed(input_pdf, output_pdf, watermark_text, strength, quality, dpi, max_pages):
    """嵌入水印到PDF"""
    try:
        config = WatermarkConfig(
            embed_strength=strength,
            quality=quality,
            dpi=dpi,
        )
        watermarker = PDFWatermarker(config)

        click.echo(f"正在嵌入水印: {watermark_text}")
        watermarker.embed(input_pdf, output_pdf, watermark_text, max_pages=max_pages)
        click.echo(f"✓ 水印已嵌入到: {output_pdf}")

    except WatermarkingError as e:
        click.echo(f"✗ 错误: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"✗ 未知错误: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option("-i", "--input", "input_file", required=True, type=click.Path(exists=True), help="输入文件路径")
@click.option("-t", "--type", "source_type", default="pdf", type=click.Choice(["pdf", "image"]), help="输入类型")
@click.option("--max-pages", default=None, type=int, help="最大处理页数 (仅PDF)")
@click.option("--rectify/--no-rectify", default=True, help="是否进行透视校正 (仅图像)")
@click.option("--dpi", default=180, type=int, help="DPI分辨率 (仅PDF)")
def extract(input_file, source_type, max_pages, rectify, dpi):
    """从PDF或图像提取水印"""
    try:
        config = WatermarkConfig(rectify=rectify, dpi=dpi)
        watermarker = PDFWatermarker(config)

        click.echo(f"正在从 {source_type.upper()} 提取水印...")
        watermark = watermarker.extract(input_file, source_type=source_type, max_pages=max_pages)
        click.echo(f"✓ 提取的水印: {watermark}")

    except WatermarkingError as e:
        click.echo(f"✗ 错误: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"✗ 未知错误: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option("-d", "--directory", required=True, type=click.Path(exists=True), help="输入PDF目录")
@click.option("-o", "--output", "output_dir", required=True, type=click.Path(), help="输出目录")
@click.option("-w", "--watermark", "watermark_text", required=True, help="水印文本内容")
@click.option("--strength", default=12.0, type=float, help="水印强度 (8-20)")
@click.option("--quality", default=85, type=int, help="输出质量 (70-95)")
@click.option("--dpi", default=180, type=int, help="DPI分辨率")
def batch_embed(directory, output_dir, watermark_text, strength, quality, dpi):
    """批量嵌入水印到目录中的所有PDF"""
    try:
        config = WatermarkConfig(embed_strength=strength, quality=quality, dpi=dpi)
        watermarker = PDFWatermarker(config)

        input_path = Path(directory)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        pdf_files = list(input_path.glob("*.pdf"))
        if not pdf_files:
            click.echo("未找到PDF文件。")
            return

        click.echo(f"找到 {len(pdf_files)} 个PDF文件")

        for pdf_file in pdf_files:
            output_file = output_path / pdf_file.name
            try:
                click.echo(f"处理: {pdf_file.name}...")
                watermarker.embed(str(pdf_file), str(output_file), watermark_text)
                click.echo(f"  ✓ 完成")
            except Exception as e:
                click.echo(f"  ✗ 失败: {e}")

        click.echo(f"✓ 批量处理完成，输出目录: {output_dir}")

    except Exception as e:
        click.echo(f"✗ 错误: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option("-o", "--output", "output_dir", default="./benchmark_results", help="Output directory for results")
@click.option("-w", "--watermark", "watermark_text", default="BENCHMARK-2024", help="Watermark text")
@click.option("--strength", default=12.0, type=float, help="Watermark strength (8-20)")
@click.option("--mode", type=click.Choice(["quick", "full"]), default="quick", help="Benchmark mode")
@click.option("--num-images", default=3, type=int, help="Number of images for full benchmark")
@click.option(
    "--attacks",
    multiple=True,
    type=click.Choice([a.value for a in AttackType]),
    help="Specific attack types to test (can specify multiple)",
)
def benchmark(output_dir, watermark_text, strength, mode, num_images, attacks):
    """Run robustness and invisibility benchmark suite"""
    try:
        config = WatermarkConfig(embed_strength=strength)
        runner = BenchmarkRunner(config=config, output_dir=output_dir)

        click.echo(f"Starting {mode} benchmark...")
        click.echo(f"Watermark strength: {strength}")
        click.echo(f"Output directory: {output_dir}")

        attack_types = None
        if attacks:
            attack_types = [AttackType(a) for a in attacks]
            click.echo(f"Testing attack types: {', '.join(attacks)}")

        if mode == "quick":
            aggregated = runner.run_quick_benchmark(
                watermark_text=watermark_text, save_results=True
            )
            click.echo("\n" + "=" * 60)
            click.echo("Quick Benchmark Results:")
            click.echo("=" * 60)
            click.echo(f"Total runs: {aggregated.total_runs}")
            click.echo(f"Success rate: {aggregated.success_rate:.2%}")
            if aggregated.avg_psnr:
                click.echo(f"Average PSNR: {aggregated.avg_psnr:.2f} dB")
            if aggregated.avg_ssim:
                click.echo(f"Average SSIM: {aggregated.avg_ssim:.4f}")
            click.echo("=" * 60)

        else:
            results = runner.run_full_benchmark(
                num_images=num_images, watermark_text=watermark_text, save_results=True
            )
            click.echo("\n" + "=" * 60)
            click.echo("Full Benchmark Results:")
            click.echo("=" * 60)
            for idx, aggregated in results.items():
                click.echo(f"\nImage {idx + 1}:")
                click.echo(f"  Success rate: {aggregated.success_rate:.2%}")
                if aggregated.avg_psnr:
                    click.echo(f"  Average PSNR: {aggregated.avg_psnr:.2f} dB")
                if aggregated.avg_ssim:
                    click.echo(f"  Average SSIM: {aggregated.avg_ssim:.4f}")
            click.echo("=" * 60)

        click.echo(f"\n✓ Benchmark complete. Results saved to: {output_dir}")

    except Exception as e:
        click.echo(f"✗ Benchmark failed: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
