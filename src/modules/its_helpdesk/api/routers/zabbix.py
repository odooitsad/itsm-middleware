from fastapi import APIRouter

from src.modules.its_helpdesk.api.dependencies import CreateTicketDep
from src.modules.its_helpdesk.api.schemas import (
    CreateTicketResponse,
    ZabbixHelpdeskEvent,
)

router = APIRouter()


@router.post("", response_model=CreateTicketResponse, status_code=201)
async def create_ticket_from_zabbix(
    payload: ZabbixHelpdeskEvent, create_ticket: CreateTicketDep
):
    response = await create_ticket.execute(
        payload.to_input(),
        service_code=payload.host_name,
        event_id=payload.event_id,
    )
    return response
