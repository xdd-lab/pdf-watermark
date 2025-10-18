"""Unit tests for steganography metadata."""

import pytest
import json
from datetime import datetime
from pdf_blind_watermark.steganography.metadata import StegoMetadata


class TestStegoMetadata:
    """Test suite for StegoMetadata."""

    def test_create_metadata(self):
        """Test creating metadata with all fields."""
        metadata = StegoMetadata(
            user_id="user123",
            timestamp="2024-01-01T12:00:00",
            tracking_token="token456",
        )

        assert metadata.user_id == "user123"
        assert metadata.timestamp == "2024-01-01T12:00:00"
        assert metadata.tracking_token == "token456"

    def test_create_with_auto_timestamp(self):
        """Test creating metadata with auto-generated timestamp."""
        before = datetime.utcnow()
        metadata = StegoMetadata.create(
            user_id="user123",
            tracking_token="token456",
        )
        after = datetime.utcnow()

        timestamp = datetime.fromisoformat(metadata.timestamp)
        assert before <= timestamp <= after

    def test_create_with_custom_fields(self):
        """Test metadata with custom fields."""
        custom = {"department": "IT", "priority": "high"}
        metadata = StegoMetadata.create(
            user_id="user123",
            tracking_token="token456",
            custom_fields=custom,
        )

        assert metadata.custom_fields == custom

    def test_to_json(self):
        """Test converting metadata to JSON."""
        metadata = StegoMetadata(
            user_id="user123",
            timestamp="2024-01-01T12:00:00",
            tracking_token="token456",
        )

        json_str = metadata.to_json()
        assert isinstance(json_str, str)

        parsed = json.loads(json_str)
        assert parsed["user_id"] == "user123"
        assert parsed["timestamp"] == "2024-01-01T12:00:00"
        assert parsed["tracking_token"] == "token456"

    def test_from_json(self):
        """Test creating metadata from JSON."""
        json_str = '{"user_id":"user123","timestamp":"2024-01-01T12:00:00","tracking_token":"token456","custom_fields":null}'
        metadata = StegoMetadata.from_json(json_str)

        assert metadata.user_id == "user123"
        assert metadata.timestamp == "2024-01-01T12:00:00"
        assert metadata.tracking_token == "token456"

    def test_to_bytes(self):
        """Test converting metadata to bytes."""
        metadata = StegoMetadata(
            user_id="user123",
            timestamp="2024-01-01T12:00:00",
            tracking_token="token456",
        )

        data = metadata.to_bytes()
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_from_bytes(self):
        """Test creating metadata from bytes."""
        original = StegoMetadata(
            user_id="user123",
            timestamp="2024-01-01T12:00:00",
            tracking_token="token456",
        )

        data = original.to_bytes()
        recovered = StegoMetadata.from_bytes(data)

        assert recovered.user_id == original.user_id
        assert recovered.timestamp == original.timestamp
        assert recovered.tracking_token == original.tracking_token

    def test_roundtrip_json(self):
        """Test JSON serialization roundtrip."""
        original = StegoMetadata.create(
            user_id="user123",
            tracking_token="token456",
            custom_fields={"key": "value"},
        )

        json_str = original.to_json()
        recovered = StegoMetadata.from_json(json_str)

        assert recovered.user_id == original.user_id
        assert recovered.tracking_token == original.tracking_token
        assert recovered.custom_fields == original.custom_fields

    def test_roundtrip_bytes(self):
        """Test bytes serialization roundtrip."""
        original = StegoMetadata.create(
            user_id="user123",
            tracking_token="token456",
        )

        data = original.to_bytes()
        recovered = StegoMetadata.from_bytes(data)

        assert recovered.user_id == original.user_id
        assert recovered.tracking_token == original.tracking_token

    def test_unicode_fields(self):
        """Test metadata with unicode characters."""
        metadata = StegoMetadata.create(
            user_id="用户123",
            tracking_token="令牌456",
        )

        data = metadata.to_bytes()
        recovered = StegoMetadata.from_bytes(data)

        assert recovered.user_id == "用户123"
        assert recovered.tracking_token == "令牌456"

    def test_empty_custom_fields(self):
        """Test metadata with empty custom fields."""
        metadata = StegoMetadata(
            user_id="user123",
            timestamp="2024-01-01T12:00:00",
            tracking_token="token456",
            custom_fields={},
        )

        json_str = metadata.to_json()
        recovered = StegoMetadata.from_json(json_str)

        assert recovered.custom_fields == {}

    def test_complex_custom_fields(self):
        """Test metadata with complex custom fields."""
        custom = {
            "nested": {"level": 2},
            "list": [1, 2, 3],
            "string": "value",
        }

        metadata = StegoMetadata.create(
            user_id="user123",
            tracking_token="token456",
            custom_fields=custom,
        )

        data = metadata.to_bytes()
        recovered = StegoMetadata.from_bytes(data)

        assert recovered.custom_fields == custom
