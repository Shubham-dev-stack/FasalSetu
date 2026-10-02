from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.deps import get_current_user
from app.core.errors import AppException, register_error_handlers
from app.db.models import User
from app.db.seed import (
    seed_demo_listings,
    seed_demo_orders,
    seed_demo_requirements,
    seed_reference_and_users,
    seed_synthetic_demand_and_prices,
)
from app.modules.analytics.router import router as analytics_router
from app.modules.auth.router import router as auth_router
from app.modules.forecasting.router import router as forecasting_router
from app.modules.listings.router import router as listings_router
from app.modules.logistics.router import router as logistics_router
from app.modules.matching.router import router as matching_router
from app.modules.orders.router import router as orders_router
from app.modules.pricing.router import router as pricing_router
from app.modules.profiles.router import router as profiles_router
from app.modules.reference.router import router as reference_router
from app.modules.requirements.router import router as requirements_router
from app.modules.routes.router import router as routes_router
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

    @app.post("/system/reset-demo", tags=["system"], include_in_schema=False)
    @app.post("/api/v1/system/reset-demo", tags=["system"])
    def reset_demo(current_user: User = Depends(get_current_user)):
        """Drop/recreate tables and reseed deterministic demo data per API.md §1.

        Requires ADMIN or OPERATOR role, and DEMO_MODE=True.
        """
        if not settings.DEMO_MODE:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="DEMO_DISABLED",
                message="Demo reset is disabled in production environments.",
            )

        if current_user.role.upper() not in ["ADMIN", "OPERATOR"]:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Only administrators/operators can reset demo data.",
            )

        # Clear in-memory forecast cache
        from app.modules.forecasting.service import forecast_cache
        forecast_cache.clear()

        # Recreate tables
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        db = SessionLocal()
        try:
            ref_counts = seed_reference_and_users(db)
            syn_counts = seed_synthetic_demand_and_prices(db)
            lst_counts = seed_demo_listings(db)
            req_counts = seed_demo_requirements(db)
            ord_counts = seed_demo_orders(db)

            all_counts = {}
            all_counts.update(ref_counts)
            all_counts.update(syn_counts)
            all_counts.update(lst_counts)
            all_counts.update(req_counts)
            all_counts.update(ord_counts)

            return {
                "status": "reset",
                "counts": all_counts,
            }
        finally:
            db.close()

    # Register API routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(reference_router, prefix="/api/v1")
    app.include_router(profiles_router, prefix="/api/v1")
    app.include_router(listings_router, prefix="/api/v1")
    app.include_router(requirements_router, prefix="/api/v1")
    app.include_router(matching_router, prefix="/api/v1")
    app.include_router(orders_router, prefix="/api/v1")
    app.include_router(forecasting_router, prefix="/api/v1")
    app.include_router(logistics_router, prefix="/api/v1")
    app.include_router(routes_router, prefix="/api/v1")
    app.include_router(pricing_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")

    # Serve built SPA if frontend/dist exists (D-008 single-image deployment)
    import os
    static_dir = os.environ.get(
        "STATIC_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")),
    )
    if os.path.isdir(static_dir):
        from fastapi.responses import FileResponse, JSONResponse
        from fastapi.staticfiles import StaticFiles

        assets_dir = os.path.join(static_dir, "assets")
        if os.path.isdir(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            if full_path.startswith("api/") or full_path == "api":
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "API endpoint not found.",
                            "details": None,
                        }
                    },
                )
            target = os.path.join(static_dir, full_path)
            if full_path and os.path.isfile(target):
                return FileResponse(target)
            index_path = os.path.join(static_dir, "index.html")
            if os.path.isfile(index_path):
                return FileResponse(index_path)
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Resource not found.",
                        "details": None,
                    }
                },
            )

    return app



app = create_app()


