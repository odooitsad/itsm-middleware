from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.bmc_helix.application.use_cases import CreateIncidentUseCase
from src.bmc_helix.infrastructure.adapters import BmcHelixAdapter
from src.bmc_helix.infrastructure.repositories import TransactionRepository
from src.core.database.session import DatabaseAdapter


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    db: DatabaseAdapter = request.app.state.db
    async for session in db.session():
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_transaction_repository(session: DbSessionDep) -> TransactionRepository:
    return TransactionRepository(session)


TransactionRepoDep = Annotated[
    TransactionRepository, Depends(get_transaction_repository)
]


def get_create_incident_use_case(
    request: Request,
    repository: TransactionRepoDep,
) -> CreateIncidentUseCase:
    adapter: BmcHelixAdapter = request.app.state.bmc_helix
    return CreateIncidentUseCase(adapter, repository)


CreateIncidentDep = Annotated[
    CreateIncidentUseCase, Depends(get_create_incident_use_case)
]
