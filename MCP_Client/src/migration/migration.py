# migrations/create_tables.py
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
            logger.info("Database table migration completed successfully")
        except Exception as e:
            logger.exception("Database table migration failed: %s", e)
            raise e


if __name__ == "__main__":
    import asyncio

    async def main():
        migration = Migration()
        await migration.create_tables()

    asyncio.run(main())
