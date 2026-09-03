from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from settings import config
from utilities.exceptions.custom_exception import Custom_Exception
from utilities.exceptions.error_codes import ErrorCode
from utilities.exceptions.http_status import HttpStatusCode


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        db_url = (
            f"postgresql+psycopg://{config.db_username}:"
            f"{config.db_password}@{config.db_host}:{config.db_port}/"
            f"{config.db_name}"
        )

        self.engine = create_async_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            echo=False,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autoflush=False,
            expire_on_commit=False,
        )
        self._initialized = True

    async def close(self) -> None:
        if self._initialized:
            await self.engine.dispose()
            self._initialized = False

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            yield session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    db = Database()
    async with db.session_factory() as session:
        yield session


async def test_connection():
    db = Database()
    try:
        async with db.engine.begin() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        from utilities.logger import get_logger

        get_logger(__name__).exception("Database connectivity check failed")
        raise Custom_Exception(
            message="The database is unavailable.",
            code=ErrorCode.DB_CONNECTION_FAIL,
            status_code=HttpStatusCode.SERVICE_UNAVAILABLE,
        )

