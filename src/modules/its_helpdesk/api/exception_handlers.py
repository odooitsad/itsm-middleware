from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.modules.its_helpdesk.domain.exceptions import (
    ItsHelpdeskClientError,
    TicketCreationError,
)


def register_its_helpdesk_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(TicketCreationError)
    async def ticket_creation_error_handler(
        _: Request, exc: TicketCreationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ItsHelpdeskClientError)
    async def its_helpdesk_client_error_handler(
        _: Request, exc: ItsHelpdeskClientError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc)},
        )
