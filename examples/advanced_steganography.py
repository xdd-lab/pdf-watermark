"""
Advanced text steganography examples with user ID and timestamp embedding.

This example demonstrates how to:
1. Embed structured watermarks with user IDs and timestamps
2. Extract and parse watermarks
3. Handle multiple pages with combined extraction results
4. Implement audit trails and compliance workflows
"""

from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from pdf_blind_watermark import PDFWatermarker
from pdf_blind_watermark.core.watermark import WatermarkConfig


class WatermarkGenerator:
    """Generate structured watermarks for document tracking."""
    
    @staticmethod
    def create_user_watermark(user_id: str, timestamp: Optional[datetime] = None) -> str:
        """Create a watermark with user ID and timestamp."""
        if timestamp is None:
            timestamp = datetime.now()
        
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        return f"USER:{user_id}|TIME:{timestamp_str}"
    
    @staticmethod
    def create_document_watermark(
        user_id: str,
        document_id: str,
        department: str,
        timestamp: Optional[datetime] = None
    ) -> str:
        """Create a comprehensive document watermark."""
        if timestamp is None:
            timestamp = datetime.now()
        
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M")
        return f"DOC:{document_id}|USER:{user_id}|DEPT:{department}|{timestamp_str}"
    
    @staticmethod
    def parse_watermark(watermark: str) -> Dict[str, str]:
        """Parse a structured watermark into components."""
        components = {}
        
        # Split by pipe separator
        parts = watermark.split("|")
        
        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                components[key] = value
            else:
                # Handle timestamp without key
                components["TIMESTAMP"] = part
        
        return components


def example_1_user_tracking():
    """Example 1: Track document access with user ID and timestamp."""
    print("=" * 80)
    print("Example 1: User Tracking with Timestamps")
    print("=" * 80)
    
    # Configuration for balance between robustness and quality
    config = WatermarkConfig(
        embed_strength=12.0,
        ecc_symbols=32,
        dpi=150,
        quality=85
    )
    
    watermarker = PDFWatermarker(config)
    generator = WatermarkGenerator()
    
    # Simulate sending a document to a user
    user_id = "U12345"
    watermark_text = generator.create_user_watermark(user_id)
    
    print(f"\n1. Generating watermark for user: {user_id}")
    print(f"   Watermark text: {watermark_text}")
    
    # In production, embed this into the PDF
    print(f"\n2. Embedding watermark...")
    print(f"   watermarker.embed('contract.pdf', 'contract_watermarked.pdf', '{watermark_text}')")
    
    # Later, extract and verify
    print(f"\n3. Extracting watermark from leaked document...")
    print(f"   extracted = watermarker.extract('leaked_screenshot.jpg', source_type='image')")
    
    # Parse the extracted watermark
    print(f"\n4. Parsing extracted watermark...")
    components = generator.parse_watermark(watermark_text)
    print(f"   User ID: {components.get('USER')}")
    print(f"   Access Time: {components.get('TIME')}")
    
    print(f"\n✓ Document leak traced to user: {components.get('USER')}")


def example_2_comprehensive_tracking():
    """Example 2: Comprehensive document tracking with multiple metadata."""
    print("\n" + "=" * 80)
    print("Example 2: Comprehensive Document Tracking")
    print("=" * 80)
    
    config = WatermarkConfig(
        embed_strength=14.0,
        ecc_symbols=32,
        dpi=180,
        quality=85
    )
    
    watermarker = PDFWatermarker(config)
    generator = WatermarkGenerator()
    
    # Create comprehensive watermark
    watermark_text = generator.create_document_watermark(
        user_id="U78901",
        document_id="DOC-2024-0123",
        department="LEGAL",
        timestamp=datetime(2024, 10, 18, 14, 30, 0)
    )
    
    print(f"\n1. Generated watermark:")
    print(f"   {watermark_text}")
    
    # Parse components
    components = generator.parse_watermark(watermark_text)
    
    print(f"\n2. Watermark components:")
    for key, value in components.items():
        print(f"   - {key}: {value}")
    
    print(f"\n3. Audit trail information:")
    print(f"   Document: {components.get('DOC')}")
    print(f"   Accessed by: {components.get('USER')}")
    print(f"   Department: {components.get('DEPT')}")
    print(f"   Access time: {components.get('TIME', 'Unknown')}")


def example_3_multi_page_extraction():
    """Example 3: Extract watermarks from multi-page documents."""
    print("\n" + "=" * 80)
    print("Example 3: Multi-Page Document Extraction")
    print("=" * 80)
    
    config = WatermarkConfig(
        embed_strength=12.0,
        ecc_symbols=32,
        dpi=150,
        quality=85
    )
    
    watermarker = PDFWatermarker(config)
    
    # Simulate extraction from multi-page PDF
    print("\n1. Extracting from multi-page PDF...")
    print("   The system automatically:")
    print("   - Extracts watermark from each page")
    print("   - Uses majority voting for robustness")
    print("   - Returns the most common watermark")
    
    print("\n2. Example extraction results per page:")
    
    # Simulated extraction results
    simulated_extractions = [
        "USER:U12345|TIME:20241018-143000",  # Page 1
        "USER:U12345|TIME:20241018-143000",  # Page 2
        "USER:U12345|TIME:20241018-143000",  # Page 3
        "USER:U12345|TIME:20241018-143000",  # Page 4 (corrupted, failed)
        "USER:U12345|TIME:20241018-143000",  # Page 5
    ]
    
    for i, extraction in enumerate(simulated_extractions, 1):
        print(f"   Page {i}: {extraction}")
    
    print("\n3. Majority voting result:")
    print("   Final watermark: USER:U12345|TIME:20241018-143000")
    print("   Confidence: 5/5 pages")
    
    print("\n✓ Multi-page extraction provides redundancy and reliability")


def example_4_batch_processing():
    """Example 4: Batch processing with unique watermarks per document."""
    print("\n" + "=" * 80)
    print("Example 4: Batch Processing with Unique Watermarks")
    print("=" * 80)
    
    config = WatermarkConfig(
        embed_strength=12.0,
        ecc_symbols=32,
        dpi=150,
        quality=80  # Lower quality for faster batch processing
    )
    
    watermarker = PDFWatermarker(config)
    generator = WatermarkGenerator()
    
    # Simulate batch processing for multiple users
    users = [
        {"id": "U12345", "dept": "FINANCE"},
        {"id": "U67890", "dept": "LEGAL"},
        {"id": "U24680", "dept": "HR"},
    ]
    
    document_id = "DOC-2024-0456"
    
    print(f"\n1. Batch processing document: {document_id}")
    print(f"   Recipients: {len(users)} users")
    
    for i, user in enumerate(users, 1):
        watermark = generator.create_document_watermark(
            user_id=user["id"],
            document_id=document_id,
            department=user["dept"]
        )
        
        output_filename = f"contract_{user['id']}.pdf"
        
        print(f"\n   [{i}/{len(users)}] Processing for {user['id']}...")
        print(f"        Watermark: {watermark}")
        print(f"        Output: {output_filename}")
        
        # In production:
        # watermarker.embed(
        #     "contract_template.pdf",
        #     output_filename,
        #     watermark
        # )
    
    print(f"\n✓ Generated {len(users)} uniquely watermarked documents")


def example_5_extraction_workflow():
    """Example 5: Complete extraction and analysis workflow."""
    print("\n" + "=" * 80)
    print("Example 5: Extraction and Analysis Workflow")
    print("=" * 80)
    
    config = WatermarkConfig(
        embed_strength=12.0,
        ecc_symbols=32,
        dpi=150,
        quality=85,
        rectify=True  # Enable perspective correction for photos
    )
    
    watermarker = PDFWatermarker(config)
    generator = WatermarkGenerator()
    
    print("\n1. Scenario: Leaked document found online")
    print("   Source: Screenshot shared on social media")
    
    print("\n2. Extraction process:")
    print("   - Load image: leaked_screenshot.jpg")
    print("   - Apply perspective correction (if needed)")
    print("   - Extract watermark from frequency domain")
    print("   - Apply Reed-Solomon error correction")
    
    # Simulated extraction
    extracted_watermark = "DOC:DOC-2024-0123|USER:U78901|DEPT:LEGAL|20241018-1430"
    
    print(f"\n3. Extracted watermark:")
    print(f"   {extracted_watermark}")
    
    # Parse and analyze
    components = generator.parse_watermark(extracted_watermark)
    
    print(f"\n4. Analysis:")
    print(f"   ✓ Document identified: {components.get('DOC')}")
    print(f"   ✓ Responsible user: {components.get('USER')}")
    print(f"   ✓ Department: {components.get('DEPT')}")
    print(f"   ✓ Access timestamp: {components.get('TIMESTAMP', 'Unknown')}")
    
    print(f"\n5. Recommended actions:")
    print(f"   - Contact user {components.get('USER')} for investigation")
    print(f"   - Review {components.get('DEPT')} department access logs")
    print(f"   - Audit similar documents accessed by this user")
    print(f"   - Consider security training for the department")
    
    print("\n✓ Complete audit trail established")


def example_6_compliance_integration():
    """Example 6: Integration with compliance and audit systems."""
    print("\n" + "=" * 80)
    print("Example 6: Compliance and Audit Integration")
    print("=" * 80)
    
    # Audit log structure
    audit_log = []
    
    def log_watermark_event(event_type: str, details: Dict):
        """Log watermark events for compliance."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        audit_log.append(entry)
        return entry
    
    generator = WatermarkGenerator()
    
    print("\n1. Document Distribution Event")
    
    # Log embedding event
    watermark = generator.create_document_watermark(
        user_id="U12345",
        document_id="CONFIDENTIAL-2024-789",
        department="EXECUTIVE"
    )
    
    embed_event = log_watermark_event(
        "WATERMARK_EMBED",
        {
            "document_id": "CONFIDENTIAL-2024-789",
            "user_id": "U12345",
            "watermark": watermark,
            "action": "Document distributed to user"
        }
    )
    
    print(f"   Logged: {embed_event['event_type']}")
    print(f"   Time: {embed_event['timestamp']}")
    print(f"   User: U12345")
    
    print("\n2. Leak Detection Event")
    
    # Simulated leak detection
    extracted = watermark  # In reality, extracted from leaked document
    components = generator.parse_watermark(extracted)
    
    detection_event = log_watermark_event(
        "LEAK_DETECTED",
        {
            "document_id": components.get("DOC"),
            "responsible_user": components.get("USER"),
            "department": components.get("DEPT"),
            "watermark": extracted,
            "action": "Leak investigation initiated"
        }
    )
    
    print(f"   Logged: {detection_event['event_type']}")
    print(f"   Time: {detection_event['timestamp']}")
    print(f"   Responsible: {components.get('USER')}")
    
    print("\n3. Audit Trail Summary")
    print(f"   Total events: {len(audit_log)}")
    
    for i, entry in enumerate(audit_log, 1):
        print(f"\n   Event {i}:")
        print(f"   - Type: {entry['event_type']}")
        print(f"   - Time: {entry['timestamp']}")
        print(f"   - Document: {entry['details'].get('document_id')}")
        print(f"   - User: {entry['details'].get('user_id') or entry['details'].get('responsible_user')}")
    
    print("\n✓ Complete audit trail maintained for compliance")
    print("✓ Ready for integration with SIEM/compliance systems")


def run_all_examples():
    """Run all steganography examples."""
    example_1_user_tracking()
    example_2_comprehensive_tracking()
    example_3_multi_page_extraction()
    example_4_batch_processing()
    example_5_extraction_workflow()
    example_6_compliance_integration()
    
    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_examples()
