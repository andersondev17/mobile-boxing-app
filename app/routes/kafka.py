"""
Kafka telemetry query endpoints.
"""

from fastapi import APIRouter, HTTPException, Query

from services.events import load_messages

router = APIRouter(prefix="/kafka", tags=["kafka"])


@router.get("/smartwatch/messages")
def get_smartwatch_messages(
    device_id: str = Query(..., description="Device identifier"),
    limit: int = Query(
        default=1,
        ge=1,
        le=100,
        description="Max number of recent records",
    ),
):
    """Query buffered smartwatch telemetry from Redis."""
    records = load_messages(limit=limit, device_id=device_id)
    if not records:
        raise HTTPException(
            status_code=404,
            detail="No hay registros para el dispositivo solicitado.",
        )
    return {"device_id": device_id, "count": len(records), "messages": records}






