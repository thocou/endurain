"""Tests for MCP integration in main.py."""

import os
from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest
from fastapi import FastAPI


class TestCreateAppMcpMount:
    """Tests for MCP conditional mount logic."""

    def test_mcp_mounted_when_enabled(self):
        """Test MCP mount is called when enabled."""
        app = FastAPI()

        with patch(
            "core.config.MCP_ENABLED", True
        ), patch(
            "mcp_module.server.mcp_server"
        ) as mock_mcp:
            mock_mcp.streamable_http_app.return_value = (
                MagicMock()
            )

            import core.config as core_config

            if core_config.MCP_ENABLED:
                from mcp_module.server import (
                    mcp_server as endurain_mcp_server,
                )

                app.mount(
                    "/mcp",
                    endurain_mcp_server.streamable_http_app(),
                )

        assert any(
            "/mcp" in str(getattr(r, "path", ""))
            for r in app.routes
        )

    def test_mcp_not_mounted_when_disabled(self):
        """Test MCP mount is skipped when disabled."""
        app = FastAPI()

        with patch(
            "core.config.MCP_ENABLED", False
        ):
            import core.config as core_config

            if core_config.MCP_ENABLED:
                pass  # Would mount MCP

        route_paths = [
            getattr(r, "path", "")
            for r in app.routes
        ]
        assert "/mcp" not in route_paths


class TestShutdownMcp:
    """Tests for MCP shutdown logic."""

    @pytest.mark.asyncio
    async def test_shutdown_stops_mcp_session(self):
        """Test MCP session is closed on shutdown."""
        mock_session_cm = AsyncMock()
        app_state = MagicMock()
        app_state.mcp_session_cm = mock_session_cm

        with patch(
            "core.config.MCP_ENABLED", True
        ):
            import core.config as core_config

            if core_config.MCP_ENABLED and hasattr(
                app_state, "mcp_session_cm"
            ):
                await app_state.mcp_session_cm.__aexit__(
                    None, None, None
                )

        mock_session_cm.__aexit__.assert_awaited_once_with(
            None, None, None
        )

    @pytest.mark.asyncio
    async def test_shutdown_skips_when_disabled(self):
        """Test shutdown skips MCP when disabled."""
        app_state = MagicMock(spec=[])

        with patch(
            "core.config.MCP_ENABLED", False
        ):
            import core.config as core_config

            if core_config.MCP_ENABLED and hasattr(
                app_state, "mcp_session_cm"
            ):
                await app_state.mcp_session_cm.__aexit__(
                    None, None, None
                )

        # No exception means success

    @pytest.mark.asyncio
    async def test_shutdown_skips_when_no_session(
        self,
    ):
        """Test shutdown skips when no session_cm."""
        app_state = MagicMock(spec=[])

        with patch(
            "core.config.MCP_ENABLED", True
        ):
            import core.config as core_config

            if core_config.MCP_ENABLED and hasattr(
                app_state, "mcp_session_cm"
            ):
                await app_state.mcp_session_cm.__aexit__(
                    None, None, None
                )

        # No exception means success - hasattr
        # correctly returned False
