# 使用指南

本指南详细介绍如何在各种场景下使用 PDF 全盲水印系统。

## 目录

1. [基础使用](#基础使用)
2. [高级配置](#高级配置)
3. [常见场景](#常见场景)
4. [文本隐写术](#文本隐写术)
5. [基准测试与报告](#基准测试与报告)
6. [合规性与审计](#合规性与审计)
7. [故障排查](#故障排查)
8. [最佳实践](#最佳实践)

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

## 文本隐写术

### 什么是文本隐写术

文本隐写术（Text Steganography）是将结构化文本数据（如用户 ID、时间戳、元数据）隐藏在文档中的技术。与简单水印不同，隐写术支持更复杂的数据结构。

### 结构化水印设计

#### 基本格式

```python
# 推荐使用管道符分隔的键值对格式
watermark = "KEY1:value1|KEY2:value2|KEY3:value3"

# 示例
watermark = "USER:U12345|TIME:20241018-143000|DEPT:FINANCE"
```

#### 实用示例

**示例 1：用户追踪水印**

```python
from datetime import datetime

def create_user_watermark(user_id: str) -> str:
    """创建带用户 ID 和时间戳的水印"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"USER:{user_id}|TIME:{timestamp}"

# 使用
watermark = create_user_watermark("U12345")
watermarker.embed("contract.pdf", "contract_U12345.pdf", watermark)
```

**示例 2：文档追踪水印**

```python
def create_document_watermark(
    document_id: str,
    user_id: str,
    department: str
) -> str:
    """创建完整文档追踪水印"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    return f"DOC:{document_id}|USER:{user_id}|DEPT:{department}|TIME:{timestamp}"

# 使用
watermark = create_document_watermark(
    document_id="DOC-2024-0123",
    user_id="U78901",
    department="LEGAL"
)
```

**示例 3：访问控制水印**

```python
def create_access_watermark(
    user_id: str,
    access_level: str,
    expiry_date: str
) -> str:
    """创建访问控制水印"""
    return f"USER:{user_id}|LEVEL:{access_level}|EXPIRE:{expiry_date}"

# 使用
watermark = create_access_watermark(
    user_id="U45678",
    access_level="CONFIDENTIAL",
    expiry_date="20241231"
)
```

### 提取与解析水印

#### 基本解析

```python
def parse_watermark(watermark: str) -> dict:
    """解析结构化水印"""
    components = {}
    parts = watermark.split("|")
    
    for part in parts:
        if ":" in part:
            key, value = part.split(":", 1)
            components[key] = value
    
    return components

# 使用
extracted = watermarker.extract("leaked_document.jpg", source_type="image")
components = parse_watermark(extracted)

print(f"文档 ID: {components.get('DOC')}")
print(f"用户 ID: {components.get('USER')}")
print(f"部门: {components.get('DEPT')}")
print(f"时间: {components.get('TIME')}")
```

#### 多页文档处理

从多页 PDF 提取时，系统会自动使用多数投票机制：

```python
# 系统自动处理多页 PDF
extracted = watermarker.extract("multi_page.pdf", source_type="pdf")

# 内部流程：
# 1. 从每一页提取水印
# 2. 收集所有提取结果
# 3. 使用多数投票选择最常见的结果
# 4. 返回最可靠的水印

# 你只需处理最终结果
components = parse_watermark(extracted)
```

### 审计追踪工作流

完整的审计追踪示例：

```python
import json
from datetime import datetime
from pathlib import Path

class WatermarkAuditTrail:
    """水印审计追踪系统"""
    
    def __init__(self, log_file: str = "watermark_audit.json"):
        self.log_file = Path(log_file)
        self.logs = self._load_logs()
    
    def _load_logs(self):
        if self.log_file.exists():
            with open(self.log_file) as f:
                return json.load(f)
        return []
    
    def _save_logs(self):
        with open(self.log_file, "w") as f:
            json.dump(self.logs, f, indent=2)
    
    def log_embed(self, document_id: str, user_id: str, watermark: str):
        """记录水印嵌入事件"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "EMBED",
            "document_id": document_id,
            "user_id": user_id,
            "watermark": watermark
        }
        self.logs.append(entry)
        self._save_logs()
    
    def log_extraction(self, source: str, watermark: str, success: bool):
        """记录水印提取事件"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "EXTRACT",
            "source": source,
            "watermark": watermark,
            "success": success
        }
        self.logs.append(entry)
        self._save_logs()
    
    def find_by_user(self, user_id: str):
        """查找用户相关的所有事件"""
        return [log for log in self.logs if log.get("user_id") == user_id]

# 使用示例
audit = WatermarkAuditTrail()

# 嵌入时记录
watermark = create_user_watermark("U12345")
watermarker.embed("doc.pdf", "doc_watermarked.pdf", watermark)
audit.log_embed("DOC-001", "U12345", watermark)

# 提取时记录
try:
    extracted = watermarker.extract("leaked.jpg", source_type="image")
    audit.log_extraction("leaked.jpg", extracted, True)
    
    # 分析泄露源
    components = parse_watermark(extracted)
    responsible_user = components.get("USER")
    print(f"文档泄露追溯到用户: {responsible_user}")
    
    # 查找该用户的所有活动
    user_history = audit.find_by_user(responsible_user)
    print(f"该用户历史记录: {len(user_history)} 条")
    
except Exception as e:
    audit.log_extraction("leaked.jpg", "", False)
    print(f"提取失败: {e}")
```

## 基准测试与报告

### 运行基准测试

#### 命令行方式

```bash
# 运行完整测试套件（性能 + 鲁棒性）
python -m pdf_blind_watermark benchmark --suite full --format html

# 仅运行性能测试
python -m pdf_blind_watermark benchmark --suite performance --format markdown

# 仅运行鲁棒性测试
python -m pdf_blind_watermark benchmark --suite robustness --format json

# 指定输出目录
python -m pdf_blind_watermark benchmark --suite full --format html -o ./my_results
```

#### Python API 方式

```python
from pdf_blind_watermark.benchmark import BenchmarkSuite

# 创建测试套件
suite = BenchmarkSuite(output_dir="./benchmark_results")

# 运行性能基准测试
suite.run_standard_suite()

# 运行鲁棒性测试
suite.run_robustness_suite()

# 生成不同格式的报告
html_report = suite.generate_report("html")
json_report = suite.generate_report("json")
md_report = suite.generate_report("markdown")

print(f"HTML 报告: {html_report}")
print(f"JSON 报告: {json_report}")
print(f"Markdown 报告: {md_report}")
```

### 自定义基准测试

```python
from pdf_blind_watermark.benchmark import BenchmarkSuite
from pdf_blind_watermark.core.watermark import WatermarkConfig

suite = BenchmarkSuite()

# 测试自定义配置
custom_config = WatermarkConfig(
    embed_strength=14.0,
    ecc_symbols=40,
    dpi=160,
    quality=88
)

result = suite.run_performance_benchmark(
    test_name="Custom Configuration",
    config=custom_config,
    image_size=(1240, 1754),
    watermark_text="CUSTOM-TEST"
)

print(f"嵌入时间: {result.embed_time:.3f}s")
print(f"提取时间: {result.extract_time:.3f}s")
print(f"成功: {result.match_success}")
```

### 理解基准测试报告

#### 性能指标

**嵌入时间 (Embed Time)**
- **含义**：将水印嵌入到图像所需的时间
- **典型值**：0.3s - 2.0s/页
- **影响因素**：DPI、图像尺寸、配置参数
- **建议**：生产环境应 <2s/页

**提取时间 (Extract Time)**
- **含义**：从图像提取水印所需的时间
- **典型值**：嵌入时间的 50-70%
- **影响因素**：图像质量、噪声水平
- **建议**：应急响应需要 <1s/页

**成功率 (Success Rate)**
- **含义**：成功提取正确水印的百分比
- **目标值**：>95% 用于生产环境
- **低于 90%**：需要调整配置

#### 鲁棒性指标

**JPEG 压缩抗性**

| 质量等级 | 期望结果 | 配置建议 |
|---------|---------|---------|
| Q90+    | ✓ 应该通过 | 所有配置 |
| Q70-90  | ✓ 应该通过 | embed_strength ≥12 |
| Q50-70  | ⚠ 可能失败 | embed_strength ≥14, ecc_symbols ≥32 |
| Q<50    | ✗ 通常失败 | embed_strength ≥16, ecc_symbols ≥48 |

**缩放抗性**

| 缩放比例 | 期望结果 | 说明 |
|---------|---------|------|
| 0.75+   | ✓ 优秀 | 正常截图场景 |
| 0.5-0.75 | ✓ 良好 | 缩略图场景 |
| 0.25-0.5 | ⚠ 中等 | 需要高强度配置 |
| <0.25   | ✗ 差 | 信息损失过多 |

**噪声抗性（高斯噪声）**

| Sigma 值 | 期望结果 | 场景 |
|---------|---------|------|
| 0-10    | ✓ 优秀 | 清晰照片、截图 |
| 10-15   | ⚠ 中等 | 低光照照片 |
| 15+     | ✗ 差 | 严重噪声环境 |

### 报告格式说明

#### HTML 报告

- **优点**：可视化好，易于分享
- **包含**：表格、图表、颜色编码
- **适用于**：管理层汇报、文档归档

#### JSON 报告

- **优点**：结构化数据，易于程序处理
- **包含**：完整测试数据、元数据
- **适用于**：自动化分析、CI/CD 集成

#### Markdown 报告

- **优点**：纯文本，易于版本控制
- **包含**：表格、统计数据
- **适用于**：技术文档、GitHub 等

## 合规性与审计

### 合规性报告集成

基准测试报告可用于以下合规场景：

#### 1. ISO 27001 信息安全管理

**证明点**：
- A.8.2.3 处理资产：证明文档有防泄露措施
- A.13.2.3 电子信息传输：证明传输文档可追溯

**所需指标**：
- 水印成功率 >95%
- 提取成功案例证明
- 审计日志完整性

#### 2. GDPR 数据保护

**证明点**：
- 第 32 条：技术和组织措施
- 第 33 条：数据泄露通知能力

**所需指标**：
- 用户 ID 嵌入和提取成功率
- 泄露追溯时间 <1 小时
- 审计追踪记录

#### 3. SOC 2 安全审计

**证明点**：
- CC6.1：逻辑访问控制
- CC7.2：系统监控

**所需指标**：
- 系统可用性 >99%
- 日志保留 >1 年
- 定期基准测试（至少季度一次）

### 审计报告生成

```python
from datetime import datetime
import json

class ComplianceReporter:
    """生成合规性报告"""
    
    def __init__(self, benchmark_results: dict):
        self.results = benchmark_results
    
    def generate_compliance_report(self) -> dict:
        """生成合规性报告"""
        summary = self.results.get("summary", {})
        
        report = {
            "report_date": datetime.now().isoformat(),
            "compliance_status": self._assess_compliance(summary),
            "metrics": {
                "success_rate": summary.get("success_rate", 0),
                "avg_embed_time": summary.get("avg_embed_time", 0),
                "avg_extract_time": summary.get("avg_extract_time", 0),
                "total_tests": summary.get("total_tests", 0),
            },
            "recommendations": self._generate_recommendations(summary),
            "compliance_certifications": {
                "iso27001": self._check_iso27001(summary),
                "gdpr": self._check_gdpr(summary),
                "soc2": self._check_soc2(summary),
            }
        }
        
        return report
    
    def _assess_compliance(self, summary: dict) -> str:
        success_rate = summary.get("success_rate", 0)
        if success_rate >= 0.95:
            return "COMPLIANT"
        elif success_rate >= 0.90:
            return "WARNING"
        else:
            return "NON_COMPLIANT"
    
    def _check_iso27001(self, summary: dict) -> bool:
        """检查 ISO 27001 合规性"""
        return summary.get("success_rate", 0) >= 0.95
    
    def _check_gdpr(self, summary: dict) -> bool:
        """检查 GDPR 合规性"""
        return (summary.get("success_rate", 0) >= 0.95 and
                summary.get("avg_extract_time", 999) < 1.0)
    
    def _check_soc2(self, summary: dict) -> bool:
        """检查 SOC 2 合规性"""
        return summary.get("success_rate", 0) >= 0.95
    
    def _generate_recommendations(self, summary: dict) -> list:
        """生成改进建议"""
        recommendations = []
        
        if summary.get("success_rate", 0) < 0.95:
            recommendations.append("增加 embed_strength 以提高成功率")
        
        if summary.get("avg_embed_time", 0) > 2.0:
            recommendations.append("降低 DPI 以提高处理速度")
        
        return recommendations

# 使用示例
with open("benchmark_results/benchmark_report_*.json") as f:
    benchmark_data = json.load(f)

reporter = ComplianceReporter(benchmark_data)
compliance_report = reporter.generate_compliance_report()

print(f"合规状态: {compliance_report['compliance_status']}")
print(f"ISO 27001: {'✓' if compliance_report['compliance_certifications']['iso27001'] else '✗'}")
print(f"GDPR: {'✓' if compliance_report['compliance_certifications']['gdpr'] else '✗'}")
print(f"SOC 2: {'✓' if compliance_report['compliance_certifications']['soc2'] else '✗'}")
```

### 定期审计建议

**审计频率**：
- 初始部署：每周测试
- 稳定运行：每月测试
- 合规要求：每季度完整审计

**审计内容**：
1. 运行完整基准测试套件
2. 生成并归档报告
3. 检查成功率趋势
4. 审查审计日志
5. 更新合规文档

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
