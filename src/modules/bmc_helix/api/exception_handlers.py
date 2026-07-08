from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.modules.bmc_helix.domain.exceptions import (
    BmcHelixClientError,
    IncidentCreationError,
)


async def validation_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """
    Custom handler for Pydantic validation errors and FastAPI request validation errors.
    Returns user-friendly error messages.
    """
    assert isinstance(exc, (ValidationError, RequestValidationError))
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Validation error", "errors": errors},
    )


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
    if exc.bmc_errors:
        content["bmc_errors"] = _bmc_errors_payload(exc)
    return JSONResponse(status_code=502, content=content)


async def bmc_helix_client_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, BmcHelixClientError)
    content: dict = {"detail": str(exc)}
    if exc.bmc_errors:
        content["bmc_errors"] = _bmc_errors_payload(exc)
    return JSONResponse(status_code=exc.status_code, content=content)
