from typing import Annotated

from fastapi import Depends, Request

from src.bmc_helix.application.use_cases import CreateIncidentUseCase
from src.bmc_helix.infrastructure.adapters import BmcHelixAdapter


def get_create_incident_use_case(request: Request):
    adapter: BmcHelixAdapter = request.app.state.bmc_helix
    return CreateIncidentUseCase(adapter)


CreateIncidentDep = Annotated[
    CreateIncidentUseCase, Depends(get_create_incident_use_case)
]
