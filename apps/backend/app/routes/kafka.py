from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from kakfa import get_messages_file, load_messages

router = APIRouter(prefix="/kafka", tags=["kafka"])

@router.get("/smartwatch/messages")
def get_smartwatch_messages(
    limit: int = Query(
        default=0,
        ge=0,
        le=5000,
        description="Numero maximo de mensajes recientes (0 = todos).",
    ),
    download: bool = Query(
        default=False,
        description="Si es true, devuelve el archivo JSONL para descargar.",
    ),
):
    file_path = get_messages_file()

    if download:
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="No hay mensajes almacenados.")
        return FileResponse(
            file_path,
            media_type="application/json",
            filename=file_path.name,
        )

    records = load_messages(limit if limit > 0 else None)
    return {"count": len(records), "messages": records}
