from typing import Annotated

from fastapi import Depends, Request

from src.core.dependencies import DbSessionDep
from src.modules.freya.application.use_cases import FreyaUseCase
from src.modules.freya.infrastructure.repositories import TransactionRepository


def get_transaction_repository(session: DbSessionDep) -> TransactionRepository:
    return TransactionRepository(session)


TransactionRepoDep = Annotated[
    TransactionRepository, Depends(get_transaction_repository)
]


def get_freya_use_case(
    request: Request, repository: TransactionRepoDep
) -> FreyaUseCase:
    adapter = request.app.state.freya
    return FreyaUseCase(adapter, repository)


FreyaUseCaseDep = Annotated[FreyaUseCase, Depends(get_freya_use_case)]
