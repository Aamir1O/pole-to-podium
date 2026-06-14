import os
import sys

# Add project root and backend directory to sys.path to allow running from anywhere
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import status, dashboard, predictions, drivers, teams, telemetry, analytics

app = FastAPI(
    title="Pole to Podium API",
    description="Production-grade API backend for F1 predictions and analytics",
    version="1.0.0",
)

# Enable CORS for Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under api/v1 prefix
app.include_router(status.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")
app.include_router(drivers.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(telemetry.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Pole to Podium API is running. Direct endpoints to /api/v1"}
