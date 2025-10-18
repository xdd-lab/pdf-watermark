# 基准测试与合规性指南

本指南详细说明如何使用基准测试套件、解读报告指标，以及将结果整合到合规性审查中。

## 目录

1. [基准测试概述](#基准测试概述)
2. [运行基准测试](#运行基准测试)
3. [理解测试指标](#理解测试指标)
4. [解读鲁棒性结果](#解读鲁棒性结果)
5. [报告格式与用途](#报告格式与用途)
6. [合规性集成](#合规性集成)
7. [最佳实践](#最佳实践)

## 基准测试概述

### 什么是基准测试

基准测试套件是一个全面的测试框架，用于评估 PDF 水印系统的性能和鲁棒性。它提供：

- **性能指标**：嵌入和提取操作的速度
- **鲁棒性评估**：抵御各种攻击的能力
- **自动化报告**：生成多种格式的详细报告
- **合规性数据**：支持安全审计和合规检查

### 测试套件组成

1. **性能基准测试**
   - 不同图像尺寸的测试
   - 不同配置参数的对比
   - 嵌入和提取时间测量

2. **鲁棒性测试**
   - JPEG 压缩抗性测试
   - 图像缩放抗性测试
   - 高斯噪声抗性测试
   - 其他攻击场景测试

## 运行基准测试

### 命令行方式

#### 完整测试套件

```bash
# 运行所有测试并生成 HTML 报告
python -m pdf_blind_watermark benchmark --suite full --format html

# 输出结果将保存在 ./benchmark_results/ 目录
```

#### 仅性能测试

```bash
# 只运行性能测试
python -m pdf_blind_watermark benchmark --suite performance --format markdown

# 适用于快速性能评估
```

#### 仅鲁棒性测试

```bash
# 只运行鲁棒性测试
python -m pdf_blind_watermark benchmark --suite robustness --format json

# 适用于验证配置的抗攻击能力
```

#### 自定义输出目录

```bash
# 指定自定义输出目录
python -m pdf_blind_watermark benchmark \
    --suite full \
    --format html \
    -o ./my_reports/$(date +%Y%m%d)
```

### Python API 方式

#### 基础使用

```python
from pdf_blind_watermark.benchmark import BenchmarkSuite

# 创建测试套件实例
suite = BenchmarkSuite(output_dir="./benchmark_results")

# 运行标准性能测试
suite.run_standard_suite()

# 运行鲁棒性测试
suite.run_robustness_suite()

# 生成报告
html_report = suite.generate_report("html")
print(f"报告已生成: {html_report}")
```

#### 自定义配置测试

```python
from pdf_blind_watermark.benchmark import BenchmarkSuite
from pdf_blind_watermark.core.watermark import WatermarkConfig

suite = BenchmarkSuite()

# 测试特定配置
config = WatermarkConfig(
    embed_strength=14.0,
    ecc_symbols=40,
    dpi=160,
    quality=88
)

# 运行单个性能测试
result = suite.run_performance_benchmark(
    test_name="Custom High Security",
    config=config,
    image_size=(1240, 1754),
    watermark_text="SECURITY-TEST"
)

print(f"嵌入时间: {result.embed_time:.3f}s")
print(f"提取时间: {result.extract_time:.3f}s")
print(f"成功: {'✓' if result.match_success else '✗'}")
```

#### 批量测试多个配置

```python
from pdf_blind_watermark.benchmark import BenchmarkSuite
from pdf_blind_watermark.core.watermark import WatermarkConfig

suite = BenchmarkSuite()

# 定义多个配置
configurations = [
    ("Low Security", WatermarkConfig(embed_strength=10.0, ecc_symbols=16)),
    ("Medium Security", WatermarkConfig(embed_strength=12.0, ecc_symbols=32)),
    ("High Security", WatermarkConfig(embed_strength=16.0, ecc_symbols=48)),
]

# 测试所有配置
for name, config in configurations:
    result = suite.run_performance_benchmark(
        test_name=name,
        config=config,
        image_size=(1240, 1754),
        watermark_text="COMPARE-TEST"
    )
    print(f"{name}: {result.embed_time:.3f}s / {result.extract_time:.3f}s")

# 生成综合报告
report = suite.generate_report("html")
```

## 理解测试指标

### 性能指标详解

#### 1. 嵌入时间 (Embed Time)

**定义**：将水印嵌入到图像所需的时间（秒）

**影响因素**：
- 图像分辨率（DPI）
- 图像尺寸（宽×高）
- 水印强度
- 纠错符号数量

**典型值**：
| 配置 | A4 @ 150dpi | A4 @ 200dpi |
|------|------------|------------|
| 快速 | 0.5-0.8s   | 1.0-1.5s   |
| 平衡 | 0.8-1.2s   | 1.5-2.0s   |
| 鲁棒 | 1.2-1.8s   | 2.0-3.0s   |

**解读建议**：
- ✅ <1s/页：优秀，适合实时处理
- ⚠️ 1-2s/页：可接受，适合批处理
- ❌ >2s/页：较慢，考虑降低 DPI 或优化配置

#### 2. 提取时间 (Extract Time)

**定义**：从图像提取水印所需的时间（秒）

**特点**：
- 通常为嵌入时间的 50-70%
- 不受水印强度影响
- 受图像质量和噪声影响

**典型值**：
- 清晰图像：0.3-0.8s
- 压缩图像：0.5-1.0s
- 噪声图像：0.8-1.5s

**解读建议**：
- ✅ <0.5s：优秀，适合应急响应
- ⚠️ 0.5-1.0s：可接受
- ❌ >1.0s：较慢，检查图像质量或配置

#### 3. 成功率 (Success Rate)

**定义**：成功提取正确水印的测试占比

**计算方式**：
```
成功率 = (成功提取次数 / 总测试次数) × 100%
```

**目标值**：
- 生产环境：>95%
- 测试环境：>90%
- 最低可接受：>85%

**失败原因分析**：
- 水印强度不足
- 纠错能力不足
- DPI 设置过低
- 攻击强度过大

## 解读鲁棒性结果

### JPEG 压缩抗性

#### 测试方法

测试在不同 JPEG 质量等级下水印的生存能力：

```python
suite.run_robustness_test(
    config=config,
    watermark_text="TEST",
    attack_type="JPEG Compression",
    attack_func=suite._attack_jpeg_compress,
    attack_params={"quality": 70}
)
```

#### 结果解读

| 质量等级 | 期望结果 | 失败原因 | 改进措施 |
|---------|---------|---------|---------|
| Q90-100 | ✓ 必须通过 | 基本配置错误 | 检查基础配置 |
| Q70-90  | ✓ 应该通过 | 强度不足 | embed_strength += 2 |
| Q50-70  | ⚠️ 可能失败 | 强度或 ECC 不足 | embed_strength += 4, ecc_symbols += 16 |
| Q30-50  | ⚠️ 通常失败 | 极端压缩 | embed_strength ≥ 16, ecc_symbols ≥ 48 |
| Q<30    | ✗ 预期失败 | 信息损失过大 | 不可恢复 |

#### 实际应用场景

- **Q90+**：原始文档、轻度分享
- **Q70-90**：常见截图、邮件附件
- **Q50-70**：网络传输、即时通讯
- **Q<50**：严重压缩、恶意破坏

### 缩放抗性

#### 测试方法

测试图像经过缩放（downscale + upscale）后水印的保持能力：

```python
suite.run_robustness_test(
    config=config,
    watermark_text="TEST",
    attack_type="Resize",
    attack_func=suite._attack_resize,
    attack_params={"scale": 0.5}
)
```

#### 结果解读

| 缩放比例 | 期望结果 | 应用场景 | 配置建议 |
|---------|---------|---------|---------|
| 0.9-1.0 | ✓ 必须通过 | 轻微缩放 | 默认配置 |
| 0.75-0.9 | ✓ 应该通过 | 截图缩放 | embed_strength ≥ 12 |
| 0.5-0.75 | ⚠️ 可能失败 | 缩略图 | embed_strength ≥ 14, dpi ≥ 180 |
| 0.25-0.5 | ⚠️ 通常失败 | 小尺寸预览 | embed_strength ≥ 16 |
| <0.25   | ✗ 预期失败 | 极小图标 | 不可恢复 |

#### DPI 影响

更高的 DPI 提供更多嵌入容量，提升缩放抗性：

- DPI 120：适合 scale > 0.75
- DPI 150：适合 scale > 0.5
- DPI 180：适合 scale > 0.4
- DPI 220：适合 scale > 0.3

### 噪声抗性

#### 测试方法

测试添加高斯噪声后水印的鲁棒性：

```python
suite.run_robustness_test(
    config=config,
    watermark_text="TEST",
    attack_type="Gaussian Noise",
    attack_func=suite._attack_gaussian_noise,
    attack_params={"sigma": 10}
)
```

#### 结果解读

| Sigma 值 | 期望结果 | 应用场景 | 配置建议 |
|---------|---------|---------|---------|
| 0-5     | ✓ 必须通过 | 清晰图像 | 默认配置 |
| 5-10    | ✓ 应该通过 | 一般照片 | embed_strength ≥ 12 |
| 10-15   | ⚠️ 可能失败 | 低光照照片 | embed_strength ≥ 14, ecc_symbols ≥ 40 |
| 15-20   | ⚠️ 通常失败 | 严重噪声 | embed_strength ≥ 16, ecc_symbols ≥ 48 |
| >20     | ✗ 预期失败 | 极端噪声 | 不可恢复 |

## 报告格式与用途

### HTML 报告

**特点**：
- 可视化效果好
- 包含彩色编码状态
- 易于在浏览器中查看
- 适合非技术人员阅读

**内容结构**：
```
1. 报告头部
   - 生成时间
   - 系统版本
   
2. 摘要统计
   - 总测试数
   - 成功率
   - 平均时间
   
3. 性能结果表格
   - 测试名称
   - 配置参数
   - 时间指标
   - 成功状态
   
4. 鲁棒性结果表格
   - 攻击类型
   - 攻击参数
   - 测试结果
```

**使用场景**：
- 管理层汇报
- 技术文档归档
- 合规审计证据
- 客户演示

### JSON 报告

**特点**：
- 结构化数据
- 易于程序解析
- 完整的元数据
- 适合自动化处理

**数据结构**：
```json
{
  "timestamp": "20241018_143000",
  "performance_results": [
    {
      "test_name": "...",
      "config": {...},
      "embed_time": 0.85,
      "extract_time": 0.52,
      "match_success": true
    }
  ],
  "robustness_results": [
    {
      "attack_type": "JPEG Compression",
      "attack_params": {"quality": 70},
      "success": true
    }
  ],
  "summary": {
    "total_tests": 30,
    "success_rate": 0.96,
    "avg_embed_time": 0.89,
    "avg_extract_time": 0.54
  }
}
```

**使用场景**：
- CI/CD 集成
- 自动化分析
- 数据库存储
- API 集成

### Markdown 报告

**特点**：
- 纯文本格式
- 易于版本控制
- 可读性好
- 适合 Git 仓库

**使用场景**：
- GitHub/GitLab 文档
- 技术团队内部分享
- 版本对比
- 文档生成

## 合规性集成

### ISO 27001 信息安全管理

#### 相关控制项

**A.8.2.3 处理资产**

证明要求：
- 敏感信息有适当的处理程序
- 防止未授权访问和泄露

基准测试证据：
```python
# 生成合规性报告
suite = BenchmarkSuite()
suite.run_standard_suite()
suite.run_robustness_suite()

report_data = json.loads(open("benchmark_report.json").read())

# 验证成功率 > 95%
assert report_data["summary"]["success_rate"] > 0.95

# 验证能追溯泄露源
# (通过用户 ID 嵌入示例证明)
```

**A.13.2.3 电子信息传输**

证明要求：
- 电子传输信息有保护措施
- 可追溯信息来源

基准测试证据：
- 水印嵌入和提取成功率
- 多页文档一致性测试
- 审计日志完整性

#### 审计证据清单

准备以下文件用于 ISO 27001 审计：

1. **基准测试报告** (HTML 格式)
   - 最近 3 个月的测试结果
   - 成功率趋势图
   - 配置参数说明

2. **配置文档**
   - 生产环境配置
   - 配置选择理由
   - 风险评估

3. **审计日志样本**
   - 嵌入记录
   - 提取记录
   - 泄露追溯案例

### GDPR 数据保护

#### 第 32 条：技术和组织措施

要求：
- 实施适当的技术措施保护个人数据
- 考虑技术水平和实施成本

基准测试证明：
```python
# GDPR 合规检查
def check_gdpr_compliance(report_data):
    summary = report_data["summary"]
    
    # 技术措施有效性：成功率 > 95%
    technical_measure = summary["success_rate"] > 0.95
    
    # 应急响应能力：提取时间 < 1s
    incident_response = summary["avg_extract_time"] < 1.0
    
    # 追溯能力：用户 ID 嵌入测试通过
    traceability = True  # 通过用户 ID 示例验证
    
    return all([technical_measure, incident_response, traceability])

# 生成 GDPR 合规报告
compliance_status = check_gdpr_compliance(report_data)
print(f"GDPR 合规: {'✓' if compliance_status else '✗'}")
```

#### 第 33 条：数据泄露通知

要求：
- 72 小时内通知数据泄露
- 能够快速识别泄露范围

基准测试证明：
- 提取时间 < 1s（快速识别）
- 用户 ID 解析功能（确定影响范围）
- 审计追踪完整性（重建事件时间线）

### SOC 2 安全审计

#### CC6.1 逻辑访问控制

信任服务标准：
- 系统对数据和资产的逻辑访问有限制
- 访问权限得到适当管理

基准测试证据：
```python
# SOC 2 合规报告生成
class SOC2Reporter:
    def generate_cc6_1_report(self, benchmark_data):
        return {
            "control_objective": "CC6.1 - Logical Access",
            "implementation": {
                "watermark_system": "Embedded user ID tracking",
                "success_rate": benchmark_data["summary"]["success_rate"],
                "audit_trail": "Complete embedding and extraction logs"
            },
            "testing_results": {
                "test_date": datetime.now().isoformat(),
                "tests_performed": benchmark_data["summary"]["total_tests"],
                "pass_rate": f"{benchmark_data['summary']['success_rate']*100:.1f}%"
            },
            "evidence": [
                "benchmark_report.html",
                "audit_logs.json",
                "user_tracking_examples.py"
            ]
        }
```

#### CC7.2 系统监控

信任服务标准：
- 系统有监控措施
- 异常活动能被检测

基准测试证明：
- 定期运行基准测试（月度/季度）
- 性能指标趋势监控
- 成功率下降告警

### 合规性报告模板

```python
from datetime import datetime
import json

class ComplianceReport:
    """生成合规性报告"""
    
    def __init__(self, benchmark_results_file: str):
        with open(benchmark_results_file) as f:
            self.results = json.load(f)
    
    def generate_full_report(self) -> dict:
        """生成完整合规性报告"""
        summary = self.results.get("summary", {})
        
        return {
            "metadata": {
                "report_date": datetime.now().isoformat(),
                "report_type": "Compliance Assessment",
                "system": "PDF Blind Watermark",
                "version": "1.0.0"
            },
            "executive_summary": {
                "overall_status": self._assess_status(summary),
                "key_metrics": {
                    "success_rate": f"{summary.get('success_rate', 0)*100:.1f}%",
                    "total_tests": summary.get("total_tests", 0),
                    "avg_response_time": f"{summary.get('avg_extract_time', 0):.3f}s"
                }
            },
            "compliance_frameworks": {
                "iso27001": {
                    "status": self._check_iso27001(summary),
                    "controls_addressed": ["A.8.2.3", "A.13.2.3"],
                    "evidence": ["benchmark_report.html", "audit_logs.json"]
                },
                "gdpr": {
                    "status": self._check_gdpr(summary),
                    "articles_addressed": ["Article 32", "Article 33"],
                    "evidence": ["user_tracking_demo.py", "extraction_speed_test.json"]
                },
                "soc2": {
                    "status": self._check_soc2(summary),
                    "criteria_addressed": ["CC6.1", "CC7.2"],
                    "evidence": ["monthly_benchmark_reports/", "monitoring_config.json"]
                }
            },
            "recommendations": self._generate_recommendations(summary),
            "next_review_date": self._calculate_next_review()
        }
    
    def _assess_status(self, summary: dict) -> str:
        rate = summary.get("success_rate", 0)
        if rate >= 0.95:
            return "COMPLIANT"
        elif rate >= 0.90:
            return "NEEDS_ATTENTION"
        else:
            return "NON_COMPLIANT"
    
    def _check_iso27001(self, summary: dict) -> bool:
        return summary.get("success_rate", 0) >= 0.95
    
    def _check_gdpr(self, summary: dict) -> bool:
        return (summary.get("success_rate", 0) >= 0.95 and
                summary.get("avg_extract_time", 999) < 1.0)
    
    def _check_soc2(self, summary: dict) -> bool:
        return summary.get("success_rate", 0) >= 0.95
    
    def _generate_recommendations(self, summary: dict) -> list:
        recommendations = []
        
        if summary.get("success_rate", 0) < 0.95:
            recommendations.append({
                "priority": "HIGH",
                "action": "Increase embed_strength to improve success rate",
                "expected_impact": "Success rate increase to >95%"
            })
        
        if summary.get("avg_extract_time", 0) > 1.0:
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Optimize extraction process or increase hardware resources",
                "expected_impact": "Meet GDPR incident response requirements"
            })
        
        return recommendations
    
    def _calculate_next_review(self) -> str:
        from datetime import timedelta
        next_review = datetime.now() + timedelta(days=90)  # Quarterly
        return next_review.strftime("%Y-%m-%d")

# 使用示例
reporter = ComplianceReport("benchmark_results/benchmark_report_20241018.json")
compliance_report = reporter.generate_full_report()

# 保存报告
with open("compliance_report.json", "w") as f:
    json.dump(compliance_report, f, indent=2)

print(f"合规状态: {compliance_report['executive_summary']['overall_status']}")
for framework, details in compliance_report['compliance_frameworks'].items():
    status = "✓" if details['status'] else "✗"
    print(f"{framework.upper()}: {status}")
```

## 最佳实践

### 1. 定期测试计划

**初始部署阶段**（前 3 个月）：
```bash
# 每周运行完整测试
0 2 * * 0 cd /opt/watermark && python -m pdf_blind_watermark benchmark --suite full --format html -o ./reports/$(date +\%Y\%m\%d)
```

**稳定运行阶段**：
```bash
# 每月运行完整测试
0 2 1 * * cd /opt/watermark && python -m pdf_blind_watermark benchmark --suite full --format html -o ./reports/$(date +\%Y\%m\%d)
```

**合规审计前**：
```bash
# 审计前 2 周运行完整测试
python -m pdf_blind_watermark benchmark --suite full --format html
python -m pdf_blind_watermark benchmark --suite full --format json
python -m pdf_blind_watermark benchmark --suite full --format markdown
```

### 2. 结果归档

建议的目录结构：
```
benchmark_results/
├── 2024/
│   ├── Q1/
│   │   ├── 202401/
│   │   │   ├── benchmark_report_20240115.html
│   │   │   ├── benchmark_report_20240115.json
│   │   │   └── compliance_assessment_Q1.pdf
│   │   ├── 202402/
│   │   └── 202403/
│   ├── Q2/
│   ├── Q3/
│   └── Q4/
└── compliance_reports/
    ├── iso27001_2024_annual.pdf
    ├── gdpr_quarterly_reviews.pdf
    └── soc2_type2_evidence.pdf
```

### 3. 告警阈值设置

```python
# monitoring.py - 监控告警脚本
import json
from datetime import datetime

def check_benchmark_results(report_file: str):
    """检查基准测试结果并发送告警"""
    with open(report_file) as f:
        data = json.load(f)
    
    summary = data.get("summary", {})
    alerts = []
    
    # 成功率低于 95%
    if summary.get("success_rate", 0) < 0.95:
        alerts.append({
            "severity": "HIGH",
            "message": f"Success rate below threshold: {summary['success_rate']*100:.1f}%",
            "action": "Review configuration and run diagnostic tests"
        })
    
    # 平均嵌入时间超过 2s
    if summary.get("avg_embed_time", 0) > 2.0:
        alerts.append({
            "severity": "MEDIUM",
            "message": f"Embed time above threshold: {summary['avg_embed_time']:.2f}s",
            "action": "Consider optimizing DPI or hardware upgrade"
        })
    
    # 平均提取时间超过 1s
    if summary.get("avg_extract_time", 0) > 1.0:
        alerts.append({
            "severity": "MEDIUM",
            "message": f"Extract time above threshold: {summary['avg_extract_time']:.2f}s",
            "action": "Check for performance degradation"
        })
    
    # 发送告警
    if alerts:
        send_alerts(alerts)
    
    return alerts

def send_alerts(alerts: list):
    """发送告警（email/Slack/PagerDuty等）"""
    for alert in alerts:
        print(f"[{alert['severity']}] {alert['message']}")
        print(f"  Action: {alert['action']}")
        # 集成实际的告警系统
        # send_email(alert)
        # send_slack_message(alert)
```

### 4. 持续改进循环

1. **运行基准测试** → 2. **分析结果** → 3. **识别问题** → 4. **调整配置** → 1. 重复

```python
# improvement_cycle.py
class ImprovementCycle:
    def __init__(self):
        self.history = []
    
    def run_cycle(self, current_config):
        # 1. 运行测试
        suite = BenchmarkSuite()
        result = suite.run_performance_benchmark(
            "Current Config",
            current_config,
            (1240, 1754),
            "TEST"
        )
        
        # 2. 记录结果
        self.history.append({
            "timestamp": datetime.now(),
            "config": current_config,
            "result": result
        })
        
        # 3. 分析并建议
        recommendations = self._analyze_and_recommend(result)
        
        # 4. 返回新配置
        return recommendations
    
    def _analyze_and_recommend(self, result):
        recommendations = {}
        
        if not result.match_success:
            recommendations["embed_strength"] = "increase by 2.0"
            recommendations["ecc_symbols"] = "increase by 16"
        
        if result.embed_time > 2.0:
            recommendations["dpi"] = "decrease by 30"
        
        return recommendations
```

### 5. 文档维护

定期更新以下文档：
- 基准测试报告归档
- 配置变更记录
- 性能趋势分析
- 合规性证据收集
- 审计准备清单
