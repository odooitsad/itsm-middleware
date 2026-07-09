from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError


def register_base_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    @app.exception_handler(RequestValidationError)
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
