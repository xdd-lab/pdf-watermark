from __future__ import annotations

import os
from pathlib import Path

import click

from .core.watermark import PDFWatermarker, WatermarkConfig, WatermarkingError


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
@click.option("--enable-stego", is_flag=True, help="启用文本隐写术")
@click.option("--stego-text", default=None, help="隐写文本内容 (需启用 --enable-stego)")
@click.option("--stego-ecc", default=16, type=int, help="隐写术纠错符号数 (默认16)")
@click.option("--parallel/--no-parallel", default=True, help="启用并行处理 (默认启用)")
@click.option("--parallel-threshold", default=3, type=int, help="启用并行的最小页数 (默认3)")
def embed(input_pdf, output_pdf, watermark_text, strength, quality, dpi, max_pages, enable_stego, stego_text, stego_ecc, parallel, parallel_threshold):
    """嵌入水印到PDF"""
    try:
        config = WatermarkConfig(
            embed_strength=strength,
            quality=quality,
            dpi=dpi,
            enable_steganography=enable_stego,
            stego_ecc_symbols=stego_ecc,
            enable_parallel=parallel,
            parallel_threshold=parallel_threshold,
        )
        watermarker = PDFWatermarker(config)

        click.echo(f"正在嵌入水印: {watermark_text}")
        if enable_stego and stego_text:
            click.echo(f"正在嵌入隐写文本: {stego_text}")
        watermarker.embed(input_pdf, output_pdf, watermark_text, max_pages=max_pages, stego_text=stego_text)
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
@click.option("--enable-stego", is_flag=True, help="启用文本隐写术提取")
@click.option("--show-details", is_flag=True, help="显示详细提取信息")
def extract(input_file, source_type, max_pages, rectify, dpi, enable_stego, show_details):
    """从PDF或图像提取水印"""
    try:
        config = WatermarkConfig(rectify=rectify, dpi=dpi, enable_steganography=enable_stego)
        watermarker = PDFWatermarker(config)

        click.echo(f"正在从 {source_type.upper()} 提取水印...")
        result = watermarker.extract(input_file, source_type=source_type, max_pages=max_pages, return_dict=True)
        
        if show_details:
            click.echo(f"✓ 提取结果:")
            click.echo(f"  水印文本: {result.watermark_text}")
            if enable_stego:
                if result.stego_text:
                    click.echo(f"  隐写文本: {result.stego_text}")
                elif result.stego_error:
                    click.echo(f"  隐写提取失败: {result.stego_error}")
                else:
                    click.echo(f"  隐写文本: (未找到)")
        else:
            click.echo(f"✓ 提取的水印: {result.watermark_text}")
            if enable_stego and result.stego_text:
                click.echo(f"✓ 隐写文本: {result.stego_text}")

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


if __name__ == "__main__":
    cli()
