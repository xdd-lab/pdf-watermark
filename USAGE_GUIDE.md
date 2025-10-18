# 使用指南

本指南详细介绍如何在各种场景下使用 PDF 全盲水印系统。

## 目录

1. [基础使用](#基础使用)
2. [高级配置](#高级配置)
3. [常见场景](#常见场景)
4. [故障排查](#故障排查)
5. [最佳实践](#最佳实践)

## 基础使用

### 1. 快速开始

最简单的嵌入和提取示例：

```python
from pdf_blind_watermark import PDFWatermarker

watermarker = PDFWatermarker()

# 嵌入
watermarker.embed(
    input_pdf="document.pdf",
    output_pdf="watermarked.pdf",
    watermark_text="SECRET-2024"
)

# 提取
text = watermarker.extract(
    input_file="watermarked.pdf",
    source_type="pdf"
)
print(f"Watermark: {text}")
```

### 2. 命令行快速使用

```bash
# 嵌入
python -m pdf_blind_watermark embed -i input.pdf -o output.pdf -w "MY-WATERMARK"

# 提取
python -m pdf_blind_watermark extract -i output.pdf -t pdf
```

## 高级配置

### 自定义参数

通过 `WatermarkConfig` 调整各项参数：

```python
from pdf_blind_watermark import PDFWatermarker
from pdf_blind_watermark.core.watermark import WatermarkConfig

config = WatermarkConfig(
    wavelet="haar",           # 小波类型
    block_size=8,             # DCT 块大小
    embed_strength=12.0,      # 水印强度
    ecc_symbols=32,           # 纠错符号数
    dpi=180,                  # PDF 渲染分辨率
    quality=85,               # 输出质量
    rectify=True              # 是否校正透视
)

watermarker = PDFWatermarker(config)
```

### 参数含义详解

#### `embed_strength` (水印强度)

- **作用**：控制水印在频域系数上的调制幅度
- **取值范围**：8.0 - 20.0
- **推荐值**：
  - 10.0：适用于内部文档，不会遭受严重攻击
  - 12.0：日常使用的平衡值
  - 14.0-16.0：需要抵御压缩、截图等攻击
  - 18.0+：极端场景（可能出现轻微可见痕迹）

#### `ecc_symbols` (纠错符号数)

- **作用**：Reed-Solomon 编码的冗余度
- **取值范围**：8 - 64
- **推荐值**：
  - 16：快速嵌入，轻度纠错
  - 32：标准配置
  - 48-64：高噪声环境

#### `dpi` (渲染分辨率)

- **作用**：PDF 转图像时的分辨率
- **取值范围**：100 - 300
- **推荐值**：
  - 120-150：低分辨率，快速处理
  - 180：标准配置
  - 200-220：高分辨率，更强鲁棒性

#### `quality` (输出质量)

- **作用**：PDF 内 JPEG 图像的压缩质量
- **取值范围**：70 - 95
- **推荐值**：
  - 75-80：文件较小
  - 85：标准配置
  - 90-95：高质量，文件较大

## 常见场景

### 场景 1：合同文档防泄露

**需求**：内部合同文档，需追踪泄露源头，预期只会被截图

```python
config = WatermarkConfig(
    embed_strength=12.0,
    ecc_symbols=32,
    dpi=150,
    quality=85
)

watermarker = PDFWatermarker(config)

# 为每份合同生成唯一水印
user_id = "USER-12345"
timestamp = "2024-10-18"
watermark = f"{user_id}-{timestamp}"

watermarker.embed("contract.pdf", "contract_watermarked.pdf", watermark)
```

### 场景 2：高安全性文档（可能被打印拍照）

**需求**：机密文档，可能被打印后拍照，需要极高鲁棒性

```python
config = WatermarkConfig(
    embed_strength=16.0,
    ecc_symbols=48,
    dpi=200,
    quality=90
)

watermarker = PDFWatermarker(config)
watermarker.embed("secret.pdf", "secret_watermarked.pdf", "TOP-SECRET-001")
```

### 场景 3：批量处理（性能优先）

**需求**：大量文档需要批量嵌入，要求速度快

```python
config = WatermarkConfig(
    embed_strength=10.0,
    ecc_symbols=16,
    dpi=120,
    quality=75
)

watermarker = PDFWatermarker(config)

import os
from pathlib import Path

input_dir = Path("./documents")
output_dir = Path("./watermarked")
output_dir.mkdir(exist_ok=True)

for pdf_file in input_dir.glob("*.pdf"):
    output_file = output_dir / pdf_file.name
    try:
        watermarker.embed(
            str(pdf_file),
            str(output_file),
            "COMPANY-INTERNAL",
            max_pages=10  # 仅处理前 10 页
        )
        print(f"✓ {pdf_file.name}")
    except Exception as e:
        print(f"✗ {pdf_file.name}: {e}")
```

### 场景 4：从拍照图像提取水印

**需求**：用户用手机拍摄了文档，从照片中提取水印

```python
config = WatermarkConfig(
    rectify=True,  # 启用透视校正
    dpi=180
)

watermarker = PDFWatermarker(config)

try:
    watermark = watermarker.extract(
        input_file="photo.jpg",
        source_type="image"
    )
    print(f"提取成功: {watermark}")
except Exception as e:
    print(f"提取失败: {e}")
```

## 故障排查

### 问题 1：提取失败 "Preamble not found"

**原因**：
- 水印强度过低，被攻击破坏
- 图像经过严重压缩或模糊
- 水印未正确嵌入

**解决方法**：
1. 提高 `embed_strength` (如 14.0-16.0)
2. 增加 `ecc_symbols` (如 48)
3. 提高 `dpi` (如 180-200)

### 问题 2：输出文件过大

**原因**：
- DPI 设置过高
- Quality 设置过高

**解决方法**：
1. 降低 `dpi` 至 150 或更低
2. 降低 `quality` 至 75-80
3. 限制处理页数 (`max_pages`)

### 问题 3：嵌入后水印可见

**原因**：
- `embed_strength` 设置过高

**解决方法**：
1. 降低 `embed_strength` (如 10.0-12.0)
2. 确认图像质量足够（DPI 不要过低）

### 问题 4：处理速度太慢

**原因**：
- 文档页数过多
- DPI 设置过高
- 纠错符号数过多

**解决方法**：
1. 使用 `max_pages` 限制处理页数
2. 降低 `dpi` (如 120-150)
3. 减少 `ecc_symbols` (如 16-24)

## 最佳实践

### 1. 水印文本格式建议

```python
# 推荐格式：
# 用户ID-时间戳
watermark = f"USER{user_id}-{timestamp}"

# 或包含部门信息：
watermark = f"{department}-{user_id}-{date}"

# 示例：
# "SALES-U1234-20241018"
# "HR-U5678-2024Q4"
```

### 2. 生产环境配置建议

```python
# 标准配置（推荐）
config = WatermarkConfig(
    embed_strength=12.0,
    ecc_symbols=32,
    dpi=150,
    quality=85
)

# 配合日志记录
import logging
logging.basicConfig(level=logging.INFO)

watermarker = PDFWatermarker(config)
```

### 3. 水印验证流程

```python
def verify_watermark(pdf_path: str, expected_watermark: str) -> bool:
    """验证水印是否正确"""
    watermarker = PDFWatermarker()
    try:
        extracted = watermarker.extract(pdf_path, source_type="pdf")
        return extracted == expected_watermark
    except:
        return False

# 使用示例
if verify_watermark("document.pdf", "USER-123-2024"):
    print("Water mark verified!")
else:
    print("Watermark mismatch or missing!")
```

### 4. 错误处理

```python
from pdf_blind_watermark import PDFWatermarker
from pdf_blind_watermark.core.watermark import WatermarkingError

watermarker = PDFWatermarker()

try:
    watermarker.embed("input.pdf", "output.pdf", "WATERMARK")
except WatermarkingError as e:
    print(f"Watermarking error: {e}")
except FileNotFoundError:
    print("Input file not found")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 5. 性能优化技巧

- **限制页数**：只处理关键页面
- **并行处理**：多个文档使用多进程
- **缓存配置**：重复使用同一 `PDFWatermarker` 实例
- **预检查**：处理前检查文件大小和页数

## 安全建议

1. **水印保密**：不要在公开场合展示水印内容格式
2. **动态水印**：为每个用户/文档生成唯一水印
3. **日志审计**：记录所有嵌入和提取操作
4. **定期测试**：定期测试水印提取成功率
5. **多层防护**：水印只是防护措施之一，应配合其他安全措施

## 常见问题 (FAQ)

**Q: 水印会被完全去除吗？**  
A: 理论上不会，因为水印嵌入在频域。但极端破坏（如重新排版、OCR 重建）可能导致水印丢失。

**Q: 可以嵌入多长的文本？**  
A: 技术上支持 65,535 字节，但推荐不超过 50 个字符以提高鲁棒性。

**Q: 支持哪些图像格式提取？**  
A: 支持 JPEG、PNG、BMP 等常见格式。

**Q: 可以从扫描的纸质文档提取吗？**  
A: 有可能，但成功率取决于扫描质量和水印强度。建议使用 `embed_strength >= 16.0`。

**Q: 系统开源吗？**  
A: 是的，采用 MIT License。
