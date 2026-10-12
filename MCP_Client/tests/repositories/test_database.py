"""
Tests for MCP_Client/src/repositories/database.py
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from repositories.database import Database, get_db_session, test_connection as check_test_connection
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode


class TestClientDatabase:
    def test_database_singleton(self):
        with patch("repositories.database.create_async_engine"), \
             patch("repositories.database.async_sessionmaker"):
            Database._instance = None
            db1 = Database()
            db2 = Database()
            assert db1 is db2

    @pytest.mark.asyncio
    async def test_close(self):
        with patch("repositories.database.create_async_engine") as mock_engine, \
             patch("repositories.database.async_sessionmaker"):
            mock_eng_inst = AsyncMock()
            mock_eng_inst.dispose = AsyncMock()
            mock_engine.return_value = mock_eng_inst

            Database._instance = None
            db = Database()
            await db.close()

            mock_eng_inst.dispose.assert_awaited_once()
            assert db._initialized is False

    @pytest.mark.asyncio
    async def test_get_session(self):
        with patch("repositories.database.create_async_engine"), \
             patch("repositories.database.async_sessionmaker") as mock_maker:
            mock_session = AsyncMock()
            mock_session_ctx = AsyncMock()
            mock_session_ctx.__aenter__.return_value = mock_session
            mock_session_ctx.__aexit__.return_value = None
            mock_maker.return_value = MagicMock(return_value=mock_session_ctx)

            Database._instance = None
            db = Database()
            sessions = []
            async for s in db.get_session():
                sessions.append(s)

            assert len(sessions) == 1
            assert sessions[0] == mock_session

    @pytest.mark.asyncio
    async def test_get_db_session(self):
        with patch("repositories.database.Database") as mock_db_cls:
            mock_session = AsyncMock()
            mock_session_ctx = AsyncMock()
            mock_session_ctx.__aenter__.return_value = mock_session
            mock_session_ctx.__aexit__.return_value = None

            mock_db = MagicMock()
            mock_db.session_factory.return_value = mock_session_ctx
            mock_db_cls.return_value = mock_db

            collected = []
            async for sess in get_db_session():
                collected.append(sess)

            assert len(collected) == 1
            assert collected[0] == mock_session

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        with patch("repositories.database.Database") as mock_db_cls:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_conn_ctx = AsyncMock()
            mock_conn_ctx.__aenter__.return_value = mock_conn
            mock_conn_ctx.__aexit__.return_value = None

            mock_db = MagicMock()
            mock_db.engine.begin.return_value = mock_conn_ctx
            mock_db_cls.return_value = mock_db

            res = await check_test_connection()
            assert res is True
            mock_conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        with patch("repositories.database.Database") as mock_db_cls:
            mock_conn_ctx = AsyncMock()
            mock_conn_ctx.__aenter__.side_effect = RuntimeError("DB connection error")

            mock_db = MagicMock()
            mock_db.engine.begin.return_value = mock_conn_ctx
            mock_db_cls.return_value = mock_db

            with pytest.raises(Custom_Exception) as exc_info:
                await check_test_connection()

            assert exc_info.value.code == ErrorCode.DB_CONNECTION_FAIL
            assert exc_info.value.status_code == HttpStatusCode.SERVICE_UNAVAILABLE
