from fastapi import APIRouter

from src.modules.bmc_helix.api.dependencies import CreateIncidentDep
from src.modules.bmc_helix.api.schemas import (
    CreateIncidentResponse,
    ZabbixEvent,
)

router = APIRouter()


@router.post("", response_model=CreateIncidentResponse, status_code=201)
async def create_incident(payload: ZabbixEvent, create_incident: CreateIncidentDep):
    created_incident = await create_incident.execute_from_zabbix(payload.to_input())
    return created_incident
