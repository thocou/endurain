"""Shared fixtures for mcp_module tests."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_access_token():
    """
    Patch get_access_token to return a token
    with client_id="42".

    Autouse ensures all MCP tool tests have a
    valid access token in the contextvar.

    Returns:
        MagicMock: The mock access token.
    """
    token = MagicMock()
    token.client_id = "42"
    with patch(
        "mcp_module.utils.get_access_token",
        return_value=token,
    ):
        yield token
