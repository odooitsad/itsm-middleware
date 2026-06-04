from fastapi import APIRouter

from src.bmc_helix.api.dependencies import CreateIncidentDep
from src.bmc_helix.api.schemas import (
    CreateIncidentResponse,
    ZabbixEvent,
)

router = APIRouter(prefix="/incidents", tags=["Zabbix"])


@router.post("/from-zabbix", response_model=CreateIncidentResponse, status_code=201)
async def create_incident(payload: ZabbixEvent, create_incident: CreateIncidentDep):
    created_incident = await create_incident.execute(
        payload.to_input(),
        service_code=payload.host_name,
        event_id=payload.event_id,
    )
    return created_incident
