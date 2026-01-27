from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api.v1 import auth, verification, jobs, checklist, odooBomApi

from app.model import associations
# from app.model import ip, job, checklist

from fastapi import FastAPI, HTTPException
import xmlrpc.client
from fastapi.responses import JSONResponse

from app.routes.auth import router as auth_router
from app.routes.approval import router as approval_router
from app.routes.job import router as job_router
from app.routes.analytics import router as analytics_router



url = 'https://modula.odoo.com'  # Replace with your Odoo instance URL
db = 'modula'  # Odoo database name
username = 'admin@ayena.in'  # Odoo login username
password = '1'  # Odoo login password

# Setting up the connection to Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

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
    allow_origins=[
        "http://localhost:3000",   # React dev
        # add prod domain later
        # "https://partner.modula.in"
    ],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(verification.router, prefix="/api/v1/auth")
app.include_router(jobs.router, prefix="/api/v1/auth")
app.include_router(checklist.router, prefix="/api/v1/auth")
app.include_router(odooBomApi.router, prefix="/api/v1/auth")  
app.include_router(auth_router)
app.include_router(approval_router)
app.include_router(job_router)
app.include_router(analytics_router)


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




