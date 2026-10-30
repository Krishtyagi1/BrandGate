from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import (
    accounts,
    ai_settings,
    approvals,
    dashboard,
    document_chat,
    drafts,
    followup,
    guidelines,
    insights,
    knowledge,
    reviews,
    rewrites,
    streaming,
    tutorial,
    visual_confirmations,
    visual_tools,
)
from .config import WEB_ORIGIN
from .db import migrate


@asynccontextmanager
async def lifespan(app):
    migrate()
    yield


app = FastAPI(title="Brand Content Review", version="0.2.0", lifespan=lifespan)


class BodyLimitMiddleware:
    """Bound even chunked uploads before the multipart parser allocates temporary files."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] in ("GET", "HEAD", "OPTIONS"):
            return await self.app(scope, receive, send)
        chunks = []
        size = 0
        while True:
            incoming = await receive()
            if incoming["type"] == "http.disconnect":
                return
            chunk = incoming.get("body", b"")
            size += len(chunk)
            if size > 6 * 1024 * 1024:
                response = JSONResponse(
                    {"detail": "Request exceeds the 6 MB transport limit."}, status_code=413
                )
                return await response(scope, receive, send)
            chunks.append(chunk)
            if not incoming.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)


app.add_middleware(BodyLimitMiddleware)


@app.middleware("http")
async def request_guard(request: Request, call_next):
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if request.headers.get("x-inkloom-csrf") != "1":
            return JSONResponse({"detail": "Request verification failed."}, status_code=403)
        origin = request.headers.get("origin")
        if origin and origin != WEB_ORIGIN:
            return JSONResponse({"detail": "Request origin is not allowed."}, status_code=403)
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length) > 6 * 1024 * 1024):
            return JSONResponse(
                {"detail": "Request is too large (maximum 5 MB per file)."},
                status_code=413,
            )
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-transform"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/api/health")
def health():
    from providers.openrouter import settings

    return {
        "status": "ok",
        "phase": "review_workflow",
        "ai_mode": "configured" if settings()["OPENROUTER_API_KEY"] else "unavailable",
    }


app.include_router(accounts.router)
app.include_router(guidelines.router)
app.include_router(streaming.router)
app.include_router(drafts.router)
app.include_router(document_chat.router)
app.include_router(dashboard.router)
app.include_router(ai_settings.router)
app.include_router(reviews.router)
app.include_router(approvals.router)
app.include_router(rewrites.router)
app.include_router(knowledge.router)
app.include_router(tutorial.router)
app.include_router(visual_tools.router)
app.include_router(followup.router)
app.include_router(insights.router)
app.include_router(visual_confirmations.router)
