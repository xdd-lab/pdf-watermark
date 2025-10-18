# PDF 全盲水印系统

一个面向企业文档安全场景的 **PDF 全盲水印系统**，可在不依赖原始文档的情况下，从截屏、拍照等图像中准确提取水印。系统在保证视觉无感知的同时，重点兼顾鲁棒性、性能以及生成文件体积。

此外，系统还提供 **PDF 文本隐写术模块**，可通过零宽字符和隐形文本将结构化元数据（用户 ID、时间戳、追踪令牌）隐藏到 PDF 文档中。

## 核心特性

### 图像水印（DWT + DCT）

- ✅ **频域全盲水印**：基于 DWT + DCT 的混合频域嵌入策略
- ✅ **高鲁棒性**：对截图、拍照、压缩、缩放、轻度旋转等操作具有良好抵抗力
- ✅ **高保真度**：仅修改 Y 通道亮度子带，最大化视觉不可见性
- ✅ **全盲提取**：无需原图即可恢复水印内容
- ✅ **纠错加固**：集成 Reed-Solomon 纠错，抵御噪声与失真
- ✅ **透视校正**：自动检测页面边界，矫正拍照带来的透视畸变
- ✅ **灵活配置**：可调节水印强度、嵌入分块大小、PDF 输出质量等参数

### 文本隐写术（Zero-Width Characters）

- ✅ **隐形嵌入**：使用零宽 Unicode 字符进行隐写编码
- ✅ **结构化元数据**：支持用户 ID、时间戳、追踪令牌及自定义字段
- ✅ **可选压缩**：zlib 压缩减少元数据体积
- ✅ **纠错编码**：Reed-Solomon 纠错提高对文档编辑的容错性
- ✅ **多页支持**：在多页 PDF 中分散嵌入元数据
- ✅ **容量分析**：嵌入前检查 PDF 容量

## 技术原理概览

1. **颜色空间转换**：将页面转换至 YCbCr，仅在亮度通道上操作
2. **小波分解**：对 Y 通道执行一次离散小波变换 (DWT)，选取水平方向细节子带 (LH)
3. **块级 DCT**：将 LH 子带划分为 8×8 块，并进行离散余弦变换 (DCT)
4. **双系数调制**：对中频系数对 (2,3) 与 (3,2) 进行差值调制，以表示比特 0/1
5. **位流构造**：将水印文本编码为字节后，添加长度信息与 RS 纠错冗余，再转为比特序列
6. **冗余嵌入**：在可用块范围内循环写入同一位流，提高抗干扰能力
7. **提取阶段**：逆序执行 DWT+DCT 并读取系数差值，重建位流并完成纠错解码

## 安装

```bash
pip install -r requirements.txt
```

> 依赖列表：`numpy`, `opencv-python`, `Pillow`, `PyWavelets`, `PyMuPDF`, `reedsolo`, `click`, `tqdm`

## Python API 快速开始

```python
from pdf_blind_watermark import PDFWatermarker
from pdf_blind_watermark.core.watermark import WatermarkConfig

config = WatermarkConfig(
    embed_strength=12.0,  # 水印强度（数值越大鲁棒性越强，但过高可能带来轻微失真）
    quality=85,           # 导出 PDF 的 JPEG 压缩质量
    dpi=180               # PDF 渲染分辨率
)

watermarker = PDFWatermarker(config)

# 1. 嵌入水印
watermarker.embed(
    input_pdf="original.pdf",
    output_pdf="watermarked.pdf",
    watermark_text="ACME-SECURE-2024"
)

# 2. 从 PDF 提取水印
text = watermarker.extract(
    input_file="watermarked.pdf",
    source_type="pdf"
)
print(text)

# 3. 从截图/拍照提取水印
text = watermarker.extract(
    input_file="photo.jpg",
    source_type="image"
)
print(text)
```

### 文本隐写术 API

```python
from pdf_blind_watermark import PDFSteganography, StegoMetadata

# 初始化隐写引擎
stego = PDFSteganography(
    use_compression=True,
    use_ecc=True,
    ecc_symbols=32
)

# 创建元数据
metadata = StegoMetadata.create(
    user_id="user_12345",
    tracking_token="abc123xyz789"
)

# 嵌入元数据
stego.embed(
    input_pdf="original.pdf",
    output_pdf="tracked.pdf",
    metadata=metadata
)

# 提取元数据
extracted = stego.extract("tracked.pdf")
print(f"User: {extracted.user_id}")
print(f"Token: {extracted.tracking_token}")
print(f"Timestamp: {extracted.timestamp}")

# 检查容量
capacity = stego.get_capacity_info("document.pdf")
print(f"Estimated capacity: {capacity.estimated_capacity_bytes} bytes")
```

详细文档请参阅 [STEGANOGRAPHY.md](STEGANOGRAPHY.md)

## 命令行用法

```bash
# 嵌入水印
python -m pdf_blind_watermark embed -i input.pdf -o output.pdf -w "Secret-123"

# 从 PDF 提取
python -m pdf_blind_watermark extract -i watermarked.pdf -t pdf

# 从图像提取
python -m pdf_blind_watermark extract -i photo.jpg -t image

# 批量嵌入
python -m pdf_blind_watermark batch-embed -d ./pdfs -o ./output -w "Secret"
```

命令行参数支持调节水印强度、DPI、输出质量，以及是否启用透视校正等。

## 参数说明

### `WatermarkConfig`

| 参数              | 说明                                      | 推荐值 |
|-------------------|-------------------------------------------|--------|
| `wavelet`         | 小波基函数名称                            | `"haar"` |
| `block_size`      | DCT 分块尺寸                              | `8` |
| `embed_strength`  | 水印强度（越大越鲁棒，过大可能稍显痕迹） | `10 ~ 16` |
| `ecc_symbols`     | Reed-Solomon 纠错符号个数                 | `32` |
| `dpi`             | PDF 渲染分辨率 (内置 PDF 处理使用)        | `150 ~ 220` |
| `quality`         | 输出 PDF JPEG 压缩质量                    | `80 ~ 90` |
| `rectify`         | 图像提取是否执行透视校正                  | `True` |

## 适用场景与限制

- 推荐用于电子合同、财务报表、知识产权资料等需要追溯来源的 PDF 文档
- 对极端破坏（如打印后大幅缩放、重压缩、剧烈模糊）仍可能失效，可通过增大 `embed_strength` 与 `ecc_symbols` 提升冗余
- 单页图像尺寸越大，可用嵌入块越多，鲁棒性越好

## 项目结构

```
pdf_blind_watermark/
├── core/
│   ├── dwt_watermark.py   # 备用的 DWT 水印实现（示例）
│   ├── error_correction.py # Reed-Solomon 纠错封装
│   └── watermark.py       # 主水印逻辑（DWT + DCT）
├── steganography/
│   ├── text_encoder.py    # 零宽字符编码/解码
│   ├── pdf_stego.py       # PDF 文本隐写主逻辑
│   ├── metadata.py        # 结构化元数据
│   └── capacity.py        # 容量分析
├── pdf/
│   └── processor.py       # 基于 PyMuPDF 的 PDF 渲染与生成
├── image/
│   └── processor.py       # 图像加载、预处理及透视校正
├── utils/
│   └── helpers.py         # 位流、编码等工具函数
├── cli.py                 # 命令行接口
└── __main__.py            # `python -m pdf_blind_watermark`
```

## 测试

项目包含基础单元测试，验证嵌入与提取的闭环正确性：

```bash
# 图像水印测试
pytest tests/test_watermark.py

# 文本隐写术测试
pytest tests/test_text_encoder.py
pytest tests/test_metadata.py
pytest tests/test_capacity.py
pytest tests/test_pdf_steganography.py

# 运行所有测试
pytest tests/
```

> 测试使用合成图像和 PDF，可根据实际业务场景扩展更多鲁棒性测试脚本。

## 开源协议

本项目采用 MIT License。
