from fastapi import APIRouter, BackgroundTasks

from src.modules.freya.api.dependencies import FreyaFromZabbixUseCaseDep
from src.modules.freya.api.schemas import (
    ZabbixCreationIMResponse,
    ZabbixEvent,
)

router = APIRouter()


@router.post("", status_code=202, response_model=ZabbixCreationIMResponse)
async def create_incident(
    payload: ZabbixEvent,
    use_case: FreyaFromZabbixUseCaseDep,
    background_tasks: BackgroundTasks,
):
    create_im_input = payload.to_create_im_input()
    transaction_id = await use_case.create_pending_im(create_im_input, payload.host_id)
    background_tasks.add_task(
        use_case.process_pending_im, transaction_id, create_im_input
    )
    return ZabbixCreationIMResponse(transaction_id=transaction_id)
