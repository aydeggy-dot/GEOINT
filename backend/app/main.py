"""
Main FastAPI application for Nigeria Security Early Warning System
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.database import init_db, create_spatial_indexes
from app.api.routes import incidents, auth, admin, twofa

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown
    """
    # Startup
    print("Initializing database...")
    try:
        init_db()
        create_spatial_indexes()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {str(e)}")

    yield

    # Shutdown
    print("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Real-time security incident mapping and early warning system for Nigeria",
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(
    auth.router,
    prefix=f"/api/{settings.API_VERSION}",
    tags=["authentication"]
)

app.include_router(
    incidents.router,
    prefix=f"/api/{settings.API_VERSION}/incidents",
    tags=["incidents"]
)

app.include_router(
    admin.router,
    prefix=f"/api/{settings.API_VERSION}",
    tags=["admin"]
)

app.include_router(
    twofa.router,
    prefix=f"/api/{settings.API_VERSION}",
    tags=["2fa"]
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Nigeria Security Early Warning System API",
        "version": settings.API_VERSION,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "nigeria-security-system"
    }
