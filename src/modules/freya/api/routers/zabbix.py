from fastapi import APIRouter, BackgroundTasks, HTTPException

from src.modules.freya.api.dependencies import FreyaFromZabbixUseCaseDep
from src.modules.freya.api.schemas import (
    IMResponse,
    ZabbixCreationIMResponse,
    ZabbixEvent,
)

router = APIRouter()


@router.post("", status_code=202, response_model=ZabbixCreationIMResponse)
async def create_incident(
    event: ZabbixEvent,
    use_case: FreyaFromZabbixUseCaseDep,
    background_tasks: BackgroundTasks,
):
    create_im_input = event.to_create_im_input()
    transaction_id = await use_case.create_pending_im(create_im_input, event.host_id)
    background_tasks.add_task(
        use_case.process_pending_im, transaction_id, create_im_input
    )
    return ZabbixCreationIMResponse(transaction_id=transaction_id)


@router.post("/closure", response_model=IMResponse)
async def close_incident(
    event: ZabbixEvent,
    use_case: FreyaFromZabbixUseCaseDep,
):
    transaction_id = event.transaction_id
    if not transaction_id:
        raise HTTPException(status_code=400, detail="transaction id es required")
    close_im_input = event.to_close_im_input()
    result = await use_case.close_im_from_zabbix(close_im_input, transaction_id)
    return result
