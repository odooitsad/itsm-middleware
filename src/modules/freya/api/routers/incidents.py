from fastapi import APIRouter, status

from src.modules.freya.api.dependencies import FreyaUseCaseDep
from src.modules.freya.api.schemas import (
    CloseIMRequest,
    CreateIMRequest,
    ImId,
    IMResponse,
    UpdateIMRequest,
)

router = APIRouter()


@router.post("", response_model=IMResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(payload: CreateIMRequest, use_case: FreyaUseCaseDep):
    return await use_case.create_im(payload.to_input())


@router.post("/{incident_id}/working-notes", response_model=IMResponse)
async def add_working_note(
    incident_id: ImId, payload: UpdateIMRequest, use_case: FreyaUseCaseDep
):
    return await use_case.update_im(payload.to_input(incident_id))


@router.post("/{incident_id}/close", response_model=IMResponse)
async def close_incident(
    incident_id: ImId, payload: CloseIMRequest, use_case: FreyaUseCaseDep
):
    return await use_case.close_im(payload.to_input(incident_id))
