import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    AppError,
    IdempotencyConflictError,
    ItemAlreadyExistsError,
    ItemNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ItemNotFoundError)
    async def item_not_found_handler(_: Request, exc: ItemNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc) or "Item not found"},
        )

    @app.exception_handler(ItemAlreadyExistsError)
    async def item_exists_handler(_: Request, exc: ItemAlreadyExistsError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc) or "Item already exists"},
        )

    @app.exception_handler(IdempotencyConflictError)
    async def idempotency_conflict_handler(
        _: Request,
        exc: IdempotencyConflictError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc) or "Idempotency key reused with different payload"},
        )

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc) or "Application error"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        structlog.get_logger(__name__).exception(
            "unhandled_error",
            request_id=request_id,
            error=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "request_id": request_id,
            },
        )
