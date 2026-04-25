"""Tests for api_keys.utils module."""

import hashlib
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

import api_keys.utils as api_keys_utils
import api_keys.models as api_keys_models


@pytest.fixture
def mock_user():
    """
    Create a mock user object.

    Returns:
        MagicMock: A mock user with id=1.
    """
    user = MagicMock()
    user.id = 1
    return user


@pytest.fixture
def mock_api_key(mock_user):
    """
    Create a mock API key with associated user.

    Args:
        mock_user: The mock user fixture.

    Returns:
        MagicMock: A mock UserApiKey object.
    """
    api_key = MagicMock(
        spec=api_keys_models.UserApiKey
    )
    api_key.users = mock_user
    api_key.expires_at = None
    api_key.last_used_at = None
    return api_key


class TestValidateApiKey:
    """Tests for validate_api_key function."""

    def test_valid_key_returns_user(
        self, mock_db, mock_api_key
    ):
        """Test valid key returns associated user."""
        raw_key = "test-valid-key-123"
        key_hash = hashlib.sha256(
            raw_key.encode()
        ).hexdigest()

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_api_key

        result = api_keys_utils.validate_api_key(
            raw_key, mock_db
        )

        assert result is mock_api_key.users
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(
            mock_api_key
        )

    def test_invalid_key_returns_none(self, mock_db):
        """Test invalid key returns None."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = api_keys_utils.validate_api_key(
            "invalid-key", mock_db
        )

        assert result is None

    def test_expired_key_returns_none(
        self, mock_db, mock_api_key
    ):
        """Test expired key returns None."""
        mock_api_key.expires_at = (
            datetime.now(timezone.utc)
            - timedelta(hours=1)
        )

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_api_key

        result = api_keys_utils.validate_api_key(
            "expired-key", mock_db
        )

        assert result is None

    def test_non_expired_key_returns_user(
        self, mock_db, mock_api_key
    ):
        """Test non-expired key returns user."""
        mock_api_key.expires_at = (
            datetime.now(timezone.utc)
            + timedelta(hours=1)
        )

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_api_key

        result = api_keys_utils.validate_api_key(
            "valid-key", mock_db
        )

        assert result is mock_api_key.users

    def test_updates_last_used_at(
        self, mock_db, mock_api_key
    ):
        """Test last_used_at is updated on use."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_api_key

        api_keys_utils.validate_api_key(
            "some-key", mock_db
        )

        assert mock_api_key.last_used_at is not None

    def test_db_exception_returns_none(self, mock_db):
        """Test database error returns None."""
        mock_db.query.side_effect = Exception(
            "DB error"
        )

        result = api_keys_utils.validate_api_key(
            "key", mock_db
        )

        assert result is None

    def test_hashes_token_with_sha256(self, mock_db):
        """Test token is hashed with SHA-256."""
        raw_key = "my-secret-key"
        expected_hash = hashlib.sha256(
            raw_key.encode()
        ).hexdigest()

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        api_keys_utils.validate_api_key(
            raw_key, mock_db
        )

        mock_db.query.assert_called_once_with(
            api_keys_models.UserApiKey
        )
