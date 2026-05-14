---
name: fast-api
description: >
  FastAPI best practices for building clean, maintainable endpoints in a Zabbix-to-ITSM
  middleware using Hexagonal Architecture. Covers Pydantic V2 schemas, dependency injection,
  router organization, async path operations, return types, and error handling.
  Use when creating API endpoints, webhooks, or health checks.
when_to_use:
  - Creating API endpoints
  - Adding Zabbix webhook handlers
  - Creating health checks or metrics endpoints
  - Wiring use cases via dependency injection
allowed-tools:
  - filesystem
  - terminal
---

# FastAPI API Development

## Objective

Create maintainable, thin FastAPI endpoints that delegate all business logic to use cases.
Routers are entry-point adapters — they validate input, inject dependencies, and return typed responses.

---

## Important

Reference implementations only.

Reuse existing adapters, engines, session factories, and dependency injection
mechanisms whenever already implemented in the project.

Do NOT replace existing database infrastructure unless explicitly requested.

---

## Run the App

Development server with auto-reload:

```bash
fastapi dev
```

Production server:

```bash
fastapi run
```

Always declare the entrypoint in `pyproject.toml` so the FastAPI CLI can find the app:

```toml
[tool.fastapi]
entrypoint = "src.main:app"
```

When the above is not possible, pass the path explicitly:

```bash
fastapi dev src/main.py
```

---

## Stack

- FastAPI (standard install)
- Pydantic V2
- `async`/`await` throughout
- `APIRouter` for all route groups
- `Depends()` with `Annotated` for dependency injection

---

## App Factory

Use `lifespan` to manage startup and shutdown of shared resources: database engine,
HTTP clients, scheduled tasks, and connection pools.
Never initialize these resources at module level or inside individual request dependencies.

Reference only — do not replace existing adapters if already implemented.

```python
# src/main.py
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI
from src.infrastructure.db.session import engine
from src.infrastructure.db.base import Base
from src.infrastructure.http.client import build_httpx_client
from src.api.routers import items, health    # replace with your routers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ── Startup ────────────────────────────────────────────────
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.state.http_client = build_httpx_client()

    # optional: start background tasks here
    # app.state.task = asyncio.create_task(some_periodic_task())

    yield   # application runs here

    # ── Shutdown ───────────────────────────────────────────────
    await app.state.http_client.aclose()
    await engine.dispose()
    # app.state.task.cancel()

app = FastAPI(
    title="My Application",
    description="Short description of what this API does.",
    version="1.0.0",
    lifespan=lifespan,        # ← always pass lifespan here, never use @app.on_event
)

app.include_router(items.router)
app.include_router(health.router)
```

**Rules:**
- Always use `lifespan` — never use deprecated `@app.on_event("startup")` / `@app.on_event("shutdown")`.
- Store every shared resource in `app.state` — accessible via `request.app.state` in dependencies.
- The `lifespan` function must `yield` exactly once.
- Always dispose of resources in the shutdown block (after `yield`).

---

## Router Rules

### Declare prefix and tags on the router — not on `include_router()`

```python
# src/api/routers/items.py
from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["items"])
```

```python
# src/main.py  ← include without repeating prefix/tags
app.include_router(items.router)
```

**Do NOT do this:**

```python
# DO NOT DO THIS
app.include_router(router, prefix="/items", tags=["items"])
```

### Apply shared dependencies at the router level

```python
app.include_router(
    admin_router,
    dependencies=[Depends(require_admin_token)],
)
```

### One HTTP operation per function

```python
@router.get("/")
async def list_items() -> list[ItemResponse]: ...

@router.post("/")
async def create_item(body: ItemCreate) -> ItemResponse: ...

@router.get("/{item_id}")
async def get_item(item_id: Annotated[int, Path(ge=1)]) -> ItemResponse: ...
```

**Do NOT mix methods in one function:**

```python
# DO NOT DO THIS
@router.api_route("/items/", methods=["GET", "POST"])
async def handle_items(request: Request): ...
```

---

## Always Use `Annotated`

Use `Annotated` for every parameter declaration: `Path`, `Query`, `Header`, `Body`, and
`Depends`. Create named type aliases for reusable dependencies.

```python
# src/api/dependencies.py
from typing import Annotated
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.db.session import get_db_session
import httpx


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client

HTTPClientDep = Annotated[httpx.AsyncClient, Depends(get_http_client)]
```

```python
# src/api/routers/items.py
from typing import Annotated
from fastapi import APIRouter, Path, Query
from src.api.dependencies import DBSessionDep, HTTPClientDep
from src.api.schemas.item import ItemCreate, ItemResponse

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/")
async def list_items(
    db: DBSessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ItemResponse]:
    ...


@router.get("/{item_id}")
async def get_item(
    item_id: Annotated[int, Path(ge=1)],
    db: DBSessionDep,
) -> ItemResponse:
    ...
```

---

## Return Types — Always Declare Them

Return types drive Pydantic serialization (Rust-side), response validation, and OpenAPI schema.

```python
@router.post("/")
async def create_item(body: ItemCreate) -> ItemResponse:
    ...
```

Use `response_model=` only when the return type differs from the serialized shape
(e.g., filtering sensitive internal fields):

```python
from typing import Any

@router.get("/{item_id}", response_model=ItemPublicResponse)
async def get_item(item_id: Annotated[int, Path(ge=1)]) -> Any:
    # returns InternalItem; response_model strips sensitive fields
    ...
```

**Do NOT use `ORJSONResponse` or `UJSONResponse`** — they are deprecated.
Declared return types + Pydantic handle serialization.

---

## Do Not Use Ellipsis (`...`) as Default

```python
# CORRECT
class ItemCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
```

```python
# DO NOT DO THIS
class ItemCreate(BaseModel):
    name: str = ...
    price: float = ...
```

---

## Pydantic V2 Schemas

All request/response schemas live in `src/api/schemas/`.
Use `model_config` (not inner `class Config`). Use `field_validator` / `model_validator`
with `@classmethod`. Do **not** use `RootModel`.

```python
# src/api/schemas/item.py
from pydantic import BaseModel, Field, field_validator
from typing import Annotated


class ItemCreate(BaseModel):
    model_config = {"str_strip_whitespace": True}

    name: Annotated[str, Field(min_length=1, max_length=255)]
    description: str | None = None
    price: Annotated[float, Field(gt=0)]
    tags: list[str] = []

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v


class ItemResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float
    tags: list[str]
```

### Do NOT use `RootModel`

Use plain type annotations with `Annotated` instead:

```python
# CORRECT
from fastapi import Body

@router.post("/batch")
async def batch_create(
    items: Annotated[list[ItemCreate], Field(min_length=1), Body()]
) -> list[ItemResponse]:
    ...
```

```python
# DO NOT DO THIS
from pydantic import RootModel, Field
class ItemList(RootModel[Annotated[list[ItemCreate], Field(min_length=1)]]):
    pass
```

---

## Dependency Injection Patterns

### Class Dependencies — Use Factory Functions

Avoid using classes directly as `Depends()` targets. Use a factory function that returns the instance.

```python
# src/application/use_cases/create_item.py
class CreateItemUseCase:
    def __init__(self, repo: ItemRepositoryPort) -> None:
        self.repo = repo

    async def execute(self, data: ItemCreate) -> ItemResponse:
        ...


def get_create_item_use_case(db: DBSessionDep) -> CreateItemUseCase:
    from src.infrastructure.db.repositories.item_repository import ItemRepository
    return CreateItemUseCase(repo=ItemRepository(db))

CreateItemUseCaseDep = Annotated[CreateItemUseCase, Depends(get_create_item_use_case)]
```

```python
# DO NOT DO THIS
@router.post("/")
async def create(use_case: Annotated[CreateItemUseCase, Depends()]):
    ...
```

### `yield` Dependencies — Scope

Use the default `"request"` scope for cleanup after the response is sent:

```python
async def get_db_session():
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()
```

Use `scope="function"` when cleanup must run **before** the response is sent:

```python
def get_audit_context():
    ctx = AuditContext()
    try:
        yield ctx
    finally:
        ctx.flush()     # runs before response is sent

AuditContextDep = Annotated[AuditContext, Depends(get_audit_context, scope="function")]
```

---

## Async vs Sync Path Operations

Use `async def` only when all called code is fully awaitable.
Use plain `def` when calling blocking/sync code — FastAPI runs it in a threadpool automatically.

```python
# async: awaiting DB and/or HTTP
@router.post("/")
async def create_item(body: ItemCreate, use_case: CreateItemUseCaseDep) -> ItemResponse:
    return await use_case.execute(body)


# sync: no I/O — runs in threadpool, correct
@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

**Never call blocking code inside `async def`** — it blocks the event loop.
When a third-party SDK is synchronous, wrap it with `asyncer.asyncify()`:

```python
from asyncer import asyncify

async def call_blocking_sdk(data: dict) -> dict:
    return await asyncify(some_sdk.do_work)(data)
```

---

## Error Handling

Centralize exception mapping. Never raise `HTTPException` inside use cases or domain logic —
raise domain exceptions and map them at the API layer.

```python
# src/api/exception_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from src.domain.exceptions import DuplicateAlertError, ITSMProviderError


async def duplicate_alert_handler(request: Request, exc: DuplicateAlertError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


async def itsm_provider_handler(request: Request, exc: ITSMProviderError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


# src/api/main.py
app.add_exception_handler(DuplicateAlertError, duplicate_alert_handler)
app.add_exception_handler(ITSMProviderError, itsm_provider_handler)
```

---

## Response Rules

- Always use response schemas — never expose ORM models or internal entities directly.
- Use consistent error structures across all endpoints.
- Never include sensitive fields (tokens, passwords, internal keys) in responses.
- Never use `ORJSONResponse` or `UJSONResponse`.
- Dispose of every resource in the shutdown block (after `yield`), even if startup raised an error.
- Do NOT create `AsyncSession` or `httpx.AsyncClient` instances inside `lifespan` —
  only the engine and the shared client belong here; sessions are created per-request in dependencies.