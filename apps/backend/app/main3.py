import base64
import json
from collections import Counter
from datetime import datetime
import logging
import shutil
import time
from pathlib import Path
from typing import Optional
import uuid

import cv2
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, UploadFile, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from ml_service.boxing_jab_tracker import BoxingJabTracker

# -------------------------
# Configuracion basica
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Analizador Deportivo",
    description="API para analisis de ejercicios de boxeo",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carpetas necesarias
TEMP_DIR = Path("videos/temp")
OUTPUT_DIR = Path("videos/output")
PROCESSED_DIR = Path("processed_videos")
UPLOAD_FOLDER = Path("uploads")
DEFAULT_BASELINE_PATH = Path("baseline.parquet")

for folder in (TEMP_DIR, OUTPUT_DIR, PROCESSED_DIR, UPLOAD_FOLDER):
    folder.mkdir(parents=True, exist_ok=True)


class SessionStore:
    """Almacena en memoria las metricas por sesion."""

    def __init__(self):
        self._sessions = {}

    def ensure(self, session_id: Optional[str] = None) -> str:
        session_id = session_id or uuid.uuid4().hex
        self._sessions.setdefault(session_id, [])
        return session_id

    def extend(self, session_id: str, rows):
        if not rows:
            return
        bucket = self._sessions.setdefault(session_id, [])
        bucket.extend(rows)

    def get(self, session_id: str):
        return list(self._sessions.get(session_id, []))

    def stats(self):
        return {sid: len(rows) for sid, rows in self._sessions.items()}


def _write_metrics(session_id: str, rows):
    if not rows:
        return None

    df = pd.DataFrame(rows)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    output_file = PROCESSED_DIR / f"{session_id}_{timestamp}.parquet"
    df.to_parquet(output_file, index=False)
    return output_file


def _summarize_feedback(feedback_log):
    if not feedback_log:
        return ["Sin observaciones relevantes. Buen trabajo."]

    counter = Counter(msg for msg in feedback_log if msg)
    top = counter.most_common(5)
    summary = [f"{msg} (x{count})" for msg, count in top]
    return summary


def _render_summary_frame(base_frame, summary_lines):
    if base_frame is None or base_frame.size == 0:
        base_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    summary_frame = base_frame.copy()
    overlay = summary_frame.copy()
    cv2.rectangle(overlay, (10, 10), (summary_frame.shape[1] - 10, summary_frame.shape[0] - 10), (0, 0, 0), -1)
    alpha = 0.6
    summary_frame = cv2.addWeighted(overlay, alpha, summary_frame, 1 - alpha, 0)

    cv2.putText(
        summary_frame,
        "Resumen del feedback",
        (40, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )

    y = 110
    for line in summary_lines:
        cv2.putText(
            summary_frame,
            f"- {line}",
            (40, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        y += 40

    return summary_frame


def _encode_frame_to_base64(frame):
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        return None
    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def _persist_session_file(session_id: str, filename: Optional[str] = None):
    rows = session_store.get(session_id)
    if not rows:
        return None, 0

    if filename:
        safe_name = Path(filename).name
        target = PROCESSED_DIR / safe_name
    else:
        target = PROCESSED_DIR / f"{session_id}_session.parquet"

    pd.DataFrame(rows).to_parquet(target, index=False)
    return target, len(rows)


session_store = SessionStore()
tracker = BoxingJabTracker(baseline=None)
baseline_data = None


def _load_initial_baseline():
    global baseline_data
    if not DEFAULT_BASELINE_PATH.exists():
        logger.info("No se encontro baseline inicial en %s", DEFAULT_BASELINE_PATH)
        return
    try:
        baseline_data = pd.read_parquet(DEFAULT_BASELINE_PATH)
        tracker.set_baseline(baseline_data)
        logger.info("Baseline cargado automaticamente desde %s", DEFAULT_BASELINE_PATH)
    except Exception as exc:
        logger.warning("No se pudo cargar el baseline inicial: %s", exc)


_load_initial_baseline()


@app.post("/load_baseline")
async def load_baseline(file: UploadFile = File(...)):
    """Carga un baseline (parquet) y actualiza el tracker."""
    global baseline_data
    try:
        file_path = UPLOAD_FOLDER / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        df = pd.read_parquet(file_path)
        baseline_data = df
        tracker.set_baseline(baseline_data)
        if file_path.exists():
            file_path.unlink()
        return {"status": "baseline_loaded", "rows": len(df)}
    except Exception as exc:
        logger.exception("Error al cargar el baseline: %s", exc)
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/upload_video")
async def upload_video(
    file: UploadFile = File(...),
    session_id: Optional[str] = Query(
        default=None, description="ID de sesion existente (opcional)"
    ),
):
    """Procesa un video de jab, genera feedback visual y guarda metricas."""
    try:
        session_id = session_store.ensure(session_id)
        raw_path = UPLOAD_FOLDER / file.filename
        with open(raw_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        processed_filename = f"processed_{Path(file.filename).stem}.mp4"
        processed_path = OUTPUT_DIR / processed_filename

        cap = cv2.VideoCapture(str(raw_path))
        if not cap.isOpened():
            if raw_path.exists():
                raw_path.unlink()
            return JSONResponse({"error": "No se pudo abrir el video"}, status_code=400)

        fps = cap.get(cv2.CAP_PROP_FPS) or tracker.DEFAULT_FPS
        tracker.set_fps(fps)
        tracker.reset_state()

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        writer = cv2.VideoWriter(
            str(processed_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )

        metrics_buffer = []
        feedback_log = []
        frame_id = 0
        last_frame = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            overlay_frame, features, tracker_feedback, _ = tracker.process_frame(frame)
            frame_to_write = overlay_frame if overlay_frame is not None else frame

            writer.write(frame_to_write)
            last_frame = frame_to_write

            if features:
                enriched = dict(features)
                enriched["session_id"] = session_id
                enriched["baseline_used"] = baseline_data is not None
                metrics_buffer.append(enriched)
            if tracker_feedback:
                feedback_log.append(tracker_feedback)

            frame_id += 1

        summary_lines = _summarize_feedback(feedback_log)
        summary_frame = _render_summary_frame(last_frame, summary_lines)
        summary_repeat = max(1, int(fps))
        for _ in range(summary_repeat):
            writer.write(summary_frame)

        cap.release()
        writer.release()
        if raw_path.exists():
            raw_path.unlink()

        session_store.extend(session_id, metrics_buffer)
        metrics_path = _write_metrics(session_id, metrics_buffer)
        session_file, session_rows = _persist_session_file(session_id)

        headers = {
            "X-Frames-Analyzed": str(frame_id),
            "X-Baseline-Used": str(baseline_data is not None),
            "X-Session-Id": session_id,
            "X-Feedback-Summary": json.dumps(summary_lines),
        }

        if metrics_path:
            headers["X-Metrics-File"] = str(metrics_path)
        if session_file:
            headers["X-Session-File"] = str(session_file)
            headers["X-Session-Rows"] = str(session_rows)

        return FileResponse(
            processed_path,
            media_type="video/mp4",
            filename=processed_filename,
            headers=headers,
        )

    except Exception as exc:
        logger.exception("Error al procesar el video: %s", exc)
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.websocket("/ws/jab")
async def jab_websocket(websocket: WebSocket):
    """Canal WebSocket para feedback en streaming."""
    await websocket.accept()
    ws_tracker = BoxingJabTracker(baseline=baseline_data)
    ws_tracker.reset_state()
    baseline_ref = baseline_data
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

            if baseline_data is not baseline_ref:
                baseline_ref = baseline_data
                ws_tracker.set_baseline(baseline_ref)

            try:
                frame_bytes = base64.b64decode(frame_b64)
                np_frame = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
            except Exception:
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
                cv2.putText(
                    output_frame,
                    display_feedback,
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )

            encoded = _encode_frame_to_base64(output_frame)
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
    except Exception as exc:
        logger.exception("Error en WebSocket: %s", exc)
        await websocket.close(code=1011, reason=str(exc))


@app.post("/save_session")
async def save_session(
    session_id: str = Query(..., description="Sesion a guardar"),
    filename: Optional[str] = Query(None, description="Nombre del archivo parquet"),
):
    """Guarda la sesion especificada en un archivo parquet."""
    session_file, row_count = _persist_session_file(session_id, filename)
    if not session_file:
        return JSONResponse(
            {"error": "No hay datos para la sesion solicitada"},
            status_code=400,
        )

    return {"status": "ok", "file": str(session_file), "rows": row_count}


@app.get("/status")
async def status():
    return {
        "success": True,
        "baseline_loaded": baseline_data is not None,
        "sessions": session_store.stats(),
    }


def _cleanup_folder(folder: Path):
    count = 0
    for entry in folder.glob("*"):
        if entry.is_file():
            entry.unlink()
            count += 1
    return count


@app.delete("/cleanup")
async def cleanup_files():
    """Limpia archivos temporales, procesados y subidos."""
    deleted = {
        "temp_files_deleted": _cleanup_folder(TEMP_DIR),
        "output_files_deleted": _cleanup_folder(OUTPUT_DIR),
        "uploads_deleted": _cleanup_folder(UPLOAD_FOLDER),
        "metrics_deleted": _cleanup_folder(PROCESSED_DIR),
    }
    return {"message": "Archivos limpiados", **deleted}
