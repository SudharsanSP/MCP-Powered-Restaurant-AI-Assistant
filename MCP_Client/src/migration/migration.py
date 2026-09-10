# migrations/create_tables.py
from sqlalchemy import text

from repositories.schema.coffee_shop_models import Base
from repositories.database import Database
from utilities.logger import get_logger

logger = get_logger(__name__)


class Migration:
    def __init__(self):
        self.db = Database()

    async def create_tables(self):
        logger.info("Starting database table migration")
        try:
            async with self.db.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                await conn.execute(text(
                    "ALTER TABLE customers "
                    "ADD COLUMN IF NOT EXISTS password_hash VARCHAR(128) NOT NULL DEFAULT ''"
                ))
                await conn.execute(text(
                    "ALTER TABLE customers "
                    "ADD COLUMN IF NOT EXISTS role VARCHAR(32) NOT NULL DEFAULT 'user'"
                ))
            logger.info("Database table migration completed successfully")
        except Exception:
            logger.exception("Database table migration failed")
            raise


if __name__ == "__main__":
    import asyncio

    async def main():
        migration = Migration()
        await migration.create_tables()

    asyncio.run(main())
