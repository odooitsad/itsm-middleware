from fastapi import APIRouter

from src.modules.bmc_helix.api.dependencies import BmcHelixAdapterDep, CreateIncidentDep
from src.modules.bmc_helix.api.schemas import (
    CreateIncidentRequest,
    CreateIncidentResponse,
    IncidentInfoResponse,
)

router = APIRouter()


@router.post("", response_model=CreateIncidentResponse, status_code=201)
async def create_incident(
    payload: CreateIncidentRequest, create_incident: CreateIncidentDep
):
    created_incident = await create_incident.execute(payload.to_input())
    return created_incident


@router.get("/{incident_id}", response_model=IncidentInfoResponse)
async def get_incident(incident_id: str, adapter: BmcHelixAdapterDep):
    incident = await adapter.get_incident(incident_id)
    return incident
