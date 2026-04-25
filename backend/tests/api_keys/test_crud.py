"""Tests for api_keys.crud module."""

import hashlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

import api_keys.crud as api_keys_crud
import api_keys.models as api_keys_models


class TestCreateApiKey:
    """Tests for create_api_key function."""

    @patch("api_keys.crud.api_keys_models.UserApiKey")
    @patch("api_keys.crud.secrets")
    def test_create_api_key_success(
        self, mock_secrets, mock_model_cls, mock_db
    ):
        """Test successful API key creation."""
        raw_key = "abcd1234efgh5678ijkl9012mnop3456"
        mock_secrets.token_urlsafe.return_value = (
            raw_key
        )
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.name = "Test Key"
        mock_instance.key_prefix = raw_key[:8]
        mock_instance.created_at = MagicMock()
        mock_instance.last_used_at = None
        mock_instance.expires_at = None
        mock_model_cls.return_value = mock_instance

        result = api_keys_crud.create_api_key(
            user_id=1, name="Test Key", db=mock_db
        )

        assert result.full_key == raw_key
        assert result.name == "Test Key"
        mock_db.add.assert_called_once_with(
            mock_instance
        )
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch("api_keys.crud.api_keys_models.UserApiKey")
    @patch("api_keys.crud.secrets")
    def test_create_api_key_stores_hash(
        self, mock_secrets, mock_model_cls, mock_db
    ):
        """Test key hash is SHA-256 of raw key."""
        raw_key = "test-raw-key-value-1234567890ab"
        mock_secrets.token_urlsafe.return_value = (
            raw_key
        )
        expected_hash = hashlib.sha256(
            raw_key.encode()
        ).hexdigest()
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.name = "Key"
        mock_instance.key_prefix = raw_key[:8]
        mock_instance.key_hash = expected_hash
        mock_instance.created_at = MagicMock()
        mock_instance.last_used_at = None
        mock_instance.expires_at = None
        mock_model_cls.return_value = mock_instance

        api_keys_crud.create_api_key(
            user_id=1, name="Key", db=mock_db
        )

        call_kwargs = mock_model_cls.call_args[1]
        assert call_kwargs["key_hash"] == expected_hash

    @patch("api_keys.crud.api_keys_models.UserApiKey")
    @patch("api_keys.crud.secrets")
    def test_create_api_key_prefix_is_first_8(
        self, mock_secrets, mock_model_cls, mock_db
    ):
        """Test key prefix is first 8 chars."""
        raw_key = "PREFIX12rest-of-key-data-here!!"
        mock_secrets.token_urlsafe.return_value = (
            raw_key
        )
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.name = "Key"
        mock_instance.key_prefix = raw_key[:8]
        mock_instance.created_at = MagicMock()
        mock_instance.last_used_at = None
        mock_instance.expires_at = None
        mock_model_cls.return_value = mock_instance

        api_keys_crud.create_api_key(
            user_id=1, name="Key", db=mock_db
        )

        call_kwargs = mock_model_cls.call_args[1]
        assert call_kwargs["key_prefix"] == "PREFIX12"

    @patch("api_keys.crud.api_keys_models.UserApiKey")
    @patch("api_keys.crud.secrets")
    def test_create_api_key_db_error(
        self, mock_secrets, mock_model_cls, mock_db
    ):
        """Test database error raises HTTPException."""
        mock_secrets.token_urlsafe.return_value = (
            "x" * 32
        )
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.name = "Key"
        mock_instance.key_prefix = "xxxxxxxx"
        mock_instance.created_at = MagicMock()
        mock_instance.last_used_at = None
        mock_instance.expires_at = None
        mock_model_cls.return_value = mock_instance
        mock_db.commit.side_effect = Exception(
            "DB error"
        )

        with pytest.raises(HTTPException) as exc_info:
            api_keys_crud.create_api_key(
                user_id=1, name="Key", db=mock_db
            )

        assert (
            exc_info.value.status_code
            == status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    @patch("api_keys.crud.api_keys_models.UserApiKey")
    @patch("api_keys.crud.secrets")
    def test_create_api_key_sets_user_id(
        self, mock_secrets, mock_model_cls, mock_db
    ):
        """Test user_id is set on the model."""
        mock_secrets.token_urlsafe.return_value = (
            "x" * 32
        )
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.name = "Key"
        mock_instance.key_prefix = "xxxxxxxx"
        mock_instance.created_at = MagicMock()
        mock_instance.last_used_at = None
        mock_instance.expires_at = None
        mock_model_cls.return_value = mock_instance

        api_keys_crud.create_api_key(
            user_id=42, name="Key", db=mock_db
        )

        call_kwargs = mock_model_cls.call_args[1]
        assert call_kwargs["user_id"] == 42


class TestListUserApiKeys:
    """Tests for list_user_api_keys function."""

    def test_list_returns_keys(self, mock_db):
        """Test listing keys returns results."""
        mock_key1 = MagicMock(
            spec=api_keys_models.UserApiKey
        )
        mock_key2 = MagicMock(
            spec=api_keys_models.UserApiKey
        )

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            mock_key1,
            mock_key2,
        ]

        result = api_keys_crud.list_user_api_keys(
            user_id=1, db=mock_db
        )

        assert len(result) == 2
        mock_db.query.assert_called_once_with(
            api_keys_models.UserApiKey
        )

    def test_list_returns_empty(self, mock_db):
        """Test listing returns empty list."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = api_keys_crud.list_user_api_keys(
            user_id=1, db=mock_db
        )

        assert result == []

    def test_list_db_error(self, mock_db):
        """Test database error raises HTTPException."""
        mock_db.query.side_effect = Exception(
            "DB error"
        )

        with pytest.raises(HTTPException) as exc_info:
            api_keys_crud.list_user_api_keys(
                user_id=1, db=mock_db
            )

        assert (
            exc_info.value.status_code
            == status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class TestDeleteApiKey:
    """Tests for delete_api_key function."""

    def test_delete_success(self, mock_db):
        """Test successful key deletion."""
        mock_key = MagicMock(
            spec=api_keys_models.UserApiKey
        )

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_key

        api_keys_crud.delete_api_key(
            user_id=1, key_id=5, db=mock_db
        )

        mock_db.delete.assert_called_once_with(
            mock_key
        )
        mock_db.commit.assert_called_once()

    def test_delete_not_found(self, mock_db):
        """Test deleting nonexistent key raises 404."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            api_keys_crud.delete_api_key(
                user_id=1, key_id=99, db=mock_db
            )

        assert (
            exc_info.value.status_code
            == status.HTTP_404_NOT_FOUND
        )
        assert "99" in exc_info.value.detail

    def test_delete_db_error(self, mock_db):
        """Test database error raises HTTPException."""
        mock_key = MagicMock(
            spec=api_keys_models.UserApiKey
        )

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_key
        mock_db.delete.side_effect = Exception(
            "DB error"
        )

        with pytest.raises(HTTPException) as exc_info:
            api_keys_crud.delete_api_key(
                user_id=1, key_id=5, db=mock_db
            )

        assert (
            exc_info.value.status_code
            == status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def test_delete_not_found_reraises(self, mock_db):
        """Test HTTPException from not found re-raises."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            api_keys_crud.delete_api_key(
                user_id=1, key_id=10, db=mock_db
            )

        assert (
            exc_info.value.status_code
            == status.HTTP_404_NOT_FOUND
        )
