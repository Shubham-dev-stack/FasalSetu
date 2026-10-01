from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.errors import register_error_handlers
from app.modules.auth.router import router as auth_router
from app.modules.forecasting.router import router as forecasting_router
from app.modules.listings.router import router as listings_router
from app.modules.orders.router import router as orders_router
from app.modules.profiles.router import router as profiles_router
from app.modules.reference.router import router as reference_router
from app.modules.requirements.router import router as requirements_router
from ml.predict import get_model_artifacts


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="FasalSetu API",
        description="AI-assisted direct agricultural supply-chain coordination platform",
        version="0.1.0",
        docs_url="/docs" if settings.APP_ENV == "dev" else None,
        redoc_url=None,
    )

    # Register error handlers
    register_error_handlers(app)

    # CORS configuration
    if settings.APP_ENV == "dev":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # System endpoints
    @app.get("/api/v1/health", tags=["system"])
    def health():
        db_status = "ok"
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
        except Exception:
            db_status = "error"

        artifacts = get_model_artifacts()
        model_loaded = artifacts is not None
        deployed_method = (
            artifacts["model_card"].get("deployed_method", "NONE")
            if artifacts
            else "NONE"
        )

        return {
            "status": "ok",
            "db": db_status,
            "model": {
                "loaded": model_loaded,
                "deployed_method": deployed_method,
            },
            "demo_mode": settings.DEMO_MODE,
            "version": "0.1.0",
        }

    # Register API routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(reference_router, prefix="/api/v1")
    app.include_router(profiles_router, prefix="/api/v1")
    app.include_router(listings_router, prefix="/api/v1")
    app.include_router(requirements_router, prefix="/api/v1")
    app.include_router(orders_router, prefix="/api/v1")
    app.include_router(forecasting_router, prefix="/api/v1")

    return app



app = create_app()

