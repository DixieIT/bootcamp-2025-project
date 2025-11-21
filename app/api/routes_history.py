from fastapi import APIRouter, Query
from app.services.db_service import get_predictions, get_logs

router = APIRouter()

@router.get("/predictions")
def get_prediction_history(
    limit: int = Query(default=10, ge=1, le=100),
    user_id: str = Query(default=None),
    purpose: str = Query(default=None)
):
    """
    Get prediction history from SQLite database

    Query parameters:
    - limit: Number of records to return (1-100, default 10)
    - user_id: Filter by user ID (optional)
    - purpose: Filter by purpose (optional)
    """
    predictions = get_predictions(limit=limit, user_id=user_id, purpose=purpose)

    return {
        "count": len(predictions),
        "predictions": [
            {
                "id": p["id"],
                "prompt": p["prompt"][:100] + "..." if len(p["prompt"]) > 100 else p["prompt"],
                "response": p["response"][:100] + "..." if len(p["response"]) > 100 else p["response"],
                "timestamp": p["timestamp"],
                "user_id": p["user_id"],
                "purpose": p["purpose"],
                "provider": p["provider"],
                "prompt_id": p["prompt_id"],
                "latency_ms": p["latency_ms"]
            }
            for p in predictions
        ]
    }

@router.get("/logs")
def get_log_history(
    limit: int = Query(default=100, ge=1, le=500),
    level: str = Query(default=None)
):
    """
    Get application logs from SQLite database

    Query parameters:
    - limit: Number of records to return (1-500, default 100)
    - level: Filter by log level (INFO, WARNING, ERROR)
    """
    logs = get_logs(limit=limit, level=level)

    return {
        "count": len(logs),
        "logs": [
            {
                "id": log["id"],
                "timestamp": log["timestamp"],
                "level": log["level"],
                "logger_name": log["logger_name"],
                "message": log["message"]
            }
            for log in logs
        ]
    }
