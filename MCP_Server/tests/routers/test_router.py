"""
Tests for MCP_Server/src/routers/router.py
"""
import pytest
from fastmcp import FastMCP
from routers.router import router


class TestServerRouter:
    def test_router_is_fastmcp_instance(self):
        assert isinstance(router, FastMCP)

    def test_router_name(self):
        assert router.name == "router"
