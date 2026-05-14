---
name: architecture
description: >
  Build and extend features using Hexagonal Architecture in a FastAPI middleware
  that receives Zabbix alerts and routes them to ITSM platforms.
  Enforces strict layer separation, dependency inversion, and port/adapter patterns.
when_to_use:
  - Creating new business features
  - Adding external integrations
  - Refactoring infrastructure logic
  - Deciding where a new class or module belongs	
allowed-tools:
  - filesystem
  - terminal
---

# Hexagonal Architecture

## Objective

Implement every feature following strict Hexagonal Architecture principles. 
The goal is to keep domain logic completely independent of frameworks, databases, and external services — making every integration replaceable.

---

## Layer Map

```text
src/
├── domain/           # Entities, value objects, ports, domain exceptions
├── application/      # Use cases, DTOs, orchestration
├── infrastructure/   # DB repositories, HTTP adapters, external service clients
├── api/              # FastAPI routers, schemas, dependency wiring
└── main.py           # FastAPI app entry point
```

---

## Layer Responsibilities

### `domain/`

The core of the application. Must be framework-free.

Contains:
- Entities (core business objects)
- Value objects (immutable descriptors)
- Domain exceptions
- Repository port interfaces
- External service port interfaces
- Business rules and invariants

**MUST NOT import:**
- `fastapi`
- `sqlalchemy`
- `httpx`
- Any infrastructure or API module

### `application/`

Orchestrates domain operations. Contains use cases that coordinate ports.

Contains:
- Use cases (one class per business operation)
- Input/output DTOs
- Orchestration logic (coordinate ports, enforce flow)

**MUST depend only on domain abstractions (ports), never on concrete adapters.**

### `infrastructure/`

Implements domain ports with concrete technology.

Contains:
- SQLAlchemy ORM models and async repositories
- HTTP client adapters (external APIs, third-party services)
- External service clients and their factories
- Payload mappers (external format <-> domain model)

**Rules:**
- ORM models stay inside `infrastructure/db/` — never exposed outside
- Repositories return domain entities or DTOs, not ORM rows
- Each external integration lives in its own sub-package

### `api/`

FastAPI entry-point adapter. Must remain thin.

Contains:
- Routers
- Pydantic V2 request/response schemas
- Dependency injection wiring (`dependencies.py`)
- Exception handlers (maps domain exceptions → HTTP responses)

**MUST NOT contain business logic.**

---

## Dependency Direction

```
api          →  application  →  domain
infrastructure               →  domain
```

**Never invert this flow.** Domain must not know about FastAPI, SQLAlchemy, or httpx.

---

## Port / Adapter Pattern

Every external system is hidden behind a domain port.

```python
# src/domain/ports/example_service_port.py
from typing import Protocol
from src.domain.models.example import DomainEntity, DomainResult


class ExampleServicePort(Protocol):
    async def perform_action(self, entity: DomainEntity) -> DomainResult: ...
```

```python
# src/domain/ports/example_repository_port.py
from typing import Protocol
from src.domain.models.example import DomainEntity


class ExampleRepositoryPort(Protocol):
    async def save(self, entity: DomainEntity) -> None: ...
    async def find_by_id(self, entity_id: str) -> DomainEntity | None: ...
```

Concrete adapters live in `infrastructure/` and implement these protocols.

---

## Recommended Full Structure

```text
src/
├── main.py                          # Entrypoint de FastAPI
│
├── core/                            # Core utilities, base classes, shared logic
│   ├── config.py                    # Settings (Pydantic BaseSettings)
│   ├── logger.py                    # Inicialización de logger (structlog/loguru/standard)
│   └── authorization.py             # utilidades de auth (JWT, password hashing)
│
├── domain/
│   ├── models/
│   │   └── <your_entity>.py         # e.g. order.py, user.py, incident.py
│   ├── value_objects/
│   │   └── <your_value_object>.py   # e.g. status.py, currency.py
│   ├── ports/
│   │   ├── <repo>_port.py           # e.g. order_repository_port.py
│   │   └── <service>_port.py        # e.g. payment_port.py
│   └── exceptions.py
│
├── application/
│   └── use_cases/
│       └── <action>.py              # e.g. create_order.py, cancel_order.py
│
├── infrastructure/
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   ├── models/
│   │   │   └── <entity>_orm.py      # e.g. order_orm.py
│   │   └── repositories/
│   │       └── <entity>_repository.py
│   └── integrations/
│       └── <provider>/
│           ├── adapter.py
│           └── mapper.py
│
└── api/
    ├── dependencies.py
    ├── exception_handlers.py
    ├── schemas/
    │   └── <resource>.py            # e.g. order.py → OrderCreate, OrderResponse
    └── routers/
        └── <resource>.py            # e.g. orders.py, health.py
```

---

## Rules

- Never place business logic in routers.
- Never access the database directly from routers.
- Never import infrastructure into domain.
- Domain entities are plain Pydantic models — no ORM decorators.
- ORM models are separate from domain entities; repositories do the mapping.
- Use constructor injection in use cases and adapters.
- Keep each ITSM integration isolated in its own sub-package.
- Prefer `Protocol` over `ABC` for ports — duck typing keeps domain lighter.