from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app import config

ALLOWED_METHODS = "GET, POST, OPTIONS"
ALLOWED_HEADERS = "Content-Type, X-Lab-Token"


def _allowed_origin_for(path: str) -> str:
    """Lab routes are only reachable from the Lab Console's own origin.
    Every other (agent-visible) route is only reachable from the agent
    frontend's origin. This is enforced per-request-path, not globally —
    FastAPI/Starlette's built-in CORSMiddleware only supports one origin
    list for the whole app, which isn't fine-grained enough for this
    isolation requirement."""
    if path.startswith("/lab"):
        return config.LAB_ORIGIN
    return config.AGENT_ORIGIN


class PathScopedCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        allowed_origin = _allowed_origin_for(request.url.path)
        origin_ok = origin is not None and origin == allowed_origin

        if request.method == "OPTIONS":
            if origin_ok:
                return Response(
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Origin": allowed_origin,
                        "Access-Control-Allow-Methods": ALLOWED_METHODS,
                        "Access-Control-Allow-Headers": ALLOWED_HEADERS,
                    },
                )
            # Wrong/missing origin for this path: no CORS headers, so the
            # browser refuses to let the calling page read (or even send,
            # for a preflighted request) the real request.
            return Response(status_code=403)

        response = await call_next(request)
        if origin_ok:
            response.headers["Access-Control-Allow-Origin"] = allowed_origin
        return response
