"""
Tests for MCP_Client/src/migration/migration.py
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from migration.migration import Migration


class TestClientMigration:
    def test_init(self):
        with patch("migration.migration.Database") as mock_db_cls:
            m = Migration()
            assert m.db is not None
            mock_db_cls.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tables_success(self):
        with patch("migration.migration.Database") as mock_db_cls:
            mock_db = MagicMock()
            mock_conn = AsyncMock()
            mock_conn.run_sync = AsyncMock()

            mock_begin_ctx = AsyncMock()
            mock_begin_ctx.__aenter__.return_value = mock_conn
            mock_begin_ctx.__aexit__.return_value = None
            mock_db.engine.begin.return_value = mock_begin_ctx
            mock_db_cls.return_value = mock_db

            migration = Migration()
            await migration.create_tables()

            mock_db.engine.begin.assert_called_once()
            mock_conn.run_sync.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_tables_raises_on_failure(self):
        with patch("migration.migration.Database") as mock_db_cls:
            mock_db = MagicMock()
            mock_conn = AsyncMock()
            mock_conn.run_sync = AsyncMock(side_effect=RuntimeError("Migration failed"))

            mock_begin_ctx = AsyncMock()
            mock_begin_ctx.__aenter__.return_value = mock_conn
            mock_begin_ctx.__aexit__.return_value = None
            mock_db.engine.begin.return_value = mock_begin_ctx
            mock_db_cls.return_value = mock_db

            migration = Migration()
            with pytest.raises(RuntimeError, match="Migration failed"):
                await migration.create_tables()
