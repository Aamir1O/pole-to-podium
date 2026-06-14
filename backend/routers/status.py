from fastapi import APIRouter
from db.connection import test_connection
from backend.services.db_service import get_cached_data

router = APIRouter()

@router.get("/status")
def get_status():
    try:
        test_connection()
        return {
            "status": "ok",
            "db_connection": "connected",
            "message": "Pole to Podium API is healthy."
        }
    except Exception as e:
        return {
            "status": "error",
            "db_connection": "failed",
            "details": str(e)
        }

@router.post("/refresh")
def refresh_cache():
    try:
        get_cached_data(force_reload=True)
        return {
            "status": "ok",
            "message": "Cache refreshed successfully."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to refresh cache: {str(e)}"
        }

