from typing import Annotated

from fastapi import Depends, Request

from src.core.dependencies import DbSessionDep
from src.modules.bmc_helix.application.use_cases import CreateIncidentUseCase
from src.modules.bmc_helix.infrastructure.adapters import BmcHelixAdapter
from src.modules.bmc_helix.infrastructure.repositories import (
    CategorizationsRepository,
    TransactionRepository,
)


def get_transaction_repository(session: DbSessionDep) -> TransactionRepository:
    return TransactionRepository(session)


TransactionRepoDep = Annotated[
    TransactionRepository, Depends(get_transaction_repository)
]


def get_categorizations_repository(session: DbSessionDep) -> CategorizationsRepository:
    return CategorizationsRepository(session)


CategorizationsRepoDep = Annotated[
    CategorizationsRepository, Depends(get_categorizations_repository)
]


def get_create_incident_use_case(
    request: Request,
    transaction_repository: TransactionRepoDep,
    categorization_repository: CategorizationsRepoDep,
) -> CreateIncidentUseCase:
    adapter: BmcHelixAdapter = request.app.state.bmc_helix
    return CreateIncidentUseCase(
        adapter, transaction_repository, categorization_repository
    )


CreateIncidentDep = Annotated[
    CreateIncidentUseCase, Depends(get_create_incident_use_case)
]


def get_bmc_helix_adapter(request: Request) -> BmcHelixAdapter:
    return request.app.state.bmc_helix


BmcHelixAdapterDep = Annotated[BmcHelixAdapter, Depends(get_bmc_helix_adapter)]
