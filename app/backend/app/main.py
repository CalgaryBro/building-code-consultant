"""
Calgary Building Code Expert System - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .database import init_db
from .api import explore, guide, review, zones, checklists, permits

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    init_db()
    print("Database initialized")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Calgary Building Code Expert System API

    Three operating modes:
    - **EXPLORE**: Search and browse building codes
    - **GUIDE**: Get permit requirements for your project
    - **REVIEW**: Check drawings for code compliance
    """,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(explore.router, prefix=f"{settings.api_prefix}/explore", tags=["EXPLORE Mode"])
app.include_router(guide.router, prefix=f"{settings.api_prefix}/guide", tags=["GUIDE Mode"])
app.include_router(review.router, prefix=f"{settings.api_prefix}/review", tags=["REVIEW Mode"])
app.include_router(zones.router, prefix=f"{settings.api_prefix}/zones", tags=["Zones & Parcels"])
app.include_router(checklists.router, prefix=f"{settings.api_prefix}/checklists", tags=["Checklists"])
app.include_router(permits.router, prefix=f"{settings.api_prefix}/permits", tags=["Permit Workflow"])


@app.get("/")
async def root():
    """Root endpoint with system info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "modes": {
            "explore": f"{settings.api_prefix}/explore",
            "guide": f"{settings.api_prefix}/guide",
            "review": f"{settings.api_prefix}/review",
        },
        "codes": {
            "building": settings.nbc_version,
            "building_effective": settings.nbc_effective_date,
            "zoning": settings.bylaw_version,
            "zoning_effective": settings.bylaw_effective_date,
        },
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
