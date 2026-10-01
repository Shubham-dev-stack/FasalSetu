from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="KrishiSetu API",
        description="AI-assisted direct agricultural supply-chain coordination platform",
        version="0.1.0",
        docs_url="/docs" if settings.APP_ENV == "dev" else None,
        redoc_url=None,
    )

    if settings.APP_ENV == "dev":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/api/v1/health", tags=["system"])
    def health():
        return {
            "status": "ok",
            "db": "ok",
            "model": {"loaded": False, "deployed_method": "NONE"},
            "demo_mode": settings.DEMO_MODE,
            "version": "0.1.0",
        }

    return app


app = create_app()
