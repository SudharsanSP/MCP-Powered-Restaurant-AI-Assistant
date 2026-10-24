FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY MCP_Client/src ./MCP_Client/src

EXPOSE 8080

CMD ["uv", "run", "--project", "/app", "--no-sync", "--directory", "/app/MCP_Client", "python", "src/main.py"]