"""Tests for mcp_module.auth module."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from mcp_module.auth import EndurainTokenVerifier


@pytest.fixture
def verifier():
    """
    Create an EndurainTokenVerifier instance.

    Returns:
        EndurainTokenVerifier: A token verifier.
    """
    return EndurainTokenVerifier()


@pytest.fixture
def mock_user():
    """
    Create a mock user object.

    Returns:
        MagicMock: A mock user with id=42.
    """
    user = MagicMock()
    user.id = 42
    return user


class TestEndurainTokenVerifier:
    """Tests for EndurainTokenVerifier.verify_token."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_access_token(
        self, verifier, mock_user
    ):
        """
        Test that a valid API key returns an
        AccessToken with correct client_id and scopes.
        """
        with patch(
            "mcp_module.auth.api_keys_utils.validate_api_key",
            return_value=mock_user,
        ), patch(
            "mcp_module.auth.SessionLocal"
        ) as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db

            result = await verifier.verify_token(
                "valid-key-abc123"
            )

            assert result is not None
            assert result.token == "valid-key-abc123"
            assert result.client_id == "42"
            assert result.scopes == ["read", "write"]
            mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(
        self, verifier
    ):
        """
        Test that an invalid API key returns None.
        """
        with patch(
            "mcp_module.auth.api_keys_utils.validate_api_key",
            return_value=None,
        ), patch(
            "mcp_module.auth.SessionLocal"
        ) as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db

            result = await verifier.verify_token(
                "invalid-key"
            )

            assert result is None
            mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_session_closed_on_success(
        self, verifier, mock_user
    ):
        """
        Test that the DB session is always closed
        after a successful validation.
        """
        with patch(
            "mcp_module.auth.api_keys_utils.validate_api_key",
            return_value=mock_user,
        ), patch(
            "mcp_module.auth.SessionLocal"
        ) as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db

            await verifier.verify_token("some-key")

            mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_session_closed_on_failure(
        self, verifier
    ):
        """
        Test that the DB session is always closed
        even when validation returns None.
        """
        with patch(
            "mcp_module.auth.api_keys_utils.validate_api_key",
            return_value=None,
        ), patch(
            "mcp_module.auth.SessionLocal"
        ) as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db

            await verifier.verify_token("bad-key")

            mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_session_closed_on_exception(
        self, verifier
    ):
        """
        Test that the DB session is closed even if
        validate_api_key raises an exception.
        """
        with patch(
            "mcp_module.auth.api_keys_utils.validate_api_key",
            side_effect=Exception("DB error"),
        ), patch(
            "mcp_module.auth.SessionLocal"
        ) as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db

            with pytest.raises(Exception, match="DB error"):
                await verifier.verify_token("key")

            mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_token_to_validate(
        self, verifier
    ):
        """
        Test that the raw token is passed through
        to validate_api_key correctly.
        """
        with patch(
            "mcp_module.auth.api_keys_utils.validate_api_key",
            return_value=None,
        ) as mock_validate, patch(
            "mcp_module.auth.SessionLocal"
        ) as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db

            await verifier.verify_token(
                "my-specific-token-xyz"
            )

            mock_validate.assert_called_once_with(
                "my-specific-token-xyz", mock_db
            )
