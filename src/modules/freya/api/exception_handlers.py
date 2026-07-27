from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.modules.freya.domain.exceptions import FreyaClientError


def register_freya_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(FreyaClientError)
    async def freya_client_error_handler(
        _: Request, exc: FreyaClientError
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})
