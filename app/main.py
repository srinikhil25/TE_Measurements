from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import auth

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "TE Measurements API",
        "version": settings.APP_VERSION
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
    return {"status": "healthy", "version": settings.APP_VERSION}
