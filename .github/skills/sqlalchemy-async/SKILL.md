---
name: sqlalchemy-async
description: >
  Implement async persistence using SQLAlchemy 2.x with the repository pattern.
  Covers engine setup, lifespan integration, session management, ORM model definition,
  domain entity mapping, and Alembic migrations. Supports PostgreSQL and MySQL.
when_to_use:
  - Creating or modifying repositories
  - Adding ORM models
  - Managing database sessions
  - Writing or running Alembic migrations
allowed-tools:
  - filesystem
  - terminal
---

# SQLAlchemy Async

## Objective

Implement async persistence using SQLAlchemy 2.x. All database access lives exclusively
in `infrastructure/db/`. The domain layer never sees SQLAlchemy — repositories map
ORM rows to domain entities and back.

---

## Important

Reference implementations only.

Reuse existing adapters, engines, session factories, and dependency injection
mechanisms whenever already implemented in the project.

Do NOT replace existing database infrastructure unless explicitly requested.

---

## Supported Drivers

```python
# PostgreSQL
postgresql+asyncpg://user:pass@host:5432/db

# MySQL
mysql+aiomysql://user:pass@host:3306/db
```

---

## Engine and Session Factory

Define the engine and session factory at module level so they can be imported by both
`lifespan` (for `dispose`) and `get_db_session` (for per-request sessions).
Never call `engine.dispose()` here — that is `lifespan`'s responsibility.

```python
# src/infrastructure/db/session.py
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from src.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,        # detect and discard stale connections
    pool_size=10,
    max_overflow=20,
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    expire_on_commit=False,    # avoid lazy-load errors after commit
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Per-request dependency. Session is closed after the response."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()
```

`engine.dispose()` is called in `lifespan` shutdown — not here.

---

## Declarative Base

```python
# src/infrastructure/db/base.py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

---

## ORM Models

ORM models are infrastructure concerns only. They MUST NOT be imported by domain or
application layers. Use SQLAlchemy 2.x `Mapped` / `mapped_column` style.

The following is a **reference example** — adapt table names, columns, and relationships
to your domain:

```python
# src/infrastructure/db/models/<your_entity>_orm.py
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.db.base import Base


class YourEntityORM(Base):
    __tablename__ = "your_entities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

**Conventions:**
- Use `Mapped[T]` for all columns — it provides full type inference.
- Add `index=True` on columns used in `WHERE` clauses (lookups, joins).
- Use `String(n)` with an explicit length for portability across MySQL and PostgreSQL.
- Use `DateTime(timezone=True)` for all timestamps.
- Separate ORM models from domain entities — never reuse one as the other.

---

## Repository Pattern

Repositories implement domain port interfaces.
They map ORM rows to domain entities and vice versa — no ORM objects ever leave the repository.

```python
# src/infrastructure/db/repositories/<entity>_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.domain.ports.<entity>_repository_port import YourEntityRepositoryPort
from src.domain.models.<entity> import YourDomainEntity
from src.infrastructure.db.models.<entity>_orm import YourEntityORM


class YourEntityRepository(YourEntityRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, entity: YourDomainEntity) -> None:
        orm = self._to_orm(entity)
        self.session.add(orm)
        await self.session.commit()

    async def find_by_id(self, entity_id: str) -> YourDomainEntity | None:
        result = await self.session.execute(
            select(YourEntityORM).where(YourEntityORM.external_id == entity_id)
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[YourDomainEntity]:
        result = await self.session.execute(
            select(YourEntityORM).limit(limit).offset(offset)
        )
        return [self._to_domain(row) for row in result.scalars().all()]

    # ── Mapping helpers ────────────────────────────────────────

    @staticmethod
    def _to_domain(row: YourEntityORM) -> YourDomainEntity:
        return YourDomainEntity(
            id=row.external_id,
            name=row.name,
            status=row.status,
            description=row.description,
        )

    @staticmethod
    def _to_orm(entity: YourDomainEntity) -> YourEntityORM:
        return YourEntityORM(
            external_id=entity.id,
            name=entity.name,
            status=entity.status,
            description=entity.description,
        )
```

---

## Transaction Management

UUse `session.begin()` when multiple operations must be atomic:

```python
async with session.begin():
    session.add(entity_orm)
    session.add(related_orm)
# commits automatically on exit; rolls back on exception
```

For single-operation saves, calling `commit()` directly is acceptable.

---

## Query Rules

- Prefer `select()` over legacy `session.query()`.
- Use `scalar_one_or_none()` for single-row lookups.
- Use `scalars().all()` for lists.
- Add indexes on columns used in `WHERE` and `JOIN` clauses.
- Avoid raw SQL unless strictly necessary; prefer SQLAlchemy expressions.

<!-- ---

## Alembic Migrations

Initialize Alembic once:

```bash
alembic init -t async alembic
```

Configure `alembic/env.py` to use the async engine and import `Base.metadata`:

```python
from src.infrastructure.db.base import Base
target_metadata = Base.metadata
```

Migration rules:
- One migration per feature/change.
- Use descriptive names: `add_itsm_system_to_alerts`.
- Never perform destructive operations (DROP COLUMN) without a fallback plan.
- Always review autogenerated migrations before applying.

Generate and apply:

```bash
alembic revision --autogenerate -m "add_itsm_system_to_alerts"
alembic upgrade head
``` -->