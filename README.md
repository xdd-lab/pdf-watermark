# PDF 全盲水印系统

一个面向企业文档安全场景的 **PDF 全盲水印系统**，可在不依赖原始文档的情况下，从截屏、拍照等图像中准确提取水印。系统在保证视觉无感知的同时，重点兼顾鲁棒性、性能以及生成文件体积。

## 核心特性

- ✅ **频域全盲水印**：基于 DWT + DCT 的混合频域嵌入策略
- ✅ **高鲁棒性**：对截图、拍照、压缩、缩放、轻度旋转等操作具有良好抵抗力
- ✅ **高保真度**：仅修改 Y 通道亮度子带，最大化视觉不可见性
- ✅ **全盲提取**：无需原图即可恢复水印内容
- ✅ **纠错加固**：集成 Reed-Solomon 纠错，抵御噪声与失真
- ✅ **透视校正**：自动检测页面边界，矫正拍照带来的透视畸变
- ✅ **灵活配置**：可调节水印强度、嵌入分块大小、PDF 输出质量等参数

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
pytest tests/test_watermark.py
```

> 测试使用合成图像，可根据实际业务场景扩展更多鲁棒性测试脚本。

## 开源协议

本项目采用 MIT License。
