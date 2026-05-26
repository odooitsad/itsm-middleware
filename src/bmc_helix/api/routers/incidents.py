from fastapi import APIRouter

from src.bmc_helix.api.dependencies import CreateIncidentDep, GetIncidentDep
from src.bmc_helix.api.schemas import (
    CreateIncidentRequest,
    CreateIncidentResponse,
    IncidentInfoResponse,
)

router = APIRouter(prefix="/incidents", tags=["BMC-Helix"])


@router.post("/from-bmc", response_model=CreateIncidentResponse, status_code=201)
async def create_incident(
    payload: CreateIncidentRequest, create_incident: CreateIncidentDep
):
    created_incident = await create_incident.execute(payload.to_input())
    return created_incident


@router.get("/{incident_id}", response_model=IncidentInfoResponse)
async def get_incident(incident_id: str, get_incident: GetIncidentDep):
    incident = await get_incident.execute(incident_id)
    return incident
