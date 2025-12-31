"""FastAPI application entry point."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router
from .core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="A web-based Obsidian vault reader",
    docs_url="/api/docs" if settings.is_development else None,
    redoc_url="/api/redoc" if settings.is_development else None,
)

# CORS middleware for development
if settings.is_development:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    import logging

    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Ensure data directory exists
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    # Initialize vault manager
    from .services.vault_manager import vault_manager

    await vault_manager.initialize()

    # Build search indexes for all vaults
    from .services.search import search_service

    for vault_info in vault_manager.list_vaults():
        vault = vault_manager.get_vault(vault_info.id)
        if vault:
            try:
                search_service.build_index(vault_info.id, vault.vault_path)
            except Exception as e:
                logging.warning(f"Failed to build search index for {vault_info.id}: {e}")


# Include API routes
app.include_router(api_router, prefix="/api")

# Serve static files in production (frontend build)
if not settings.is_development:
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    static_path = Path(__file__).parent.parent.parent.parent / "static"
    if static_path.exists():
        app.mount("/assets", StaticFiles(directory=static_path / "assets"), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """Serve SPA for all non-API routes."""
            file_path = static_path / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(static_path / "index.html")


def run():
    """Run the application."""
    uvicorn.run(
        "obsidian_reader.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
    )


if __name__ == "__main__":
    run()

