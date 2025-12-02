from fastapi import APIRouter, HTTPException, Query

from kakfa import load_messages

router = APIRouter(prefix="/kafka", tags=["kafka"])


@router.get("/smartwatch/messages")
def get_smartwatch_messages(
    device_id: str = Query(..., description="Identificador del dispositivo."),
    limit: int = Query(
        default=1,
        ge=1,
        le=100,
        description="Numero maximo de registros mas recientes.",
    ),
):
    records = load_messages(limit=limit, device_id=device_id)
    if not records:
        raise HTTPException(
            status_code=404,
            detail="No hay registros para el dispositivo solicitado.",
        )
    return {"device_id": device_id, "count": len(records), "messages": records}
