"""Tests for MCP_ENABLED config in core.config."""

from unittest.mock import patch

import pytest


class TestMcpEnabledConfig:
    """Tests for MCP_ENABLED configuration."""

    @patch.dict(
        "os.environ", {"MCP_ENABLED": "true"}
    )
    def test_mcp_enabled_true(self):
        """Test MCP_ENABLED is True when 'true'."""
        import importlib
        import core.config as core_config

        importlib.reload(core_config)
        assert core_config.MCP_ENABLED is True

    @patch.dict(
        "os.environ", {"MCP_ENABLED": "false"}
    )
    def test_mcp_enabled_false(self):
        """Test MCP_ENABLED is False when 'false'."""
        import importlib
        import core.config as core_config

        importlib.reload(core_config)
        assert core_config.MCP_ENABLED is False

    @patch.dict(
        "os.environ", {"MCP_ENABLED": "True"}
    )
    def test_mcp_enabled_case_insensitive(self):
        """Test MCP_ENABLED is case insensitive."""
        import importlib
        import core.config as core_config

        importlib.reload(core_config)
        assert core_config.MCP_ENABLED is True

    @patch.dict(
        "os.environ", {}, clear=False
    )
    def test_mcp_enabled_default(self):
        """Test MCP_ENABLED defaults to True."""
        import importlib
        import os
        import core.config as core_config

        os.environ.pop("MCP_ENABLED", None)
        importlib.reload(core_config)
        assert core_config.MCP_ENABLED is True
