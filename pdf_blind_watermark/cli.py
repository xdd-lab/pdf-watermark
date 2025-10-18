from __future__ import annotations

import os
from pathlib import Path

import click

from .core.watermark import PDFWatermarker, WatermarkConfig, WatermarkingError


@click.group()
def cli():
    """PDF全盲水印系统 - 嵌入和提取水印，包含基准测试功能"""
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
@click.option("-o", "--output", "output_dir", default="./benchmark_results", help="基准测试结果输出目录")
@click.option("--format", "report_format", type=click.Choice(["html", "json", "markdown"]), default="html", help="报告格式")
@click.option("--suite", type=click.Choice(["performance", "robustness", "full"]), default="full", help="测试套件类型")
def benchmark(output_dir, report_format, suite):
    """运行基准测试套件并生成报告"""
    try:
        from .benchmark import BenchmarkSuite
        
        click.echo("=" * 60)
        click.echo("PDF 全盲水印系统 - 基准测试")
        click.echo("=" * 60)
        
        bench_suite = BenchmarkSuite(output_dir=output_dir)
        
        if suite in ["performance", "full"]:
            click.echo("\n运行性能基准测试...")
            bench_suite.run_standard_suite()
        
        if suite in ["robustness", "full"]:
            click.echo("\n运行鲁棒性测试...")
            bench_suite.run_robustness_suite()
        
        click.echo("\n生成报告...")
        report_path = bench_suite.generate_report(report_format)
        click.echo(f"✓ 报告已生成: {report_path}")
        
    except ImportError:
        click.echo("✗ 基准测试模块未安装。请确保所有依赖已安装。", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"✗ 错误: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
