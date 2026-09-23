import hashlib
import hmac
import logging
import time

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import config

logger = logging.getLogger("benefitsworld")

# Demo-only session auth for the hosted Lab Console (see routes/lab.py's
# auth_router). A single shared password, not per-user accounts — this
# is deliberately not production-grade auth, matching require_lab_token's
# own long-standing "not production auth" framing below. HMAC-signed,
# time-limited, HttpOnly cookie: never readable by frontend JS, so it can
# never leak through a public frontend bundle the way an embedded token
# would.
SESSION_COOKIE_NAME = "bw_lab_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 12  # 12 hours


def _sign(value: str) -> str:
    return hmac.new(config.SESSION_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()


def create_session_token() -> str:
    issued_at = str(int(time.time()))
    return f"{issued_at}.{_sign(issued_at)}"


def verify_session_token(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    issued_at, signature = token.split(".", 1)
    if not hmac.compare_digest(_sign(issued_at), signature):
        return False
    try:
        issued_ts = int(issued_at)
    except ValueError:
        return False
    return (time.time() - issued_ts) <= SESSION_MAX_AGE_SECONDS


def require_lab_token(request: Request) -> None:
    """Gate every /lab route. Accepts either credential:
    - X-Lab-Token header == LAB_TOKEN (original mechanism, unchanged —
      used by local automated tests and research harnesses, e.g. the
      Fable runner's own curl/`claude` invocations)
    - a valid signed session cookie (new — used by the hosted Lab
      Console's browser session after POST /lab/login; see security.py's
      create_session_token/verify_session_token and routes/lab.py's
      auth_router)
    Neither LAB_TOKEN nor LAB_CONSOLE_PASSWORD nor SESSION_SECRET is ever
    sent to, or embedded in, any frontend bundle."""
    if request.headers.get("x-lab-token") == config.LAB_TOKEN:
        return
    if verify_session_token(request.cookies.get(SESSION_COOKIE_NAME)):
        return
    raise HTTPException(status_code=401, detail="invalid or missing lab credentials")


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
