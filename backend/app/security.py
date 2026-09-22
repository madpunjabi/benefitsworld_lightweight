import logging

from fastapi import Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import config

logger = logging.getLogger("benefitsworld")


def require_lab_token(x_lab_token: str | None = Header(default=None)) -> None:
    """Gate every /lab route. Not production auth — a single static shared
    secret is the simplest isolation that still fails closed if the
    benchmark agent's browser tries to call a lab endpoint directly. The
    frontend-agent bundle never contains this value."""
    if x_lab_token != config.LAB_TOKEN:
        raise HTTPException(status_code=401, detail="invalid or missing lab token")


def install_sanitized_error_handlers(app) -> None:
    """Agent-visible (and lab) routes must never leak stack traces, ORM
    reprs, SQL, or internal exception text to the client. Full detail is
    logged server-side only."""

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        logger.warning("validation error on %s: %s", request.url.path, exc)
        return JSONResponse(status_code=422, content={"error": "invalid_request"})

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        # HTTPException.detail is developer-authored (e.g. "invalid lab token",
        # "requirement not found") and safe to return as-is; it never carries
        # ORM/stack-trace content.
        return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception):
        logger.exception("unhandled error on %s", request.url.path)
        return JSONResponse(status_code=500, content={"error": "internal_error"})
