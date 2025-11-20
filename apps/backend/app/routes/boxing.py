import json
import logging
import shutil
import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from config import get_db
from ml_service.boxing_service import boxing_service
from models import BoxingSession
from schemas import (
    BaselineResponse,
    BoxingSessionSchema,
    BoxingStatusResponse,
    CleanupResponse,
    SessionSaveResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/boxing", tags=["boxing"])


@router.post("/baseline", response_model=BaselineResponse)
async def load_baseline(file: UploadFile = File(...)):
    try:
        result = boxing_service.load_baseline(file.filename, file.file)
        return BaselineResponse(**result.__dict__)
    except Exception as exc:  # pragma: no cover - FastAPI runtime
        logger.exception("Error al cargar baseline: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/videos/upload")
async def upload_video(
    file: UploadFile = File(...),
    session_id: Optional[str] = Query(None, description="ID de sesion existente (opcional)"),
    db: Session = Depends(get_db),
):
    temp_filename = f"temp_{uuid.uuid4().hex}_{file.filename}"
    temp_path = boxing_service.temp_dir / temp_filename

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = boxing_service.process_video_file(temp_path, file.filename, session_id)

        session_record = (
            db.query(BoxingSession)
            .filter(BoxingSession.session_id == result.session_id)
            .one_or_none()
        )
        if not session_record:
            session_record = BoxingSession(
                session_id=result.session_id,
                processed_filename=result.processed_filename,
            )
            db.add(session_record)

        session_record.frames_analyzed = result.frame_count
        session_record.baseline_used = result.baseline_used
        session_record.feedback_summary = result.summary_lines
        session_record.metrics_path = str(result.metrics_path) if result.metrics_path else None
        session_record.session_file = str(result.session_file) if result.session_file else None
        session_record.session_rows = result.session_rows
        db.commit()

        return FileResponse(
            result.processed_path,
            media_type="video/mp4",
            filename=result.processed_filename,
            headers=result.headers(),
        )
    except Exception as exc:
        logger.exception("Error al procesar video: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        temp_path.unlink(missing_ok=True)


@router.websocket("/ws/jab")
async def jab_websocket(websocket: WebSocket):
    await websocket.accept()
    ws_tracker = boxing_service.create_realtime_tracker()
    baseline_ref = boxing_service.get_baseline()
    last_feedback_time = 0.0

    try:
        while True:
            message = await websocket.receive()
            if "text" in message and message["text"] is not None:
                payload = json.loads(message["text"])
            elif "bytes" in message and message["bytes"] is not None:
                payload = json.loads(message["bytes"].decode("utf-8"))
            else:
                continue

            frame_b64 = payload.get("frame")
            if not frame_b64:
                await websocket.send_json({"error": "frame_missing"})
                continue

            fps_override = payload.get("fps")
            if fps_override:
                ws_tracker.set_fps(float(fps_override))

            current_baseline = boxing_service.get_baseline()
            if current_baseline is not baseline_ref:
                baseline_ref = current_baseline
                ws_tracker.set_baseline(baseline_ref)

            frame = boxing_service.decode_frame_payload(frame_b64)
            if frame is None:
                await websocket.send_json({"error": "frame_decode_error"})
                continue

            annotated, features, feedback_msg, jab_event = ws_tracker.process_frame(frame)
            output_frame = annotated
            now = time.monotonic()
            display_feedback = None

            if jab_event:
                display_feedback = feedback_msg or "Buen jab detectado."
                last_feedback_time = now
            elif feedback_msg and now - last_feedback_time > 1.5:
                display_feedback = feedback_msg
                last_feedback_time = now

            if display_feedback:
                boxing_service.annotate_feedback_on_frame(output_frame, display_feedback)

            encoded = boxing_service.encode_frame_to_base64(output_frame)
            if encoded is None:
                await websocket.send_json({"error": "encode_error"})
                continue

            await websocket.send_json(
                {
                    "frame": encoded,
                    "feedback": display_feedback,
                    "jab_detected": bool(jab_event),
                    "frame_index": features.get("frame_index") if features else None,
                }
            )
    except WebSocketDisconnect:
        logger.info("Cliente WebSocket desconectado.")
    except Exception as exc:  # pragma: no cover - runtime safety
        logger.exception("Error en WebSocket: %s", exc)
        await websocket.close(code=1011, reason=str(exc))


@router.post("/sessions/save", response_model=SessionSaveResponse)
async def save_session(
    session_id: str = Query(..., description="Sesion a guardar"),
    filename: Optional[str] = Query(None, description="Nombre del archivo parquet"),
):
    result = boxing_service.persist_session(session_id, filename)
    if not result.file_path:
        raise HTTPException(status_code=400, detail="No hay datos para la sesion solicitada")

    return SessionSaveResponse(status="ok", file=str(result.file_path), rows=result.rows)


@router.get("/sessions", response_model=List[BoxingSessionSchema])
async def list_sessions(db: Session = Depends(get_db)):
    records = db.query(BoxingSession).order_by(BoxingSession.created_at.desc()).all()
    return records


@router.get("/status", response_model=BoxingStatusResponse)
async def status():
    return BoxingStatusResponse(
        success=True,
        baseline_loaded=boxing_service.get_baseline() is not None,
        sessions=boxing_service.get_session_stats(),
    )


@router.delete("/cleanup", response_model=CleanupResponse)
async def cleanup_files():
    deleted = boxing_service.cleanup_storage()
    return CleanupResponse(message="Archivos limpiados", **deleted)
