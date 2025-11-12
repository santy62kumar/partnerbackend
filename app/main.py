from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api.v1 import auth, verification, jobs


# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Partner App API",
    description="User Registration and Verification System",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(verification.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "Partner App API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "API is running"
    }