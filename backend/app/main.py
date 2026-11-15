"""
StoryForge AI - FastAPI Application Entry Point

Main application factory with CORS, routers, WebSocket support,
health checks, and static file serving.
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.events import lifespan

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Application factory that builds and configures the FastAPI instance."""

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="AI-powered video story generation pipeline — from idea to published video.",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS Middleware ──────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── API Routers ─────────────────────────────────────────────────
    _register_routers(application)

    # ── Static File Serving ─────────────────────────────────────────
    _mount_static_files(application)

    # ── Health Check ────────────────────────────────────────────────
    @application.get("/health", tags=["Health"])
    async def health_check() -> JSONResponse:
        """Basic health check endpoint."""
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "app": settings.APP_NAME,
                "version": settings.VERSION,
            },
        )

    @application.get("/", tags=["Dashboard"])
    async def root() -> Any:
        """Serve the StoryForge AI dark-mode dashboard."""
        html_path = Path(__file__).resolve().parent / "static" / "index.html"
        if html_path.exists():
            return FileResponse(html_path)
        return JSONResponse(
            status_code=200,
            content={
                "app": settings.APP_NAME,
                "version": settings.VERSION,
                "docs": "/docs",
                "health": "/health",
            },
        )

    # ── WebSocket ───────────────────────────────────────────────────
    @application.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time progress updates."""
        await websocket.accept()
        logger.info("WebSocket client connected.")
        try:
            while True:
                data = await websocket.receive_text()
                # Echo back for now; will be replaced with job-progress streaming
                await websocket.send_json({"type": "ack", "message": data})
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected.")

    return application


def _register_routers(app: FastAPI) -> None:
    """Import and include all API routers."""
    # Routers are imported here to avoid circular imports and so the app
    # still starts even if a router module has not been created yet.
    router_modules = [
        ("app.api.projects", "/api/v1/projects", ["Projects"]),
        ("app.api.stories", "/api/v1/stories", ["Stories"]),
        ("app.api.scenes", "/api/v1/scenes", ["Scenes"]),
        ("app.api.images", "/api/v1/images", ["Images"]),
        ("app.api.audio", "/api/v1/audio", ["Audio"]),
        ("app.api.renders", "/api/v1/renders", ["Renders"]),
        ("app.api.analytics", "/api/v1/analytics", ["Analytics"]),
        ("app.api.youtube", "/api/v1/youtube", ["YouTube"]),
        ("app.api.system", "/api/v1/system", ["System"]),
    ]
    for module_path, prefix, tags in router_modules:
        try:
            import importlib
            module = importlib.import_module(module_path)
            router = getattr(module, "router", None)
            if router:
                app.include_router(router, prefix=prefix, tags=tags)
                logger.info("Registered router: %s -> %s", module_path, prefix)
        except (ImportError, AttributeError) as exc:
            logger.debug("Router %s not yet available: %s", module_path, exc)


def _mount_static_files(app: FastAPI) -> None:
    """Mount static file directories for serving generated assets."""
    outputs_dir = Path(settings.BASE_DIR) / settings.OUTPUTS_DIR
    outputs_dir.mkdir(parents=True, exist_ok=True)

    app.mount(
        "/static/outputs",
        StaticFiles(directory=str(outputs_dir)),
        name="outputs",
    )

    assets_dir = Path(settings.BASE_DIR) / settings.ASSETS_DIR
    assets_dir.mkdir(parents=True, exist_ok=True)

    app.mount(
        "/static/assets",
        StaticFiles(directory=str(assets_dir)),
        name="assets",
    )


# Create the app instance
app = create_app()
