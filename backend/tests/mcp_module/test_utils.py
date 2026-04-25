"""Tests for mcp_module.utils module."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_module.utils import get_user_id, get_db


MODULE = "mcp_module.utils"


class TestGetUserId:
    """Tests for get_user_id function."""

    @patch(f"{MODULE}.get_access_token")
    def test_extracts_user_id_from_context(
        self, mock_get_token
    ):
        """
        Test that get_user_id returns the integer
        client_id from the MCP access token.
        """
        mock_token = MagicMock()
        mock_token.client_id = "7"
        mock_get_token.return_value = mock_token
        ctx = MagicMock()

        result = get_user_id(ctx)

        assert result == 7
        assert isinstance(result, int)

    @patch(f"{MODULE}.get_access_token")
    def test_extracts_large_user_id(
        self, mock_get_token
    ):
        """
        Test that get_user_id handles large user IDs.
        """
        mock_token = MagicMock()
        mock_token.client_id = "99999"
        mock_get_token.return_value = mock_token
        ctx = MagicMock()

        result = get_user_id(ctx)

        assert result == 99999

    @patch(f"{MODULE}.get_access_token")
    def test_raises_on_non_numeric_client_id(
        self, mock_get_token
    ):
        """
        Test that get_user_id raises ValueError for
        non-numeric client_id values.
        """
        mock_token = MagicMock()
        mock_token.client_id = "not-a-number"
        mock_get_token.return_value = mock_token
        ctx = MagicMock()

        with pytest.raises(ValueError):
            get_user_id(ctx)

    @patch(f"{MODULE}.get_access_token")
    def test_raises_when_no_token(
        self, mock_get_token
    ):
        """
        Test that get_user_id raises ValueError when
        no access token is available.
        """
        mock_get_token.return_value = None
        ctx = MagicMock()

        with pytest.raises(ValueError):
            get_user_id(ctx)


class TestGetDb:
    """Tests for get_db function."""

    def test_returns_session_instance(self):
        """
        Test that get_db returns a new SessionLocal
        instance.
        """
        with patch(
            "mcp_module.utils.SessionLocal"
        ) as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            result = get_db()

            assert result is mock_session
            mock_session_cls.assert_called_once()
