import asyncio
import sys

from fastmcp import FastMCP
from migration.migration import Migration
from settings import config

async def main():
    migration = Migration()
    await migration.create_tables()

    mcp = FastMCP("my_server")
    from routers.router import router

    mcp.mount(router)
    await mcp.run_async(
        transport="streamable-http",
        port=config.port
    )


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(main())