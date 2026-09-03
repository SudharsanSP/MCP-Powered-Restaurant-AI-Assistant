from __future__ import annotations

import uvicorn

from MCP_Client.src.main import app


def main() -> None:
    uvicorn.run(
        "MCP_Client.src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
