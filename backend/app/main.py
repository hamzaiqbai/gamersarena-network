"""
GAN - Gaming Arena Network
FastAPI Main Application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database import init_db, engine, Base
from .routers import (
    auth_router,
    users_router,
    wallets_router,
    tournaments_router,
    payments_router,
    whatsapp_router,
    admin_router
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting GAN application...")
    
    # Create database tables
    try:
        init_db()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    # Seed initial data (token bundles)
    try:
        await seed_initial_data()
    except Exception as e:
        logger.error(f"Seeding error: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GAN application...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Gaming tournament platform with virtual token economy",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None
)

# Configure CORS
origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(wallets_router)
app.include_router(tournaments_router)
app.include_router(payments_router)
app.include_router(whatsapp_router)
app.include_router(admin_router)


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Root redirect
@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs" if settings.DEBUG else "Disabled in production",
        "health": "/api/health"
    }


async def seed_initial_data():
    """Seed initial data like token bundles"""
    from sqlalchemy.orm import Session
    from .database import SessionLocal
    from .models.tournament import TokenBundle
    
    db = SessionLocal()
    try:
        # Check if bundles exist
        existing = db.query(TokenBundle).count()
        if existing > 0:
            logger.info(f"Token bundles already exist ({existing})")
            return
        
        # Create default bundles
        bundles = [
            TokenBundle(
                name="Starter Pack",
                tokens=100,
                bonus_tokens=0,
                price_pkr=1399,
                price_usd=4.99,
                description="Perfect for beginners",
                sort_order=1,
                is_active=True
            ),
            TokenBundle(
                name="Popular Pack",
                tokens=200,
                bonus_tokens=10,
                price_pkr=2239,
                price_usd=7.99,
                description="Most popular choice",
                badge="POPULAR",
                sort_order=2,
                is_active=True,
                is_featured=True
            ),
            TokenBundle(
                name="Value Pack",
                tokens=500,
                bonus_tokens=50,
                price_pkr=5039,
                price_usd=17.99,
                description="Best value for money",
                badge="BEST VALUE",
                sort_order=3,
                is_active=True
            ),
            TokenBundle(
                name="Pro Pack",
                tokens=1000,
                bonus_tokens=150,
                price_pkr=8399,
                price_usd=29.99,
                description="For serious gamers",
                sort_order=4,
                is_active=True
            ),
            TokenBundle(
                name="Ultimate Pack",
                tokens=2500,
                bonus_tokens=500,
                price_pkr=19599,
                price_usd=69.99,
                description="Maximum tokens, maximum wins",
                badge="ULTIMATE",
                sort_order=5,
                is_active=True
            )
        ]
        
        for bundle in bundles:
            db.add(bundle)
        
        db.commit()
        logger.info(f"Created {len(bundles)} token bundles")
        
    finally:
        db.close()


# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
