"""
Calgary Building Code Expert System - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .database import init_db
from .api import explore, guide, review, zones, checklists, permits, auth, documents, fees, addresses, public, standata, admin, dssp, quantity_survey, reports, presets, chat

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    init_db()
    print("Database initialized")

    # Initialize price scheduler for background price updates
    try:
        from .services.quantity_survey.price_scheduler import initialize_price_scheduler
        scheduler = await initialize_price_scheduler(
            fred_api_key=getattr(settings, 'fred_api_key', None),
            api_ninjas_key=getattr(settings, 'api_ninjas_key', None)
        )
        print("Price scheduler initialized with scheduled jobs:")
        for job in scheduler.get_scheduled_jobs():
            print(f"  - {job['name']}: next run at {job['next_run']}")
    except Exception as e:
        print(f"Warning: Price scheduler initialization failed: {e}")
        print("Price updates will not run automatically, but manual refresh is still available.")

    yield

    # Shutdown
    print("Shutting down...")
    try:
        from .services.quantity_survey.price_scheduler import get_price_scheduler
        scheduler = get_price_scheduler()
        scheduler.stop()
        print("Price scheduler stopped")
    except Exception as e:
        print(f"Warning: Error stopping price scheduler: {e}")


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
app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["Authentication"])
app.include_router(explore.router, prefix=f"{settings.api_prefix}/explore", tags=["EXPLORE Mode"])
app.include_router(guide.router, prefix=f"{settings.api_prefix}/guide", tags=["GUIDE Mode"])
app.include_router(review.router, prefix=f"{settings.api_prefix}/review", tags=["REVIEW Mode"])
app.include_router(zones.router, prefix=f"{settings.api_prefix}/zones", tags=["Zones & Parcels"])
app.include_router(checklists.router, prefix=f"{settings.api_prefix}/checklists", tags=["Checklists"])
app.include_router(permits.router, prefix=f"{settings.api_prefix}/permits", tags=["Permit Workflow"])
app.include_router(documents.router, prefix=f"{settings.api_prefix}/documents", tags=["Documents & Checklists"])
app.include_router(fees.router, prefix=f"{settings.api_prefix}/fees", tags=["Fee Calculator"])
app.include_router(addresses.router, prefix=f"{settings.api_prefix}/addresses", tags=["Address Autocomplete"])
app.include_router(public.router, prefix=f"{settings.api_prefix}/public", tags=["Public API (Rate Limited)"])
app.include_router(standata.router, prefix=f"{settings.api_prefix}/standata", tags=["STANDATA Bulletins"])
app.include_router(admin.router, prefix=f"{settings.api_prefix}/admin", tags=["Admin"])
app.include_router(dssp.router, prefix=settings.api_prefix, tags=["DSSP Calculator"])
app.include_router(quantity_survey.router, prefix=f"{settings.api_prefix}/quantity-survey", tags=["Quantity Survey"])
app.include_router(reports.router, prefix=settings.api_prefix, tags=["Calculation Reports"])
app.include_router(presets.router, prefix=settings.api_prefix, tags=["Industry Presets"])
app.include_router(chat.router, prefix=settings.api_prefix, tags=["AI Chat Q&A"])


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
