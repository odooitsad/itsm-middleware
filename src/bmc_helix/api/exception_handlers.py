from fastapi import Request
from fastapi.responses import JSONResponse

from src.bmc_helix.domain.exceptions import BmcHelixClientError, IncidentCreationError


def _bmc_errors_payload(exc: IncidentCreationError | BmcHelixClientError) -> list[dict]:
    return [
        {
            "messageType": e.message_type,
            "messageText": e.message_text,
            "messageNumber": e.message_number,
            "messageAppendedText": e.message_appended_text,
        }
        for e in exc.bmc_errors
    ]


async def incident_creation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, IncidentCreationError)
    content: dict = {"detail": str(exc)}
    print(f"BMC Errors{exc.bmc_errors}")
    if exc.bmc_errors:
        print("Adding BMC errors to response")
        content["bmc_errors"] = _bmc_errors_payload(exc)
    return JSONResponse(status_code=502, content=content)


async def bmc_helix_client_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, BmcHelixClientError)
    content: dict = {"detail": str(exc)}
    if exc.bmc_errors:
        content["bmc_errors"] = _bmc_errors_payload(exc)
    return JSONResponse(status_code=exc.status_code, content=content)
