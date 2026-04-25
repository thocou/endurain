"""Tests for api_keys.router module."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

import api_keys.router as api_keys_router
import api_keys.schema as api_keys_schema
import auth.security as auth_security
import core.database as core_database


@pytest.fixture
def api_keys_app(mock_db):
    """
    Create a FastAPI app with api_keys router.

    Args:
        mock_db: Mock database session.

    Returns:
        FastAPI: Test app with api_keys router.
    """
    app = FastAPI()
    app.include_router(
        api_keys_router.router, prefix="/api_keys"
    )

    app.dependency_overrides[
        auth_security.get_sub_from_access_token
    ] = lambda: 1
    app.dependency_overrides[
        auth_security.validate_access_token
    ] = lambda: None
    app.dependency_overrides[
        core_database.get_db
    ] = lambda: mock_db

    return app


@pytest.fixture
def api_keys_client(api_keys_app):
    """
    Create a TestClient for the api_keys app.

    Args:
        api_keys_app: The FastAPI app fixture.

    Returns:
        TestClient: Test client for requests.
    """
    return TestClient(api_keys_app)


class TestCreateApiKeyEndpoint:
    """Tests for POST /api_keys endpoint."""

    @patch("api_keys.router.api_keys_crud.create_api_key")
    def test_create_success(
        self, mock_create, api_keys_client
    ):
        """Test successful key creation returns 201."""
        now = datetime.now(timezone.utc)
        mock_create.return_value = (
            api_keys_schema.ApiKeyCreated(
                id=1,
                name="Test Key",
                key_prefix="abcd1234",
                created_at=now,
                last_used_at=None,
                expires_at=None,
                full_key="full-raw-key-value",
            )
        )

        response = api_keys_client.post(
            "/api_keys",
            json={"name": "Test Key"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Key"
        assert data["full_key"] == "full-raw-key-value"
        assert data["key_prefix"] == "abcd1234"
        mock_create.assert_called_once()

    @patch("api_keys.router.api_keys_crud.create_api_key")
    def test_create_passes_user_id(
        self, mock_create, api_keys_client
    ):
        """Test user_id from token is passed."""
        now = datetime.now(timezone.utc)
        mock_create.return_value = (
            api_keys_schema.ApiKeyCreated(
                id=1,
                name="Key",
                key_prefix="12345678",
                created_at=now,
                last_used_at=None,
                expires_at=None,
                full_key="key",
            )
        )

        api_keys_client.post(
            "/api_keys",
            json={"name": "Key"},
        )

        args = mock_create.call_args
        assert args[0][0] == 1  # user_id
        assert args[0][1] == "Key"  # name

    def test_create_missing_name(self, api_keys_client):
        """Test missing name returns 422."""
        response = api_keys_client.post(
            "/api_keys",
            json={},
        )

        assert response.status_code == 422

    @patch("api_keys.router.api_keys_crud.create_api_key")
    def test_create_server_error(
        self, mock_create, api_keys_client
    ):
        """Test server error returns 500."""
        mock_create.side_effect = HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal Server Error",
        )

        response = api_keys_client.post(
            "/api_keys",
            json={"name": "Key"},
        )

        assert response.status_code == 500


class TestListApiKeysEndpoint:
    """Tests for GET /api_keys endpoint."""

    @patch(
        "api_keys.router.api_keys_crud.list_user_api_keys"
    )
    def test_list_success(
        self, mock_list, api_keys_client
    ):
        """Test successful key listing."""
        now = datetime.now(timezone.utc)
        mock_key = MagicMock()
        mock_key.id = 1
        mock_key.name = "Test Key"
        mock_key.key_prefix = "abcd1234"
        mock_key.created_at = now
        mock_key.last_used_at = None
        mock_key.expires_at = None
        mock_list.return_value = [mock_key]

        response = api_keys_client.get("/api_keys")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Key"

    @patch(
        "api_keys.router.api_keys_crud.list_user_api_keys"
    )
    def test_list_empty(
        self, mock_list, api_keys_client
    ):
        """Test empty list returns 200."""
        mock_list.return_value = []

        response = api_keys_client.get("/api_keys")

        assert response.status_code == 200
        assert response.json() == []

    @patch(
        "api_keys.router.api_keys_crud.list_user_api_keys"
    )
    def test_list_does_not_expose_full_key(
        self, mock_list, api_keys_client
    ):
        """Test list response has no full_key."""
        now = datetime.now(timezone.utc)
        mock_key = MagicMock()
        mock_key.id = 1
        mock_key.name = "Key"
        mock_key.key_prefix = "abcd1234"
        mock_key.created_at = now
        mock_key.last_used_at = None
        mock_key.expires_at = None
        mock_list.return_value = [mock_key]

        response = api_keys_client.get("/api_keys")

        data = response.json()
        assert "full_key" not in data[0]


class TestDeleteApiKeyEndpoint:
    """Tests for DELETE /api_keys/{key_id} endpoint."""

    @patch(
        "api_keys.router.api_keys_crud.delete_api_key"
    )
    def test_delete_success(
        self, mock_delete, api_keys_client
    ):
        """Test successful deletion returns 204."""
        mock_delete.return_value = None

        response = api_keys_client.delete(
            "/api_keys/5"
        )

        assert response.status_code == 204
        mock_delete.assert_called_once()

    @patch(
        "api_keys.router.api_keys_crud.delete_api_key"
    )
    def test_delete_not_found(
        self, mock_delete, api_keys_client
    ):
        """Test deleting nonexistent key returns 404."""
        mock_delete.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key 99 not found",
        )

        response = api_keys_client.delete(
            "/api_keys/99"
        )

        assert response.status_code == 404

    @patch(
        "api_keys.router.api_keys_crud.delete_api_key"
    )
    def test_delete_server_error(
        self, mock_delete, api_keys_client
    ):
        """Test server error returns 500."""
        mock_delete.side_effect = HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal Server Error",
        )

        response = api_keys_client.delete(
            "/api_keys/5"
        )

        assert response.status_code == 500
