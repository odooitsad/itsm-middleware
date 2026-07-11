from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.session import DatabaseAdapter
from src.modules.its_helpdesk.application.use_cases import (
    CreateTicketUseCase,
)
from src.modules.its_helpdesk.infrastructure.adapters import ItsHelpdeskAdapter
from src.modules.its_helpdesk.infrastructure.repositories import TransactionRepository


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


def get_its_helpdesk_adapter(request: Request) -> ItsHelpdeskAdapter:
    return request.app.state.its_helpdesk


ItsHelpdeskAdapterDep = Annotated[ItsHelpdeskAdapter, Depends(get_its_helpdesk_adapter)]


def get_create_ticket_use_case(
    request: Request,
    repository: TransactionRepoDep,
) -> CreateTicketUseCase:
    adapter: ItsHelpdeskAdapter = request.app.state.its_helpdesk
    return CreateTicketUseCase(adapter, repository)


CreateTicketDep = Annotated[CreateTicketUseCase, Depends(get_create_ticket_use_case)]
