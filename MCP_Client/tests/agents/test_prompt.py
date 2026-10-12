"""
Tests for MCP_Client/src/agents/prompt.py

Class under test: Prompt

Both methods return a multi-line string — we verify they are non-empty and
contain key structural markers so regressions in the prompt text are caught.
"""
import sys
import os

CLIENT_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "..", "MCP_Client", "src")
if CLIENT_SRC not in sys.path:
    sys.path.insert(0, CLIENT_SRC)

import pytest
from agents.prompt import Prompt


class TestGetSystemPrompt:
    def test_returns_non_empty_string(self):
        p = Prompt()
        prompt = p.get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt.strip()) > 0

    def test_contains_role_section(self):
        """Prompt must have a <role> block describing Brew Buddy."""
        p = Prompt()
        assert "<role>" in p.get_system_prompt()
        assert "Brew Buddy" in p.get_system_prompt()

    def test_contains_instructions_section(self):
        p = Prompt()
        assert "<instructions>" in p.get_system_prompt()

    def test_contains_critical_section(self):
        p = Prompt()
        assert "<critical>" in p.get_system_prompt()

    def test_mentions_order_tools(self):
        """Key tool names referenced in the instructions must be present."""
        prompt = Prompt().get_system_prompt()
        assert "cancel_order_tool" in prompt
        assert "update_order_tool" in prompt
        assert "get_order_tool" in prompt

    def test_stable_across_multiple_calls(self):
        """Prompt must be deterministic — same result on every call."""
        p = Prompt()
        assert p.get_system_prompt() == p.get_system_prompt()


class TestSummarySystemPrompt:
    def test_returns_non_empty_string(self):
        p = Prompt()
        prompt = p.summary_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt.strip()) > 0

    def test_contains_role_section(self):
        p = Prompt()
        assert "<role>" in p.summary_system_prompt()

    def test_contains_instructions_section(self):
        p = Prompt()
        assert "<instructions>" in p.summary_system_prompt()

    def test_different_from_main_prompt(self):
        """Summary prompt is a separate, different string from the main prompt."""
        p = Prompt()
        assert p.get_system_prompt() != p.summary_system_prompt()

    def test_stable_across_multiple_calls(self):
        p = Prompt()
        assert p.summary_system_prompt() == p.summary_system_prompt()
