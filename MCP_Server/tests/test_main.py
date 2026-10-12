"""
Tests for MCP_Server/src/main.py
"""
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

if "main" in sys.modules and not hasattr(sys.modules["main"], "main"):
    del sys.modules["main"]

from main import main


class TestServerMain:
    @pytest.mark.asyncio
    async def test_main_successful_startup(self):
        with patch("main.Migration") as mock_migration_cls, \
             patch("main.FastMCP") as mock_fastmcp_cls:
            
            mock_migration = MagicMock()
            mock_migration.create_tables = AsyncMock()
            mock_migration_cls.return_value = mock_migration

            mock_mcp = MagicMock()
            mock_mcp.mount = MagicMock()
            mock_mcp.run_async = AsyncMock()
            mock_fastmcp_cls.return_value = mock_mcp

            await main()

            mock_migration_cls.assert_called_once()
            mock_migration.create_tables.assert_awaited_once()
            mock_fastmcp_cls.assert_called_once_with("my_server")
            mock_mcp.mount.assert_called_once()
            mock_mcp.run_async.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_main_raises_on_migration_failure(self):
        with patch("main.Migration") as mock_migration_cls:
            mock_migration = MagicMock()
            mock_migration.create_tables = AsyncMock(side_effect=RuntimeError("Migration failed"))
            mock_migration_cls.return_value = mock_migration

            with pytest.raises(RuntimeError, match="Migration failed"):
                await main()

    @pytest.mark.asyncio
    async def test_main_raises_on_run_async_failure(self):
        with patch("main.Migration") as mock_migration_cls, \
             patch("main.FastMCP") as mock_fastmcp_cls:
            
            mock_migration = MagicMock()
            mock_migration.create_tables = AsyncMock()
            mock_migration_cls.return_value = mock_migration

            mock_mcp = MagicMock()
            mock_mcp.mount = MagicMock()
            mock_mcp.run_async = AsyncMock(side_effect=RuntimeError("Server failed to run"))
            mock_fastmcp_cls.return_value = mock_mcp

            with pytest.raises(RuntimeError, match="Server failed to run"):
                await main()
