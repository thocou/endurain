"""Tests for api_keys.schema module."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

import api_keys.schema as api_keys_schema


class TestApiKeyCreate:
    """Tests for ApiKeyCreate schema."""

    def test_valid_name(self):
        """Test valid name creates schema."""
        schema = api_keys_schema.ApiKeyCreate(
            name="My API Key"
        )
        assert schema.name == "My API Key"

    def test_name_max_length(self):
        """Test name exceeding 100 chars is rejected."""
        with pytest.raises(ValidationError):
            api_keys_schema.ApiKeyCreate(
                name="x" * 101
            )

    def test_name_at_max_length(self):
        """Test name at exactly 100 chars is accepted."""
        schema = api_keys_schema.ApiKeyCreate(
            name="x" * 100
        )
        assert len(schema.name) == 100

    def test_name_required(self):
        """Test name is required."""
        with pytest.raises(ValidationError):
            api_keys_schema.ApiKeyCreate()

    def test_empty_name(self):
        """Test empty name is accepted by schema."""
        schema = api_keys_schema.ApiKeyCreate(name="")
        assert schema.name == ""


class TestApiKeyResponse:
    """Tests for ApiKeyResponse schema."""

    def test_valid_response(self):
        """Test valid ApiKeyResponse creation."""
        now = datetime.now(timezone.utc)
        schema = api_keys_schema.ApiKeyResponse(
            id=1,
            name="Test Key",
            key_prefix="abcd1234",
            created_at=now,
            last_used_at=None,
            expires_at=None,
        )
        assert schema.id == 1
        assert schema.name == "Test Key"
        assert schema.key_prefix == "abcd1234"
        assert schema.created_at == now
        assert schema.last_used_at is None
        assert schema.expires_at is None

    def test_with_optional_fields(self):
        """Test ApiKeyResponse with optional fields."""
        now = datetime.now(timezone.utc)
        schema = api_keys_schema.ApiKeyResponse(
            id=1,
            name="Test Key",
            key_prefix="abcd1234",
            created_at=now,
            last_used_at=now,
            expires_at=now,
        )
        assert schema.last_used_at == now
        assert schema.expires_at == now

    def test_from_attributes_config(self):
        """Test from_attributes is enabled."""
        assert (
            api_keys_schema.ApiKeyResponse
            .model_config["from_attributes"]
            is True
        )

    def test_missing_required_field(self):
        """Test missing required fields raise error."""
        with pytest.raises(ValidationError):
            api_keys_schema.ApiKeyResponse(
                id=1,
                name="Test Key",
            )


class TestApiKeyCreated:
    """Tests for ApiKeyCreated schema."""

    def test_includes_full_key(self):
        """Test ApiKeyCreated includes full_key."""
        now = datetime.now(timezone.utc)
        schema = api_keys_schema.ApiKeyCreated(
            id=1,
            name="Test Key",
            key_prefix="abcd1234",
            created_at=now,
            last_used_at=None,
            expires_at=None,
            full_key="full-raw-key-value",
        )
        assert schema.full_key == "full-raw-key-value"

    def test_inherits_from_api_key_response(self):
        """Test ApiKeyCreated inherits ApiKeyResponse."""
        assert issubclass(
            api_keys_schema.ApiKeyCreated,
            api_keys_schema.ApiKeyResponse,
        )

    def test_full_key_required(self):
        """Test full_key is required."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            api_keys_schema.ApiKeyCreated(
                id=1,
                name="Test Key",
                key_prefix="abcd1234",
                created_at=now,
                last_used_at=None,
                expires_at=None,
            )
