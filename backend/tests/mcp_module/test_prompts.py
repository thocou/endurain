"""Tests for mcp_module.prompts module."""

from unittest.mock import patch, MagicMock

import pytest

from mcp_module.prompts import (
    analyze_training,
    weekly_summary,
    gear_check,
)


MODULE = "mcp_module.prompts"


class TestAnalyzeTraining:
    """Tests for the analyze_training prompt."""

    def test_returns_messages_with_period(self):
        """
        Prompt returns messages containing the
        specified period.
        """
        result = analyze_training(
            period="last_7_days"
        )
        assert isinstance(result, list)
        assert len(result) == 1
        msg = result[0]
        assert msg["role"] == "user"
        assert "last_7_days" in msg["content"]

    def test_default_period(self):
        """
        Prompt uses last_30_days when no period
        is specified.
        """
        result = analyze_training()
        assert isinstance(result, list)
        assert len(result) == 1
        msg = result[0]
        assert "last_30_days" in msg["content"]

    def test_contains_analysis_instructions(self):
        """
        Prompt includes key analysis sections.
        """
        result = analyze_training()
        content = result[0]["content"]
        assert "list_activities" in content
        assert "Training volume" in content
        assert "Recovery indicators" in content
        assert "Recommendations" in content


class TestWeeklySummary:
    """Tests for the weekly_summary prompt."""

    def test_returns_messages(self):
        """
        Prompt returns a list with one user message.
        """
        result = weekly_summary()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"

    def test_contains_summary_instructions(self):
        """
        Prompt includes key summary sections.
        """
        content = weekly_summary()[0]["content"]
        assert "weekly" in content.lower()
        assert "list_activities" in content
        assert "Health trends" in content
        assert "Goal progress" in content
        assert "next week" in content


class TestGearCheck:
    """Tests for the gear_check prompt."""

    def test_returns_messages(self):
        """
        Prompt returns a list with one user message.
        """
        result = gear_check()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"

    def test_contains_gear_instructions(self):
        """
        Prompt includes key gear assessment sections.
        """
        content = gear_check()[0]["content"]
        assert "list_gear" in content
        assert "replacement" in content.lower()
        assert "Maintenance" in content
        assert "rotation" in content.lower()


class TestPromptsRegistered:
    """Tests that all prompts are registered."""

    def test_all_prompts_registered(self):
        """
        All 3 prompts are registered on the MCP
        server.
        """
        from mcp_module.server import mcp_server

        manager = mcp_server._prompt_manager
        prompts = manager._prompts
        names = set(prompts.keys())
        assert "analyze_training" in names
        assert "weekly_summary" in names
        assert "gear_check" in names
