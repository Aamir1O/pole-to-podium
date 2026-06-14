from fastapi import APIRouter
from db.connection import test_connection

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
