# ☕ CoffeeBotMCP

An AI-powered coffee shop chatbot built with the **Model Context Protocol (MCP)**. Customers chat with **Brew Buddy** — a friendly assistant that can show the menu, take orders, and check order status using natural language.

---

## How It Works

The system is two services that talk to each other:

```
Customer (HTTP) → MCP_Client (FastAPI) → MCP_Server (FastMCP) → PostgreSQL
                        ↑
                 Gemini 3.5-flash
                 LangGraph Agent
```

- **MCP_Client** — the customer-facing API. Handles authentication, manages the AI agent, and serves the chat endpoint.
- **MCP_Server** — exposes coffee-shop business logic (menu, orders) as MCP tools that the AI agent can call.

---

## Features

- 🤖 Conversational AI agent (Brew Buddy) powered by Google Gemini 2.5-flash
- 🔐 JWT authentication with refresh tokens and role-based access control
- 🧠 Persistent conversation memory per session (LangGraph + PostgreSQL checkpointer)
- ✅ Human-in-the-Loop order approval — agent pauses before placing an order and waits for your confirmation
- 📋 Context summarisation — long conversations are summarised automatically to stay within token limits
- 📦 Structured error responses with request ID tracing
- 🗂️ JSON-structured logging across both services

---

## Prerequisites

- Python 3.11+
- PostgreSQL (running and accessible)
- A [Google AI API key](https://aistudio.google.com/app/apikey) for Gemini

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd CoffeeBotMCP
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
```

### 2. Install dependencies

Install for both services (they share the same `.venv`):

```bash
pip install -r MCP_Client/requirements.txt
pip install -r MCP_Server/requirements.txt
```

### 3. Configure environment variables

Copy the sample and fill in your values:

```bash
cp .env.sample .env
```

Open `.env` and set:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
DB_USERNAME=postgres
DB_PASSWORD=your_password

# Server
PORT=8080
HOST=0.0.0.0
LOG_LEVEL=INFO

# Auth
JWT_SECRET=your_strong_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google Gemini
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=gemini-2.5-flash
TEMPERATURE=0.1
MAX_TOKEN=500

# MCP Server URL (used by the client to connect to the server)
MCP_SERVER_URL=http://localhost:8001/mcp
```

### 4. Start the MCP Server

```bash
cd MCP_Server
python src/main.py
```

The server starts on **port 8001**. It creates the database tables on first run.

### 5. Start the MCP Client

Open a new terminal:

```bash
cd MCP_Client
python src/main.py
```

The client starts on **port 8080**. It connects to the MCP server, loads tools, and sets up the AI agent.

---

## API Reference

**Base URL:** `http://localhost:8080`
**Prefix:** `/coffee_shop_bot/api/v1`

### Public Endpoints

| Method   | Path              | Description                                 |
| -------- | ----------------- | ------------------------------------------- |
| `GET`  | `/health/live`  | Liveness check                              |
| `GET`  | `/health/ready` | Readiness check (DB + agent)                |
| `POST` | `/auth/login`   | Login → access token + refresh token       |
| `POST` | `/auth/refresh` | Exchange refresh token for new access token |
| `POST` | `/auth/logout`  | Revoke refresh token                        |
| `POST` | `/user`         | Register a new customer                     |

### Protected Endpoints (Bearer JWT required)

| Method   | Path                               | Description                       |
| -------- | ---------------------------------- | --------------------------------- |
| `POST` | `/chat_bot/{thread_id}`          | Send a message to Brew Buddy      |
| `POST` | `/chat_bot/{thread_id}/approval` | Approve or reject a pending order |

The `thread_id` is any UUID you generate — it represents a conversation session. Use the same UUID across multiple requests to have a continuous conversation.

---

## Usage Examples

### Register

```bash
curl -X POST http://localhost:8080/coffee_shop_bot/api/v1/user \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "phone_number": "9876543210", "email": "alice@example.com", "password": "secret123"}'
```

### Login

```bash
curl -X POST http://localhost:8080/coffee_shop_bot/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "secret123"}'
```

### Chat with Brew Buddy

```bash
curl -X POST http://localhost:8080/coffee_shop_bot/api/v1/chat_bot/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_query": "What is on the menu?"}'
```

### Place an Order (with approval)

1. Ask to order:

```bash
curl -X POST http://localhost:8080/coffee_shop_bot/api/v1/chat_bot/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_query": "I would like 2 espressos"}'
```

The response will contain an approval prompt.

2. Approve the order:

```bash
curl -X POST http://localhost:8080/coffee_shop_bot/api/v1/chat_bot/550e8400-e29b-41d4-a716-446655440000/approval \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"decision": "approve"}'
```

---

## Project Structure

```
CoffeeBotMCP/
├── .env.sample               # Environment variable template
├── README.md                 # This file
├── CODEBASE_ANALYSIS.md      # Detailed analysis, issues, and roadmap
│
├── MCP_Client/               # Customer-facing FastAPI service (port 8080)
│   └── src/
│       ├── main.py           # App entry point
│       ├── agents/           # LangGraph agent + system prompts
│       ├── client/           # Gemini model + MCP client factories
│       ├── middleware/       # Auth (JWT/RBAC) + request context
│       ├── models/           # Pydantic DTOs
│       ├── repositories/     # DB access layer + ORM schema
│       ├── routers/          # HTTP route handlers
│       ├── services/         # Business logic + dependency injection
│       └── utilities/        # Hashing, tokens, logging, exceptions
│
└── MCP_Server/               # MCP tool server (port 8001)
    └── src/
        ├── main.py           # FastMCP entry point
        ├── tools/            # 4 MCP tools (menu, shop, order)
        ├── repositories/     # DB access layer
        └── utilities/        # Logging
```

---

## Database Schema

The shared PostgreSQL database has four tables:

- **`customers`** — registered users with hashed passwords and refresh tokens
- **`items`** — menu items with name and price
- **`orders`** — customer orders with status (`ordered → processing → pending → completed`)
- **`order_items`** — line items linking orders to menu items

Tables are created automatically on first startup.

---

## MCP Tools

The MCP Server exposes four tools to the AI agent:

| Tool                      | Triggered when...                                    |
| ------------------------- | ---------------------------------------------------- |
| `get_menu_tool`         | Customer asks to see the menu                        |
| `get_shop_details_tool` | Customer asks about location or contact info         |
| `place_order_tool`      | Customer wants to place an order (requires approval) |
| `get_order_tool`        | Customer wants to check their order status           |

---
