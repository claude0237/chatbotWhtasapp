"""Main Application Entry Point"""
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.jobs.followup import run_followup_job
from app.config import settings
from app.auth.routes import router as auth_router
from app.companies.routes import router as companies_router
from app.companies.controllers.ml_quotas import router as ml_quotas_router
from app.users.routes import router as users_router
from app.whatsapp.routes import router as whatsapp_router
from app.conversations.routes import router as conversations_router
from app.customers.routes import router as customers_router
from app.bot.routes import router as bot_router
from app.knowledge.routes import router as knowledge_router
from app.ml.routes import router as ml_router, public_router as ml_public_router
from app.channels.routes import router as channels_router
from app.notifications.controllers import router as notifications_router
from app.analytics.controllers import router as analytics_router
from app.products.controllers import router as products_router
from app.reservations.controllers import router as reservations_router
from app.upload import router as upload_router

@asynccontextmanager
async def lifespan(application: FastAPI):
    task = asyncio.create_task(run_followup_job())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="WhatsApp SaaS Platform API",
    redirect_slashes=False,
    debug=settings.app_debug,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(companies_router)
app.include_router(ml_quotas_router)
app.include_router(users_router)
app.include_router(whatsapp_router)
app.include_router(conversations_router)
app.include_router(customers_router)
app.include_router(bot_router)
app.include_router(knowledge_router)
app.include_router(ml_router)
app.include_router(ml_public_router, prefix="/ml", tags=["ML Public"])
app.include_router(channels_router)
app.include_router(notifications_router)
app.include_router(analytics_router)
app.include_router(products_router)
app.include_router(reservations_router)
app.include_router(upload_router)

# Serve uploaded files
_static_dir = Path(__file__).parent.parent / "static"
_static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "WhatsApp SaaS Platform API",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_debug,
    )
