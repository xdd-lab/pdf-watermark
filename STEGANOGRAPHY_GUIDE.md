# 文本隐写术（Text Steganography）指南

本指南详细介绍如何使用 PDF 全盲水印系统进行文本隐写，包括结构化数据嵌入、提取和审计追踪。

## 目录

1. [什么是文本隐写术](#什么是文本隐写术)
2. [与传统水印的区别](#与传统水印的区别)
3. [设计结构化水印](#设计结构化水印)
4. [嵌入用户 ID 和时间戳](#嵌入用户-id-和时间戳)
5. [提取和解析水印](#提取和解析水印)
6. [审计追踪实现](#审计追踪实现)
7. [实际应用场景](#实际应用场景)
8. [最佳实践](#最佳实践)

## 什么是文本隐写术

### 定义

文本隐写术（Text Steganography）是将结构化文本信息隐藏在载体（如 PDF 文档）中的技术。与简单的水印不同，隐写术强调：

1. **隐蔽性**：信息完全不可见
2. **结构化**：支持复杂的数据格式
3. **可解析**：可提取并解析为结构化数据
4. **鲁棒性**：抵御各种攻击和修改

### 系统实现

本系统基于频域（DWT + DCT）的全盲水印技术实现文本隐写：

```
输入文本 → 编码 → 纠错编码 → 频域嵌入 → 输出 PDF
                                        ↓
                                  完全不可见
```

提取过程：

```
PDF/图像 → 频域分析 → 纠错解码 → 解析 → 结构化数据
```

## 与传统水印的区别

| 特性 | 传统水印 | 文本隐写术 |
|-----|---------|----------|
| 可见性 | 可能可见 | 完全不可见 |
| 数据量 | 有限 | 较大（理论上 65KB） |
| 结构化 | 简单文本 | 复杂数据结构 |
| 解析能力 | 基础 | 高级（键值对等） |
| 应用场景 | 版权保护 | 追溯、审计、合规 |
| 鲁棒性 | 中等 | 高（带纠错） |

## 设计结构化水印

### 推荐格式

**基础格式：键值对 + 管道符分隔**

```python
watermark = "KEY1:value1|KEY2:value2|KEY3:value3"
```

**优点**：
- 易于解析
- 可扩展
- 人类可读
- 标准化

### 格式设计原则

#### 1. 简洁性

```python
# ✓ 好 - 简洁明了
"USER:U12345|TIME:20241018"

# ✗ 差 - 过于冗长
"USER_IDENTIFICATION_NUMBER:U12345|TIMESTAMP:2024-10-18T14:30:00Z"
```

**原因**：水印容量有限，简短格式可嵌入更多信息。

#### 2. 一致性

```python
# ✓ 好 - 统一格式
"DOC:D001|USER:U123|DEPT:FIN|TIME:20241018"

# ✗ 差 - 格式不一致
"DOC:D001|User=U123|Department:FIN|time-20241018"
```

**原因**：统一格式便于自动化解析和验证。

#### 3. 可扩展性

```python
class WatermarkFormat:
    """标准化水印格式"""
    
    @staticmethod
    def v1_basic(user_id: str) -> str:
        """版本 1：基础格式"""
        return f"V:1|USER:{user_id}"
    
    @staticmethod
    def v2_extended(user_id: str, doc_id: str, dept: str) -> str:
        """版本 2：扩展格式"""
        return f"V:2|DOC:{doc_id}|USER:{user_id}|DEPT:{dept}"
```

**原因**：版本号支持未来格式升级。

## 嵌入用户 ID 和时间戳

### 基础示例

```python
from datetime import datetime
from pdf_blind_watermark import PDFWatermarker
from pdf_blind_watermark.core.watermark import WatermarkConfig

def embed_user_tracking_watermark(
    input_pdf: str,
    output_pdf: str,
    user_id: str
):
    """嵌入用户追踪水印"""
    
    # 创建水印文本
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    watermark = f"USER:{user_id}|TIME:{timestamp}"
    
    # 配置水印系统
    config = WatermarkConfig(
        embed_strength=12.0,
        ecc_symbols=32,
        dpi=150,
        quality=85
    )
    
    # 嵌入水印
    watermarker = PDFWatermarker(config)
    watermarker.embed(input_pdf, output_pdf, watermark)
    
    return watermark

# 使用示例
watermark = embed_user_tracking_watermark(
    "contract.pdf",
    "contract_for_user.pdf",
    "U12345"
)
print(f"Embedded: {watermark}")
# 输出: Embedded: USER:U12345|TIME:20241018-143000
```

### 高级示例：完整元数据

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class DocumentMetadata:
    """文档元数据"""
    document_id: str
    user_id: str
    department: str
    access_level: str
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_watermark(self) -> str:
        """转换为水印格式"""
        time_str = self.timestamp.strftime("%Y%m%d-%H%M")
        return (
            f"DOC:{self.document_id}|"
            f"USER:{self.user_id}|"
            f"DEPT:{self.department}|"
            f"LEVEL:{self.access_level}|"
            f"TIME:{time_str}"
        )
    
    @classmethod
    def from_watermark(cls, watermark: str):
        """从水印解析"""
        data = {}
        for part in watermark.split("|"):
            if ":" in part:
                key, value = part.split(":", 1)
                data[key] = value
        
        timestamp = datetime.strptime(data["TIME"], "%Y%m%d-%H%M")
        
        return cls(
            document_id=data["DOC"],
            user_id=data["USER"],
            department=data["DEPT"],
            access_level=data["LEVEL"],
            timestamp=timestamp
        )

# 使用示例
metadata = DocumentMetadata(
    document_id="DOC-2024-0456",
    user_id="U78901",
    department="LEGAL",
    access_level="CONFIDENTIAL"
)

watermark = metadata.to_watermark()
print(f"Watermark: {watermark}")

# 嵌入
watermarker = PDFWatermarker()
watermarker.embed("document.pdf", "document_tracked.pdf", watermark)

# 提取和解析
extracted = watermarker.extract("document_tracked.pdf", source_type="pdf")
recovered_metadata = DocumentMetadata.from_watermark(extracted)

print(f"User: {recovered_metadata.user_id}")
print(f"Department: {recovered_metadata.department}")
print(f"Access Level: {recovered_metadata.access_level}")
```

### 批量嵌入不同水印

```python
from pathlib import Path
from typing import List, Dict

def batch_embed_unique_watermarks(
    template_pdf: str,
    output_dir: str,
    users: List[Dict[str, str]]
):
    """为多个用户批量生成唯一水印的文档"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    watermarker = PDFWatermarker(WatermarkConfig(
        embed_strength=12.0,
        ecc_symbols=32,
        dpi=150,
        quality=85
    ))
    
    results = []
    
    for user in users:
        # 为每个用户生成唯一水印
        metadata = DocumentMetadata(
            document_id=user["doc_id"],
            user_id=user["user_id"],
            department=user["department"],
            access_level=user["access_level"]
        )
        
        watermark = metadata.to_watermark()
        output_file = output_path / f"doc_{user['user_id']}.pdf"
        
        # 嵌入
        watermarker.embed(template_pdf, str(output_file), watermark)
        
        results.append({
            "user_id": user["user_id"],
            "output_file": str(output_file),
            "watermark": watermark
        })
    
    return results

# 使用示例
users = [
    {
        "doc_id": "CONTRACT-2024-001",
        "user_id": "U12345",
        "department": "SALES",
        "access_level": "INTERNAL"
    },
    {
        "doc_id": "CONTRACT-2024-001",
        "user_id": "U67890",
        "department": "LEGAL",
        "access_level": "CONFIDENTIAL"
    },
    {
        "doc_id": "CONTRACT-2024-001",
        "user_id": "U24680",
        "department": "FINANCE",
        "access_level": "RESTRICTED"
    }
]

results = batch_embed_unique_watermarks(
    "contract_template.pdf",
    "./output",
    users
)

for result in results:
    print(f"Generated: {result['output_file']}")
    print(f"  Watermark: {result['watermark']}")
```

## 提取和解析水印

### 基础提取

```python
from pdf_blind_watermark import PDFWatermarker

def extract_and_parse(file_path: str, source_type: str = "pdf"):
    """提取并解析水印"""
    
    watermarker = PDFWatermarker()
    
    try:
        # 提取水印
        watermark = watermarker.extract(file_path, source_type=source_type)
        
        # 解析为字典
        components = {}
        for part in watermark.split("|"):
            if ":" in part:
                key, value = part.split(":", 1)
                components[key] = value
        
        return {
            "success": True,
            "watermark": watermark,
            "components": components
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# 从 PDF 提取
result = extract_and_parse("document.pdf", source_type="pdf")
if result["success"]:
    print(f"User: {result['components'].get('USER')}")
    print(f"Time: {result['components'].get('TIME')}")

# 从截图提取
result = extract_and_parse("screenshot.jpg", source_type="image")
```

### 高级解析：类型验证

```python
from typing import Optional
from datetime import datetime

class WatermarkParser:
    """水印解析器"""
    
    @staticmethod
    def parse(watermark: str) -> Optional[DocumentMetadata]:
        """解析水印为 DocumentMetadata 对象"""
        try:
            components = {}
            for part in watermark.split("|"):
                if ":" in part:
                    key, value = part.split(":", 1)
                    components[key] = value
            
            # 验证必需字段
            required_fields = ["DOC", "USER", "DEPT", "LEVEL", "TIME"]
            for field in required_fields:
                if field not in components:
                    raise ValueError(f"Missing required field: {field}")
            
            # 解析时间
            timestamp = datetime.strptime(
                components["TIME"],
                "%Y%m%d-%H%M"
            )
            
            return DocumentMetadata(
                document_id=components["DOC"],
                user_id=components["USER"],
                department=components["DEPT"],
                access_level=components["LEVEL"],
                timestamp=timestamp
            )
        
        except Exception as e:
            print(f"Parse error: {e}")
            return None
    
    @staticmethod
    def validate(metadata: DocumentMetadata) -> bool:
        """验证元数据的有效性"""
        # 验证用户 ID 格式
        if not metadata.user_id.startswith("U"):
            return False
        
        # 验证文档 ID 格式
        if not metadata.document_id.startswith("DOC-"):
            return False
        
        # 验证时间戳不在未来
        if metadata.timestamp > datetime.now():
            return False
        
        return True

# 使用示例
extracted = watermarker.extract("leaked_document.jpg", source_type="image")
metadata = WatermarkParser.parse(extracted)

if metadata and WatermarkParser.validate(metadata):
    print("✓ Valid watermark found")
    print(f"  Document: {metadata.document_id}")
    print(f"  User: {metadata.user_id}")
    print(f"  Department: {metadata.department}")
else:
    print("✗ Invalid or corrupted watermark")
```

### 多页文档提取

```python
def extract_from_multipage(
    pdf_path: str,
    expected_watermark: Optional[str] = None
) -> dict:
    """从多页 PDF 提取水印并分析一致性"""
    
    watermarker = PDFWatermarker()
    
    # 系统自动处理多页，使用多数投票
    extracted = watermarker.extract(pdf_path, source_type="pdf")
    
    result = {
        "watermark": extracted,
        "match": False,
        "confidence": "high"  # 多数投票提供高置信度
    }
    
    if expected_watermark:
        result["match"] = (extracted == expected_watermark)
    
    return result

# 使用示例
result = extract_from_multipage(
    "multi_page_document.pdf",
    expected_watermark="USER:U12345|TIME:20241018-143000"
)

print(f"Extracted: {result['watermark']}")
print(f"Match: {'✓' if result['match'] else '✗'}")
print(f"Confidence: {result['confidence']}")
```

## 审计追踪实现

### 完整审计系统

```python
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

class WatermarkAuditSystem:
    """水印审计系统"""
    
    def __init__(self, audit_dir: str = "./audit_logs"):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.audit_dir / "watermark_audit.json"
        self.logs = self._load_logs()
    
    def _load_logs(self) -> List[dict]:
        """加载审计日志"""
        if self.log_file.exists():
            with open(self.log_file) as f:
                return json.load(f)
        return []
    
    def _save_logs(self):
        """保存审计日志"""
        with open(self.log_file, "w") as f:
            json.dump(self.logs, f, indent=2)
    
    def log_embed(
        self,
        document_id: str,
        user_id: str,
        watermark: str,
        output_file: str,
        metadata: Optional[dict] = None
    ):
        """记录嵌入事件"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "EMBED",
            "document_id": document_id,
            "user_id": user_id,
            "watermark": watermark,
            "output_file": output_file,
            "metadata": metadata or {}
        }
        self.logs.append(entry)
        self._save_logs()
        return entry
    
    def log_extract(
        self,
        source_file: str,
        watermark: Optional[str],
        success: bool,
        metadata: Optional[dict] = None
    ):
        """记录提取事件"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "EXTRACT",
            "source_file": source_file,
            "watermark": watermark,
            "success": success,
            "metadata": metadata or {}
        }
        self.logs.append(entry)
        self._save_logs()
        return entry
    
    def log_leak_detection(
        self,
        source_file: str,
        watermark: str,
        responsible_user: str,
        metadata: Optional[dict] = None
    ):
        """记录泄露检测事件"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "LEAK_DETECTED",
            "source_file": source_file,
            "watermark": watermark,
            "responsible_user": responsible_user,
            "metadata": metadata or {},
            "severity": "HIGH",
            "status": "INVESTIGATING"
        }
        self.logs.append(entry)
        self._save_logs()
        return entry
    
    def find_by_user(self, user_id: str) -> List[dict]:
        """查找用户的所有活动"""
        return [
            log for log in self.logs
            if log.get("user_id") == user_id or
               log.get("responsible_user") == user_id
        ]
    
    def find_by_document(self, document_id: str) -> List[dict]:
        """查找文档的所有活动"""
        return [
            log for log in self.logs
            if log.get("document_id") == document_id
        ]
    
    def find_leaks(self) -> List[dict]:
        """查找所有泄露事件"""
        return [
            log for log in self.logs
            if log.get("event_type") == "LEAK_DETECTED"
        ]
    
    def generate_report(self, user_id: Optional[str] = None) -> dict:
        """生成审计报告"""
        logs = self.find_by_user(user_id) if user_id else self.logs
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_events": len(logs),
            "event_breakdown": {},
            "user_activity": {},
            "leak_summary": {
                "total_leaks": 0,
                "by_user": {}
            }
        }
        
        # 事件类型统计
        for log in logs:
            event_type = log.get("event_type", "UNKNOWN")
            report["event_breakdown"][event_type] = \
                report["event_breakdown"].get(event_type, 0) + 1
            
            # 用户活动统计
            user = log.get("user_id") or log.get("responsible_user")
            if user:
                report["user_activity"][user] = \
                    report["user_activity"].get(user, 0) + 1
            
            # 泄露统计
            if event_type == "LEAK_DETECTED":
                report["leak_summary"]["total_leaks"] += 1
                resp_user = log.get("responsible_user")
                if resp_user:
                    report["leak_summary"]["by_user"][resp_user] = \
                        report["leak_summary"]["by_user"].get(resp_user, 0) + 1
        
        return report

# 使用示例：完整工作流
audit = WatermarkAuditSystem()
watermarker = PDFWatermarker()

# 1. 嵌入阶段
metadata = DocumentMetadata(
    document_id="DOC-2024-0789",
    user_id="U12345",
    department="FINANCE",
    access_level="CONFIDENTIAL"
)

watermark = metadata.to_watermark()
watermarker.embed("sensitive.pdf", "sensitive_U12345.pdf", watermark)

audit.log_embed(
    document_id=metadata.document_id,
    user_id=metadata.user_id,
    watermark=watermark,
    output_file="sensitive_U12345.pdf",
    metadata={"department": metadata.department}
)

# 2. 泄露检测阶段
try:
    extracted = watermarker.extract("leaked_image.jpg", source_type="image")
    
    audit.log_extract(
        source_file="leaked_image.jpg",
        watermark=extracted,
        success=True
    )
    
    # 解析水印
    leaked_metadata = DocumentMetadata.from_watermark(extracted)
    
    # 记录泄露
    audit.log_leak_detection(
        source_file="leaked_image.jpg",
        watermark=extracted,
        responsible_user=leaked_metadata.user_id,
        metadata={
            "document_id": leaked_metadata.document_id,
            "department": leaked_metadata.department,
            "access_level": leaked_metadata.access_level
        }
    )
    
    print(f"✗ LEAK DETECTED!")
    print(f"  Responsible User: {leaked_metadata.user_id}")
    print(f"  Document: {leaked_metadata.document_id}")
    print(f"  Department: {leaked_metadata.department}")
    
except Exception as e:
    audit.log_extract(
        source_file="leaked_image.jpg",
        watermark=None,
        success=False,
        metadata={"error": str(e)}
    )

# 3. 生成报告
report = audit.generate_report()
print(f"\nAudit Summary:")
print(f"  Total Events: {report['total_events']}")
print(f"  Total Leaks: {report['leak_summary']['total_leaks']}")
print(f"  Event Breakdown: {report['event_breakdown']}")
```

## 实际应用场景

### 场景 1：合同管理系统

```python
class ContractWatermarkSystem:
    """合同水印管理系统"""
    
    def __init__(self):
        self.audit = WatermarkAuditSystem("./contract_audit")
        self.watermarker = PDFWatermarker(WatermarkConfig(
            embed_strength=14.0,
            ecc_symbols=32,
            dpi=150,
            quality=85
        ))
    
    def distribute_contract(
        self,
        contract_id: str,
        recipient_email: str,
        recipient_name: str,
        department: str
    ) -> dict:
        """分发带水印的合同"""
        
        # 生成唯一用户 ID
        user_id = self._generate_user_id(recipient_email)
        
        # 创建水印
        metadata = DocumentMetadata(
            document_id=contract_id,
            user_id=user_id,
            department=department,
            access_level="CONFIDENTIAL"
        )
        
        watermark = metadata.to_watermark()
        output_file = f"contracts/{contract_id}_{user_id}.pdf"
        
        # 嵌入水印
        self.watermarker.embed(
            f"templates/{contract_id}.pdf",
            output_file,
            watermark
        )
        
        # 记录审计日志
        self.audit.log_embed(
            document_id=contract_id,
            user_id=user_id,
            watermark=watermark,
            output_file=output_file,
            metadata={
                "recipient_email": recipient_email,
                "recipient_name": recipient_name,
                "department": department
            }
        )
        
        return {
            "contract_id": contract_id,
            "file_path": output_file,
            "watermark": watermark,
            "user_id": user_id
        }
    
    def investigate_leak(self, leaked_file: str) -> dict:
        """调查泄露文件"""
        
        try:
            # 提取水印
            extracted = self.watermarker.extract(leaked_file, source_type="image")
            
            # 解析元数据
            metadata = DocumentMetadata.from_watermark(extracted)
            
            # 查找用户历史
            user_history = self.audit.find_by_user(metadata.user_id)
            
            # 记录泄露
            self.audit.log_leak_detection(
                source_file=leaked_file,
                watermark=extracted,
                responsible_user=metadata.user_id,
                metadata={"document_id": metadata.document_id}
            )
            
            return {
                "success": True,
                "responsible_user": metadata.user_id,
                "document_id": metadata.document_id,
                "department": metadata.department,
                "user_history_count": len(user_history),
                "action_required": "Contact user and review department security"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action_required": "Manual investigation required"
            }
    
    @staticmethod
    def _generate_user_id(email: str) -> str:
        """从邮箱生成用户 ID"""
        import hashlib
        hash_obj = hashlib.md5(email.encode())
        return f"U{hash_obj.hexdigest()[:8].upper()}"
```

### 场景 2：文档下载监控

```python
class DocumentDownloadMonitor:
    """文档下载监控系统"""
    
    def __init__(self):
        self.audit = WatermarkAuditSystem("./download_audit")
        self.watermarker = PDFWatermarker()
    
    def prepare_download(
        self,
        document_id: str,
        user_id: str,
        user_ip: str
    ) -> str:
        """准备下载（嵌入水印）"""
        
        # 创建带时间戳的水印
        metadata = DocumentMetadata(
            document_id=document_id,
            user_id=user_id,
            department="DOWNLOAD",
            access_level="TRACKED"
        )
        
        watermark = metadata.to_watermark()
        temp_file = f"/tmp/{document_id}_{user_id}.pdf"
        
        # 嵌入水印
        self.watermarker.embed(
            f"documents/{document_id}.pdf",
            temp_file,
            watermark
        )
        
        # 记录下载
        self.audit.log_embed(
            document_id=document_id,
            user_id=user_id,
            watermark=watermark,
            output_file=temp_file,
            metadata={
                "user_ip": user_ip,
                "download_time": datetime.now().isoformat()
            }
        )
        
        return temp_file
```

## 最佳实践

### 1. 水印格式标准化

```python
# 定义企业级水印格式标准
class EnterpriseWatermarkStandard:
    VERSION = "2.0"
    
    @classmethod
    def create(cls, **kwargs) -> str:
        """创建符合标准的水印"""
        required = ["doc_id", "user_id", "dept"]
        for key in required:
            if key not in kwargs:
                raise ValueError(f"Missing required field: {key}")
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        
        return (
            f"V:{cls.VERSION}|"
            f"DOC:{kwargs['doc_id']}|"
            f"USER:{kwargs['user_id']}|"
            f"DEPT:{kwargs['dept']}|"
            f"TIME:{timestamp}"
        )
```

### 2. 错误处理和降级

```python
def safe_embed_watermark(
    input_pdf: str,
    output_pdf: str,
    metadata: DocumentMetadata,
    fallback: bool = True
) -> dict:
    """安全嵌入水印，支持降级"""
    
    watermarker = PDFWatermarker()
    
    try:
        # 尝试完整嵌入
        watermark = metadata.to_watermark()
        watermarker.embed(input_pdf, output_pdf, watermark)
        
        return {
            "success": True,
            "watermark": watermark,
            "method": "full"
        }
    
    except Exception as e:
        if fallback:
            # 降级：仅嵌入用户 ID
            simplified = f"USER:{metadata.user_id}"
            try:
                watermarker.embed(input_pdf, output_pdf, simplified)
                return {
                    "success": True,
                    "watermark": simplified,
                    "method": "simplified",
                    "warning": str(e)
                }
            except Exception as e2:
                return {
                    "success": False,
                    "error": str(e2),
                    "method": "failed"
                }
        else:
            return {
                "success": False,
                "error": str(e),
                "method": "failed"
            }
```

### 3. 定期验证

```python
def verify_watermark_integrity(
    pdf_path: str,
    expected_metadata: DocumentMetadata
) -> dict:
    """验证水印完整性"""
    
    watermarker = PDFWatermarker()
    
    try:
        # 提取水印
        extracted = watermarker.extract(pdf_path, source_type="pdf")
        
        # 解析
        actual_metadata = DocumentMetadata.from_watermark(extracted)
        
        # 验证
        matches = {
            "document_id": actual_metadata.document_id == expected_metadata.document_id,
            "user_id": actual_metadata.user_id == expected_metadata.user_id,
            "department": actual_metadata.department == expected_metadata.department
        }
        
        all_match = all(matches.values())
        
        return {
            "valid": all_match,
            "matches": matches,
            "extracted": extracted
        }
    
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }
```

### 4. 性能优化

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def batch_embed_parallel(
    documents: List[dict],
    max_workers: int = 4
) -> List[dict]:
    """并行批量嵌入"""
    
    def embed_single(doc_info):
        watermarker = PDFWatermarker()
        metadata = DocumentMetadata(**doc_info["metadata"])
        watermark = metadata.to_watermark()
        
        watermarker.embed(
            doc_info["input"],
            doc_info["output"],
            watermark
        )
        
        return {
            "success": True,
            "document_id": metadata.document_id,
            "output": doc_info["output"]
        }
    
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(embed_single, doc): doc
            for doc in documents
        }
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                doc = futures[future]
                results.append({
                    "success": False,
                    "document_id": doc["metadata"]["document_id"],
                    "error": str(e)
                })
    
    return results
```

### 5. 合规性文档

保留以下记录用于审计：

1. **嵌入记录** - 每次嵌入的完整日志
2. **提取记录** - 所有提取尝试
3. **泄露事件** - 检测到的泄露及处理
4. **配置历史** - 水印配置的变更
5. **验证报告** - 定期完整性检查结果
