import json
import logging
import shutil
import time
import uuid
import base64
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
        temp_path.parent.mkdir(parents=True, exist_ok=True)
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

        return {
            "video_url": f"/boxing/videos/processed/{result.processed_filename}",
            "frames_analyzed": result.frame_count,
            "baseline_used": result.baseline_used,
            "session_id": result.session_id,
            "feedback_summary": result.summary_lines,
            "session_rows": result.session_rows,
        }

    except Exception as exc:
        logger.exception("Error al procesar video: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        temp_path.unlink(missing_ok=True)


@router.get("/videos/processed/{filename}")
async def serve_processed_video(filename: str):
    video_path = boxing_service.output_dir / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video no encontrado")
    return FileResponse(video_path, media_type="video/mp4")


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

            action = payload.get("action")
            if action == "reset":
                ws_tracker.reset_state()
                await websocket.send_json({"status": "reset"})
                continue

            msg_type = payload.get("type")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "ts": payload.get("ts")})
                continue

            frame_b64 = payload.get("frame")
            if not frame_b64:
                await websocket.send_json({"error": "frame_missing"})
                continue
            if isinstance(frame_b64, str) and frame_b64.startswith("data:"):
                frame_b64 = frame_b64.split(",", 1)[-1]

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

            annotated, features, feedback_msg, jab_event, landmarks = ws_tracker.process_frame(frame)
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

            # The client overlays vector landmarks on its native feed; NO frame encoding needed.
            await websocket.send_json(
                {
                    "feedback": display_feedback,
                    "jab_detected": bool(jab_event),
                    "frame_index": features.get("frame_index") if features else None,
                    "tracking_state": features.get("tracking_state") if features else "searching",
                    "landmarks": landmarks,
                }
            )

    except WebSocketDisconnect:
        # Client disconnected cleanly — log and exit.
        logger.info("Cliente WebSocket desconectado.")

    except Exception as exc:
        logger.exception("Error en WebSocket (conexión cerrada): %s", exc)


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


@router.get("/videos/pro")
async def list_pro_videos():
    pro_dir = boxing_service.pro_videos_dir
    if not pro_dir.exists():
        return []

    videos = []
    for f in pro_dir.iterdir():
        if f.suffix.lower() in [".mp4", ".mov", ".avi"]:
            videos.append({
                "name": f.name,
                "size": f.stat().st_size,
                "path": str(f)
            })
    return videos


@router.post("/videos/pro/{video_name}/process")
async def process_pro_video(
    video_name: str,
    session_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    pro_path = boxing_service.pro_videos_dir / video_name
    if not pro_path.exists():
        raise HTTPException(status_code=404, detail="Video profesional no encontrado")

    try:
        result = boxing_service.process_video_file(pro_path, video_name, session_id)

        session_record = db.query(BoxingSession).filter(
            BoxingSession.session_id == result.session_id
        ).one_or_none()
        if not session_record:
            session_record = BoxingSession(
                session_id=result.session_id,
                processed_filename=result.processed_filename
            )
            db.add(session_record)

        session_record.frames_analyzed = result.frame_count
        session_record.baseline_used = result.baseline_used
        session_record.feedback_summary = result.summary_lines
        session_record.metrics_path = str(result.metrics_path) if result.metrics_path else None
        db.commit()

        return {
            "video_url": f"/boxing/videos/processed/{result.processed_filename}",
            "frames_analyzed": result.frame_count,
            "session_id": result.session_id,
            "feedback": result.summary_lines,
            "metrics": result.session_rows
        }
    except Exception as exc:
        logger.exception("Error al procesar video profesional: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/cleanup", response_model=CleanupResponse)
async def cleanup_files():
    deleted = boxing_service.cleanup_storage()
    return CleanupResponse(message="Archivos limpiados", **deleted)
