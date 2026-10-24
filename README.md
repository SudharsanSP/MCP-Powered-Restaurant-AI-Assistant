# CoffeeBotMCP

An AI-powered coffee-shop assistant built with the **Model Context Protocol (MCP)**. Customers chat with Brew Buddy to learn about the menu and shop, place or manage orders, and check order details.

## Architecture

```text
Customer --HTTP--> MCP_Client (FastAPI) --Streamable HTTP/MCP--> MCP_Server (FastMCP)
                         |                                          |
                    Gemini + LangGraph ------------------------ PostgreSQL
                         |
                    PostgreSQL checkpointer
```

- **MCP_Client** provides the customer-facing API, customer/admin authentication, and LangGraph conversation agent.
- **MCP_Server** publishes menu, shop, and order operations as MCP tools.
- Both services use the same PostgreSQL database. The client also uses PostgreSQL to persist LangGraph conversation state.

## Features

- Gemini-powered conversational assistant, with model, temperature, and token limit configurable by environment.
- Customer and administrator login, JWT access tokens, customer refresh tokens, refresh-token revocation, and database-backed active-identity/role checks.
- Persistent chat history per UUID thread using a PostgreSQL LangGraph checkpointer.
- Human-in-the-loop confirmation for order placement, update, and cancellation; customers can approve or reject a paused action.
- Automatic conversation summarization for longer chats.
- MCP tools for menu/shop information, order placement, order history/details, update, and cancellation.
- Authenticated administration API for viewing orders, advancing order status, and managing menu items.
- Structured API responses, request IDs, validation error responses, and JSON logging.

## Requirements

- Python **3.14 or newer** (per `pyproject.toml`).
- PostgreSQL accessible to the client and server.
- [uv](https://docs.astral.sh/uv/) to install the root project and development dependencies.
- A [Google AI API key](https://aistudio.google.com/app/apikey).

## Setup

### Install dependencies

From the repository root:

```powershell
uv sync --group dev
```

### Configure environment

Copy `.env.sample` to `.env` and set at least the database connection values, `GOOGLE_API_KEY`, `JWT_SECRET`, and `MCP_SERVER_URL`.

```powershell
copy .env.sample .env
```

The client reads `PORT` (default `8080`) and `MCP_SERVER_URL`. The MCP server reads `MCP_PORT` (default `8081`). For local development, set:

```env
MCP_SERVER_URL=http://localhost:8081/mcp
MCP_PORT=8081
```

Other supported configuration includes `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`, `HOST`, `LOG_LEVEL`, `GOOGLE_API_KEY`, `GEMINI_MODEL`, `TEMPERATURE`, `MAX_TOKEN`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and `REFRESH_TOKEN_EXPIRE_DAYS`. Defaults are defined in the client/server settings modules; `DB_NAME`, database password, Google API key, and MCP server URL should be configured explicitly.

### Start the MCP Server

From the repository root:

```powershell
cd MCP_Server
..\.venv\Scripts\python.exe src\main.py
```

The server creates its database tables at startup and runs FastMCP over Streamable HTTP on `MCP_PORT` (default `8081`).

### Start the MCP Client

Open a second terminal from the repository root:

```powershell
uv run --project . --directory MCP_Client python src\main.py
```

The FastAPI client listens on `PORT` (default `8080`). At startup it initializes the chat and summary Gemini models, connects to the MCP server and loads tools, initializes the PostgreSQL checkpointer, and creates the LangGraph agent. Startup depends on these services being configured and available.

### Build and run the MCP Client with Docker

Docker packages the client and its Python dependencies into an image. The image contains **only the client**; PostgreSQL and the MCP server must be running separately and reachable from the container.

1. Start Docker Desktop and wait until its engine is running.
2. From the repository root, create `.env` from `.env.sample` if you have not already, and set the database credentials, `GOOGLE_API_KEY`, `JWT_SECRET`, and `MCP_SERVER_URL`.
3. When PostgreSQL and the MCP server are running directly on your Windows host, set their host to `host.docker.internal` in `.env`, for example:

   ```env
   DB_HOST=host.docker.internal
   MCP_SERVER_URL=http://host.docker.internal:8081/mcp
   HOST=0.0.0.0
   PORT=8080
   ```

   If those services are in Docker containers instead, put them on the same Docker network as this client and use their container/service names as the host.
4. Build the image from the repository root:

   ```powershell
   docker build -t coffeebot-client .
   ```

5. Run the client:

   ```powershell
   docker run --rm --name coffeebot-client -p 8080:8080 --env-file .env coffeebot-client
   ```

   The client is then available at `http://localhost:8080`. Press `Ctrl+C` to stop it. `-p 8080:8080` forwards port 8080 from your computer to the container, while `--env-file .env` passes configuration at runtime without copying secrets into the image.

## HTTP API

**Base URL:** `http://localhost:8080`
**API prefix:** `/coffee_shop_bot/api/v1`

Health checks, customer registration, customer/admin login, and token refresh are public. All other routes, including logout, require an access token:

```http
Authorization: Bearer <access-token>
```

The authentication middleware verifies the JWT signature/expiry and checks the active customer or user record and its role against the token. Customer identity for chat/order tools is obtained from the verified token. Authentication confirms identity and role consistency; it does not currently enforce separate role permissions per route.

### Health and public routes

| Method   | Path                                            | Description                                                                                         |
| -------- | ----------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `GET`  | `/health/live`                                | Liveness check.                                                                                     |
| `GET`  | `/health/ready`                               | Checks PostgreSQL connectivity and whether client dependencies are initialized.                     |
| `POST` | `/coffee_shop_bot/api/v1/user`                | Register a customer; returns customer UUID, access token, refresh token, and access-token lifetime. |
| `POST` | `/coffee_shop_bot/api/v1/auth/customer/login` | Customer login; returns access and refresh tokens.                                                  |
| `POST` | `/coffee_shop_bot/api/v1/auth/admin/login`    | Administrator login; returns an access token.                                                       |
| `POST` | `/coffee_shop_bot/api/v1/auth/refresh`        | Exchange a customer refresh token for a new access token.                                           |
| `POST` | `/coffee_shop_bot/api/v1/auth/logout`         | Revoke a customer's refresh token.                                                                  |

Customer login body:

```json
{"email": "alice@example.com", "password": "secret123"}
```

Customer registration additionally requires `name` and a 10-digit `phone_number`. Passwords must contain 8–128 characters. Refresh and logout bodies use `{"refresh_token": "..."}`.

### Customer chat routes

| Method   | Path                                                      | Description                                                                                     |
| -------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `POST` | `/coffee_shop_bot/api/v1/chat_bot/{thread_id}`          | Send a chat message.`thread_id` must be a UUID. Reuse the UUID to continue that conversation. |
| `POST` | `/coffee_shop_bot/api/v1/chat_bot/{thread_id}/approval` | Resume a paused order action with an approval or rejection.                                     |

Chat body:

```json
{"user_query": "What is on the menu?"}
```

`user_query` must contain 1–1000 characters. For an order confirmation, send `{"decision": "approve"}` or `{"decision": "reject"}` to the approval route using the same thread ID.

### Administration routes

| Method     | Path                                                       | Description                                                                                              |
| ---------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `GET`    | `/coffee_shop_bot/api/v1/admin/orders`                   | List orders with customer and item details.                                                              |
| `PATCH`  | `/coffee_shop_bot/api/v1/admin/orders/{order_id}/status` | Advance an order from`ordered` to `processing`, then to `completed`. The path ID is an order UUID. |
| `POST`   | `/coffee_shop_bot/api/v1/admin/items`                    | Create a menu item. Name must be non-empty; price must be greater than zero.                             |
| `PATCH`  | `/coffee_shop_bot/api/v1/admin/items/{item_id}`          | Update an item's name, price, and/or active state. The path ID is an item UUID.                          |
| `DELETE` | `/coffee_shop_bot/api/v1/admin/items/{item_id}`          | Deactivate a menu item. The path ID is an item UUID.                                                     |

Admin login issues an access token; these routes require a valid access token. Item create/update request bodies use `name` and `price`; update also accepts `is_active`.

### API responses

Successful routes return an envelope containing `data`, `errors`, `status_code`, `request_id`, and `message`. Request validation errors use HTTP 422. Responses include the request ID in the body and `X-Request-ID` header.

## MCP tools

The MCP server exposes the following six tools to the client agent:

| Tool                      | Purpose                                                                                    |
| ------------------------- | ------------------------------------------------------------------------------------------ |
| `get_menu_tool`         | Return active menu items with integer item IDs and prices.                                 |
| `get_shop_details_tool` | Return shop information from the server's`data/shop_details.txt` file, if present.       |
| `place_order_tool`      | Place an order containing one or more menu items after customer confirmation.              |
| `get_order_tool`        | Return the customer's five most recent orders, or full details for a specified order.      |
| `update_order_tool`     | Replace an order's items and recalculate its total. Only`ordered` orders may be updated. |
| `cancel_order_tool`     | Cancel an order. Only`ordered` orders may be cancelled.                                  |

The order tools use the authenticated customer's UUID. The integer `order_id`/`item_id` values accepted by MCP order tools are database IDs; the admin HTTP routes use UUIDs for their order/item path parameters.

## Database

Both services use the same PostgreSQL database. The schema contains:

- `customers` — registered customer identity, password hash, and refresh-token state.
- `users` — administrator identity and password hash.
- `items` — menu items, price, and active state.
- `orders` — customer orders and their status (`ordered`, `processing`, `pending`, or `completed`).
- `order_items` — order/menu item relationships, quantities, and active state.

The server runs table creation at startup. The admin status endpoint advances `ordered → processing → completed`; `pending` is an enum value but is not part of that endpoint's transition sequence.

## Tests and coverage

Run the client and server suites in separate processes because both packages use top-level Python module names such as `routers` and `repositories`. From the repository root, these commands require at least 90% coverage for each service independently:

```powershell
.venv\Scripts\python.exe -m pytest -q MCP_Client\tests --cov=MCP_Client\src --cov-report=term-missing --cov-fail-under=90
.venv\Scripts\python.exe -m pytest -q MCP_Server\tests --cov=MCP_Server\src --cov-report=term-missing --cov-fail-under=90
```

## Project structure

```text
CoffeeBotMCP/
├── MCP_Client/
│   ├── src/
│   │   ├── agents/       # LangGraph agent and prompts
│   │   ├── client/       # Gemini, MCP client, and checkpointer factories
│   │   ├── middleware/   # Request context and JWT/RBAC checks
│   │   ├── models/       # API request/response models
│   │   ├── repositories/ # Database access and ORM schema
│   │   ├── routers/      # FastAPI routes
│   │   ├── services/     # Application services and dependencies
│   │   └── utilities/    # Tokens, hashing, logging, and exceptions
│   └── tests/
├── MCP_Server/
│   ├── src/
│   │   ├── tools/        # FastMCP tools
│   │   ├── repositories/ # Database access and ORM schema
│   │   └── migration/    # Startup table creation
│   └── tests/
├── .env.sample
├── pyproject.toml
└── README.md
```
