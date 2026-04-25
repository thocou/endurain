"""Tests for mcp_module.server module."""

from unittest.mock import patch, MagicMock

import pytest


class TestMcpServerConfiguration:
    """Tests for MCP server instance configuration."""

    @patch("mcp_module.auth.SessionLocal")
    @patch(
        "core.config.ENDURAIN_HOST",
        "http://localhost:8080",
    )
    def test_server_is_fastmcp_instance(self, _):
        """Test mcp_server is a FastMCP instance."""
        from mcp.server.fastmcp import FastMCP
        from mcp_module.server import mcp_server

        assert isinstance(mcp_server, FastMCP)

    @patch("mcp_module.auth.SessionLocal")
    @patch(
        "core.config.ENDURAIN_HOST",
        "http://localhost:8080",
    )
    def test_server_name(self, _):
        """Test server name is 'Endurain'."""
        from mcp_module.server import mcp_server

        assert mcp_server.name == "Endurain"

    @patch("mcp_module.auth.SessionLocal")
    @patch(
        "core.config.ENDURAIN_HOST",
        "http://localhost:8080",
    )
    def test_server_has_token_verifier(self, _):
        """Test server has EndurainTokenVerifier."""
        from mcp_module.server import mcp_server
        from mcp_module.auth import (
            EndurainTokenVerifier,
        )

        assert mcp_server._token_verifier is not None
        assert isinstance(
            mcp_server._token_verifier,
            EndurainTokenVerifier,
        )

    @patch("mcp_module.auth.SessionLocal")
    @patch(
        "core.config.ENDURAIN_HOST",
        "http://localhost:8080",
    )
    def test_server_has_streamable_http_app(self, _):
        """Test server can create streamable HTTP app."""
        from mcp_module.server import mcp_server

        http_app = mcp_server.streamable_http_app()
        assert http_app is not None
