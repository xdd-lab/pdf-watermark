from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class StegoMetadata:
    """Structured metadata for PDF text steganography."""

    user_id: str
    timestamp: str
    tracking_token: str
    custom_fields: Optional[Dict[str, Any]] = None

    @classmethod
    def create(
        cls,
        user_id: str,
        tracking_token: str,
        timestamp: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> StegoMetadata:
        """Create metadata with optional auto-generated timestamp."""
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        return cls(
            user_id=user_id,
            timestamp=timestamp,
            tracking_token=tracking_token,
            custom_fields=custom_fields,
        )

    def to_json(self) -> str:
        """Convert metadata to JSON string."""
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> StegoMetadata:
        """Create metadata from JSON string."""
        data = json.loads(json_str)
        return cls(**data)

    def to_bytes(self) -> bytes:
        """Convert metadata to bytes."""
        return self.to_json().encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> StegoMetadata:
        """Create metadata from bytes."""
        return cls.from_json(data.decode("utf-8"))
