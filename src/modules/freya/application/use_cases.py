from src.core.logger import get_logger
from src.modules.freya.domain.entities import (
    CloseIMInput,
    CreateIMInput,
    IMResult,
    UpdateIMInput,
)
from src.modules.freya.domain.exceptions import FreyaClientError
from src.modules.freya.domain.ports import FreyaPort

logger = get_logger(__name__)


def _build_create_im_payload(payload: CreateIMInput) -> dict:
    return {
        "Area": payload.area,
        "Categoria": payload.category,
        "CiAfectado": payload.affected_ci,
        "CiOperativo": payload.ci_is_operational,
        "Descripcion": payload.description,
        "IdEvento": payload.event_id,
        "Impacto": payload.impact,
        "InitService": payload.init_service,
        "Origen": payload.origin,
        "SubCategoria": payload.sub_category,
        "Titulo": payload.title,
        "Urgencia": payload.urgency,
    }


def _build_update_im_payload(payload: UpdateIMInput) -> dict:
    return {
        "ImExistente": payload.existing_im,
        "NotaTrabajo": payload.working_note,
        "Tipo": payload.type,
    }


def _build_close_im_payload(payload: CloseIMInput) -> dict:
    return {
        "IdIm": payload.im_id,
        "FechaFinInterrupcionDeServicio": payload.service_end_date,
    }


class FreyaUseCase:
    def __init__(self, adapter: FreyaPort) -> None:
        self._adapter = adapter

    async def create_im(self, payload: CreateIMInput) -> IMResult:
        body = _build_create_im_payload(payload)
        logger.info(f"Creating IM - CI: {body}")
        result = await self._adapter.send_post_request("CreateIM", body)

        im_index = result.find("IM")
        if im_index == -1:
            logger.warning(f"Unexpected response while creating IM: {result}")
            raise FreyaClientError("Unexpected response while creating the IM")

        im = result[im_index:]
        logger.info(f"IM created: {im} - CI: {payload.affected_ci}")
        return IMResult(detail="IM created successfully", im=im)

    async def update_im(self, payload: UpdateIMInput) -> IMResult:
        body = _build_update_im_payload(payload)
        im = payload.existing_im
        logger.info(f"Adding working note to {im}")
        result = await self._adapter.send_post_request("UpdateIm", body)
        logger.info(f"Working note added to {im}: {payload.working_note[0][:200]}...")
        return IMResult(detail=result, im=im)

    async def close_im(self, payload: CloseIMInput) -> IMResult:
        body = _build_close_im_payload(payload)
        logger.info(f"Resolving IM: {body}")
        result = await self._adapter.send_post_request("ResolvedIM", body)
        logger.info(f"{payload.im_id} resolved")
        return IMResult(detail=result, im=payload.im_id)
