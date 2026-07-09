from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.modules.bmc_helix.domain.exceptions import (
    BmcHelixClientError,
    IncidentCreationError,
)


def _bmc_errors_payload(
    exc: IncidentCreationError | BmcHelixClientError,
) -> list[dict]:
    return [
        {
            "messageType": e.message_type,
            "messageText": e.message_text,
            "messageNumber": e.message_number,
            "messageAppendedText": e.message_appended_text,
        }
        for e in exc.bmc_errors
    ]


def register_bmc_helix_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(IncidentCreationError)
    async def incident_creation_error_handler(
        _: Request, exc: IncidentCreationError
    ) -> JSONResponse:
        content: dict = {"detail": str(exc)}
        if exc.bmc_errors:
            content["bmc_errors"] = _bmc_errors_payload(exc)
        return JSONResponse(status_code=502, content=content)

    @app.exception_handler(BmcHelixClientError)
    async def bmc_helix_client_error_handler(
        _: Request, exc: BmcHelixClientError
    ) -> JSONResponse:
        content: dict = {"detail": str(exc)}
        if exc.bmc_errors:
            content["bmc_errors"] = _bmc_errors_payload(exc)
        return JSONResponse(status_code=exc.status_code, content=content)
