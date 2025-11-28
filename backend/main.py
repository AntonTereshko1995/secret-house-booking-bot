"""
Secret House Booking Backend API
FastAPI application providing REST API for booking management system.
"""
import sys
import os
from contextlib import asynccontextmanager

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import config


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database, scheduler, etc.
    print(f"🚀 Starting Secret House Booking API on {config.API_HOST}:{config.API_PORT}")
    print(f"📊 Database: {config.DATABASE_URL}")
    print(f"🔧 Debug mode: {config.DEBUG}")

    # Run database migrations
    from backend.db.run_migrations import run_migrations
    run_migrations()

    yield

    # Shutdown: Cleanup resources
    print("👋 Shutting down Secret House Booking API")


# Create FastAPI application
app = FastAPI(
    title="Secret House Booking API",
    description="Backend API for house rental booking system with Telegram bot integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for future web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "secret-house-backend",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Secret House Booking API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }


# Import and register routers
from backend.api.v1.routers import bookings, users, gifts, promocodes, availability, pricing

app.include_router(
    bookings.router,
    prefix="/api/v1/bookings",
    tags=["bookings"]
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["users"]
)

app.include_router(
    gifts.router,
    prefix="/api/v1/gifts",
    tags=["gifts"]
)

app.include_router(
    promocodes.router,
    prefix="/api/v1/promocodes",
    tags=["promocodes"]
)

app.include_router(
    availability.router,
    prefix="/api/v1/availability",
    tags=["availability"]
)

app.include_router(
    pricing.router,
    prefix="/api/v1/pricing",
    tags=["pricing"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG
    )
