from fastapi import APIRouter

from src.modules.its_helpdesk.api.dependencies import (
    CreateTicketDep,
    ItsHelpdeskAdapterDep,
)
from src.modules.its_helpdesk.api.schemas import (
    CloseTicketRequest,
    CloseTicketResponse,
    CreateTicketRequest,
    CreateTicketResponse,
)

router = APIRouter()


@router.post("", response_model=CreateTicketResponse, status_code=201)
async def create_ticket(payload: CreateTicketRequest, create_ticket: CreateTicketDep):
    response = await create_ticket.execute(payload.to_input())
    return response


@router.post("/close", response_model=CloseTicketResponse, status_code=200)
async def close_ticket(payload: CloseTicketRequest, adapter: ItsHelpdeskAdapterDep):
    response = await adapter.close_ticket(payload.to_input())
    return response
