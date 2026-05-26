from fastapi import Request
from fastapi.responses import JSONResponse

from src.bmc_helix.domain.exceptions import IncidentCreationError, IncidentNotFoundError


async def incident_creation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, IncidentCreationError)
    return JSONResponse(status_code=502, content={"detail": str(exc)})


async def incident_not_found_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, IncidentNotFoundError)
    return JSONResponse(status_code=404, content={"detail": str(exc)})
