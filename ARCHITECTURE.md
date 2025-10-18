# 系统架构设计文档

## 概述

本文档描述 PDF 全盲水印系统的技术架构、核心算法和实现细节。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐        │
│  │PDFWatermarker│  │    CLI      │  │Python Package│        │
│  └─────────────┘  └─────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                     Core Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐       │
│  │  Watermark   │  │ErrorCorrection│ │DWTWatermark │       │
│  │   Engine     │  │   (RS Code)   │ │  (Backup)   │       │
│  └──────────────┘  └──────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Processing Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐       │
│  │PDFProcessor  │  │ImageProcessor│  │  Helpers    │       │
│  │  (PyMuPDF)   │  │  (CV+Pillow) │  │  (Utils)    │       │
│  └──────────────┘  └──────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 核心模块

### 1. 水印引擎 (watermark.py)

**核心类**: `PDFWatermarker`

**职责**:
- 协调水印嵌入和提取流程
- 管理配置参数
- 处理多页 PDF 的水印操作

**主要方法**:
```python
embed(input_pdf, output_pdf, watermark_text, max_pages)
extract(input_file, source_type, max_pages)
embed_image(image, watermark_text)
extract_from_image(image)
```

**算法流程**:

#### 嵌入流程
```
1. 读取 PDF 页面 → 渲染为图像
2. 颜色空间转换: RGB → YCbCr
3. 提取 Y 通道（亮度）
4. 对 Y 通道执行 DWT (Haar 小波)
   - 获取 LH (水平细节) 子带
5. 将 LH 子带划分为 8×8 块
6. 对每个块执行 DCT
7. 修改中频系数对 (2,3) 和 (3,2):
   - bit = 1: 确保 coeff[2,3] > coeff[3,2] + α
   - bit = 0: 确保 coeff[3,2] > coeff[2,3] + α
8. 逆 DCT + 逆 DWT
9. 重建 YCbCr → RGB
10. 写回 PDF
```

#### 提取流程
```
1. 读取图像（PDF 或图像文件）
2. (可选) 透视校正
3. RGB → YCbCr → 提取 Y 通道
4. DWT 获取 LH 子带
5. 划分 8×8 块 → DCT
6. 读取系数差值:
   - coeff[2,3] > coeff[3,2] → bit = 1
   - 否则 → bit = 0
7. 重建位流
8. 查找前导码 (Preamble)
9. 读取元数据（长度、分段信息）
10. RS 纠错解码
11. 返回水印文本
```

### 2. 纠错编码 (error_correction.py)

**核心类**: `ErrorCorrection`

**使用的编码**: Reed-Solomon (RS) over GF(2^8)

**参数**:
- `ecc_symbols`: 纠错符号个数（默认 32）
- 可纠正最多 `ecc_symbols / 2` 个字节错误

**位流格式**:
```
[Preamble: 4字节][ECC参数: 1字节][分块大小: 2字节]
[分段数: 2字节][最后分段长度: 2字节][编码数据...]
```

### 3. PDF 处理器 (pdf/processor.py)

**核心类**: `PDFProcessor`

**依赖**: PyMuPDF (fitz)

**功能**:
- 将 PDF 页面渲染为 PIL Image (指定 DPI)
- 将图像列表写入 PDF (JPEG 压缩)

**性能优化**:
- 支持分页处理（不一次性加载所有页面）
- JPEG 质量可配置
- 支持 PDF 压缩和垃圾回收

### 4. 图像处理器 (image/processor.py)

**核心类**: `ImageProcessor`

**功能**:
1. **图像加载**: 支持多种格式
2. **透视校正**:
   - 边缘检测 (Canny)
   - 轮廓查找
   - 四点透视变换

**透视校正算法**:
```
1. 灰度化 + 高斯模糊
2. Canny 边缘检测
3. 查找轮廓，按面积排序
4. 逼近四边形
5. 计算透视变换矩阵
6. 应用变换
```

## 参数调优

### 水印强度 (embed_strength)

- **物理含义**: DCT 系数的调制幅度 α
- **影响**:
  - ↑ 强度 → ↑ 鲁棒性, ↓ 不可见性
  - ↓ 强度 → ↑ 不可见性, ↓ 鲁棒性

**推荐值**:
```python
# 视觉优先: 8.0 - 10.0
# 平衡模式: 12.0 - 14.0
# 鲁棒优先: 16.0 - 20.0
```

### 块大小 (block_size)

- **当前值**: 8 (固定)
- **原因**: 8×8 是 JPEG 标准，对 JPEG 压缩有更好的鲁棒性

### 小波类型 (wavelet)

- **当前值**: "haar"
- **原因**: Haar 小波计算最快，且对空间局部性好
- **可选值**: "db1", "db2", "sym2" 等（需测试鲁棒性）

## 安全性分析

### 攻击场景与防御

| 攻击类型         | 防御方法                          | 鲁棒性 |
|------------------|-----------------------------------|--------|
| 截图             | 频域嵌入 + 冗余重复               | ✅ 强  |
| JPEG 压缩        | 基于 DCT 的嵌入                   | ✅ 强  |
| 缩放             | DWT 多尺度特性                    | ✅ 强  |
| 轻度旋转 (±15°)  | DWT + 边缘检测校正                | ✅ 中  |
| 拍照             | 透视校正 + 频域鲁棒性             | ✅ 中  |
| 高斯模糊         | 频域嵌入                          | ⚠️ 中  |
| 噪声添加         | RS 纠错                           | ⚠️ 中  |
| 打印再扫描       | 高强度 + 高 ECC                   | ⚠️ 弱  |
| 裁剪             | 前导码搜索 + 多页冗余             | ✅ 中  |
| 重新排版/OCR     | 无法防御（水印在像素层）          | ❌ 无  |

### 不可见性保证

1. **仅修改 Y 通道**: 人眼对亮度变化不敏感
2. **频域中频嵌入**: 避免低频 (视觉显著) 和高频 (易损失)
3. **自适应强度**: 可根据图像内容调整（当前版本固定）

## 性能分析

### 时间复杂度

对于单页图像 (H×W):

- **DWT**: O(H×W)
- **DCT (per block)**: O(64) = O(1)
- **总 DCT**: O((H/8) × (W/8)) = O(H×W)
- **RS 编码**: O(n²) where n = 数据长度
- **总体**: O(H×W)

### 空间复杂度

- **图像存储**: O(H×W×3) (RGB)
- **DWT 系数**: O(H×W)
- **峰值内存**: ~5× 原图大小

### 实测性能 (Intel i7, 单核)

| 图像尺寸        | 嵌入时间 | 提取时间 | 内存峰值 |
|-----------------|----------|----------|----------|
| 1024×768        | ~0.3s    | ~0.2s    | ~30 MB   |
| 1240×1754 (A4)  | ~0.8s    | ~0.5s    | ~60 MB   |
| 1754×2480       | ~1.5s    | ~1.0s    | ~100 MB  |

## 可扩展性

### 未来增强方向

1. **多通道嵌入**: 在 Cb, Cr 通道也嵌入水印
2. **自适应强度**: 根据图像局部纹理复杂度调整强度
3. **GPU 加速**: 使用 CUDA 加速 DWT/DCT
4. **多进程**: 批量处理时使用多进程
5. **视频支持**: 扩展至视频文件

### 接口扩展

当前系统支持：
- Python API
- 命令行 CLI

可扩展至：
- REST API (Flask/FastAPI)
- Web UI
- Docker 容器化服务

## 测试策略

### 单元测试

- `test_watermark.py`: 基础嵌入提取
- `test_error_correction.py`: RS 编解码
- `test_performance.py`: 性能基准测试

### 鲁棒性测试

建议测试：
```python
# 压缩测试
image.save("compressed.jpg", quality=50)

# 缩放测试
image = image.resize((w//2, h//2))

# 噪声测试
noisy = image + np.random.normal(0, 10, image.shape)

# 旋转测试
rotated = image.rotate(5)
```

## 依赖管理

### 核心依赖

- `numpy`: 数值计算
- `opencv-python`: DCT 和图像处理
- `PyWavelets`: DWT
- `PyMuPDF`: PDF 渲染和生成
- `Pillow`: 图像 I/O
- `reedsolo`: Reed-Solomon 纠错

### 版本要求

- Python >= 3.8
- NumPy >= 1.21
- OpenCV >= 4.5

## 参考文献

1. Cox, I. J., et al. (2007). Digital Watermarking and Steganography.
2. Bhatnagar, G., & Raman, B. (2009). "A new robust reference watermarking scheme based on DWT-SVD."
3. Reed, I. S., & Solomon, G. (1960). "Polynomial Codes Over Certain Finite Fields."
