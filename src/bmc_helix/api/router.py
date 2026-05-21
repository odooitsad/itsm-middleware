from fastapi import APIRouter

from src.bmc_helix.api.dependencies import CreateIncidentDep
from src.bmc_helix.api.schemas import (
    CreateIncidentRequest,
    CreateIncidentResponse,
)

router = APIRouter(prefix="/incidents", tags=["bmc-helix"])


@router.post("/", response_model=CreateIncidentResponse, status_code=201)
async def create_incident(
    payload: CreateIncidentRequest, create_incident: CreateIncidentDep
):
    created_incident = await create_incident.execute(payload.model_dump(by_alias=True))
    return created_incident
