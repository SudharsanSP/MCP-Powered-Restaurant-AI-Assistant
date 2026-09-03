# migrations/create_tables.py
from repositories.schema.coffee_shop_models import Base
from repositories.database import Database


class Migration:
    def __init__(self):
        self.db = Database()

    async def create_tables(self):
        try:
            async with self.db.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
            raise e


if __name__ == "__main__":
    import asyncio

    async def main():
        migration = Migration()
        await migration.create_tables()

    asyncio.run(main())
