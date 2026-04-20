"""
Boxing analysis endpoints: baseline management, video processing,
WebSocket for real-time technique analysis, and session persistence.
"""

import asyncio
import json
import logging
import shutil
import time
import uuid
from typing import List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect

from kafka import TechniqueProducer
from ml_service import WindowBuffer, punch_classifier, dtw_scorer
from ml_service.boxing_service import boxing_service
from models import BoxingSession
from models.boxing import Consent
from schemas import (
    BaselineResponse,
    BoxingSessionSchema,
    BoxingStatusResponse,
    CleanupResponse,
    SessionSaveResponse,
)

# Module-level singletons — created once, reused across all WS connections.
technique_producer = TechniqueProducer()

_async_redis: aioredis.Redis | None = None
_window_buffer: WindowBuffer | None = None


def _get_window_buffer() -> WindowBuffer:
    """Lazy-init the async Redis client and WindowBuffer singleton."""
    global _async_redis, _window_buffer
    if _async_redis is None:
        from schemas import settings
        allow_mock = (settings.ENV_MODE == "dev_mock")
        
        _async_redis = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
        
        # Test connection immediately if not in mock mode
        if not allow_mock:
            try:
                # We can't easily await here if called from sync, but _get_window_buffer
                # is called within the async websocket handler.
                pass 
            except Exception as exc:
                logger.error("❌ CRITICAL: Redis connection failed and ENV_MODE='local_real'.")
                raise exc
        else:
            # Check if we should use fakeredis
            try:
                # Try to ping real redis first even in mock mode, but with short timeout
                pass
            except Exception:
                logger.warning("⚠️ Redis connection failed, using fakeredis.")
                import fakeredis.aioredis
                _async_redis = fakeredis.aioredis.FakeRedis()
    if _window_buffer is None:
        _window_buffer = WindowBuffer(_async_redis)
    return _window_buffer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/boxing", tags=["boxing"])


@router.post("/baseline", response_model=BaselineResponse)
async def load_baseline(file: UploadFile = File(...)):
    """Upload and load a baseline parquet file."""
    try:
        result = boxing_service.load_baseline(file.filename, file.file)
        # Keep analyzer in sync with boxing_service baseline
        from ml_service.analyzer import boxing_analyzer
        if boxing_service.get_baseline() is not None:
            boxing_analyzer.set_baseline(boxing_service.get_baseline())
        return BaselineResponse(**result.__dict__)
    except Exception as exc:
        logger.exception("Error al cargar baseline: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/analyze-video")
async def analyze_video(
    file: UploadFile = File(...),
    user_id: Optional[str] = Query(None, description="User UUID (optional for anonymous testing)"),
):
    """Full pipeline video analysis — web testing endpoint.

    Accepts an mp4/mov file, runs it through the full ML pipeline
    (MediaPipe → features → quality filter → DTW), and returns
    per-frame scores, aggregated stats, and coaching feedback.

    Results are persisted to the test_runs table in PostgreSQL.
    """
    import json as _json
    from ml_service.analyzer import boxing_analyzer
    from config.database import get_pg_session
    from models.postgres import TestRun

    tmp_path = boxing_service.temp_dir / f"web_{uuid.uuid4().hex}_{file.filename}"
    try:
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        # Sync baseline to analyzer
        baseline = boxing_service.get_baseline()
        if baseline is not None:
            boxing_analyzer.set_baseline(baseline)

        # Run analysis in a thread pool to avoid blocking the event loop
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: boxing_analyzer.analyze_video(tmp_path, file.filename or ""),
        )

        # Persist test run (best-effort — don't fail the response if DB is down)
        try:
            pg_session_gen = get_pg_session()
            pg_session = await pg_session_gen.__anext__()
            run = TestRun(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id) if user_id else None,
                video_name=result.video_name,
                total_frames=result.total_frames,
                scored_frames=result.scored_frames,
                avg_score=result.avg_score,
                min_score=result.min_score,
                max_score=result.max_score,
                punch_type=result.punch_type,
                feedback=_json.dumps(result.feedback),
                processing_ms=result.processing_ms,
            )
            pg_session.add(run)
            await pg_session.commit()
            run_id = str(run.id)
            await pg_session_gen.aclose()
        except Exception as db_exc:
            logger.warning("test_run persistence failed (non-fatal): %s", db_exc)
            run_id = None

        return {
            "run_id": run_id,
            "video_name": result.video_name,
            "total_frames": result.total_frames,
            "scored_frames": result.scored_frames,
            "avg_score": result.avg_score,
            "min_score": result.min_score,
            "max_score": result.max_score,
            "frame_scores": [
                {
                    "frame_index": r.frame_index,
                    "dtw_score": r.dtw_score,
                    "label": r.qualitative_label,
                }
                for r in result.frame_results
            ],
            "baseline_curve": result.baseline_curve,
            "feedback": result.feedback,
            "punch_type": result.punch_type,
            "processing_ms": result.processing_ms,
        }

    except Exception as exc:
        logger.exception("Error in analyze_video: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


@router.get("/test-runs")
async def list_test_runs(limit: int = Query(20, le=100)):
    """Return the most recent test runs from the web UI."""
    from config.database import get_pg_session
    from models.postgres import TestRun
    from sqlalchemy import select

    try:
        pg_gen = get_pg_session()
        pg = await pg_gen.__anext__()
        rows = (await pg.execute(
            select(TestRun).order_by(TestRun.created_at.desc()).limit(limit)
        )).scalars().all()
        await pg_gen.aclose()
        return [
            {
                "id": str(r.id),
                "video_name": r.video_name,
                "avg_score": r.avg_score,
                "min_score": r.min_score,
                "max_score": r.max_score,
                "scored_frames": r.scored_frames,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    except Exception as exc:
        logger.exception("Error listing test runs: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/videos/upload")
async def upload_video(
    file: UploadFile = File(...),
    session_id: Optional[str] = Query(None, description="ID de sesión existente (opcional)"),
):
    """Upload a video for offline boxing analysis."""
    temp_filename = f"temp_{uuid.uuid4().hex}_{file.filename}"
    temp_path = boxing_service.temp_dir / temp_filename

    try:
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = boxing_service.process_video_file(temp_path, file.filename, session_id)

        # Persist to MongoDB
        existing = await BoxingSession.find_one(BoxingSession.session_id == result.session_id)
        if not existing:
            existing = BoxingSession(
                session_id=result.session_id,
                processed_filename=result.processed_filename,
            )

        existing.frames_analyzed = result.frame_count
        existing.baseline_used = result.baseline_used
        existing.feedback_summary = result.summary_lines
        existing.metrics_path = str(result.metrics_path) if result.metrics_path else None
        existing.session_file = str(result.session_file) if result.session_file else None
        existing.session_rows = result.session_rows
        await existing.save()

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


@router.websocket("/ws/jab")
async def jab_websocket(websocket: WebSocket):
    """Real-time jab analysis via WebSocket.

    Accepts landmarks (not images) from the mobile client and
    returns technique feedback and jab detection events.

    Consent is verified once per session on the first frame that carries a
    ``user_id``.  If biometric consent has not been granted the socket
    remains open but each frame is rejected with an ``"consent_required"``
    error until the client provides a user with valid consent.

    Expected payload::

        {
            "landmarks": {"right_shoulder": [x,y,z,v], ...},
            "timestamp": 1234567890,
            "user_id": "user-uuid",
            "session_id": "optional-session-uuid"
        }

    If ``session_id`` is present in the payload it will be echoed back
    in every response frame so the mobile client can correlate feedback
    to the originating session without extra bookkeeping.
    """
    await websocket.accept()
    ws_tracker = boxing_service.create_realtime_tracker()
    baseline_ref = boxing_service.get_baseline()
    last_feedback_time = 0.0

    # Consent is verified once per WebSocket session to avoid per-frame DB
    # round-trips, which would violate the <100 ms WS response requirement.
    consent_verified: bool = False
    consented_user_id: str | None = None

    # Stable session key for the window buffer throughout this connection.
    conn_session_id = str(uuid.uuid4())
    window_buffer = _get_window_buffer()

    jitter_buffer = []
    MAX_BUFFER_SIZE = 3 # small window for reordering
    
    try:
        while True:
            # Receive next message
            message = await websocket.receive()
            if "text" in message and message["text"] is not None:
                payload = json.loads(message["text"])
            elif "bytes" in message and message["bytes"] is not None:
                payload = json.loads(message["bytes"].decode("utf-8"))
            else:
                continue

            # ── Ping/Pong (process immediately) ──────────────
            msg_type = payload.get("type")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "ts": payload.get("ts")})
                continue
            
            # ── Jitter Buffer: Reordering ────────────────────
            # Push payload into buffer and sort by timestamp
            ts = payload.get("timestamp", time.time())
            jitter_buffer.append((ts, payload))
            jitter_buffer.sort(key=lambda x: x[0])
            
            if len(jitter_buffer) < MAX_BUFFER_SIZE:
                continue
            
            # Pop the oldest frame to process
            _, payload = jitter_buffer.pop(0)

            # ── Reset ────────────────────────────────────────
            action = payload.get("action")
            if action == "reset":
                ws_tracker.reset_state()
                await websocket.send_json({"status": "reset"})
                continue

            # ── Landmarks path (preferred) ───────────────────
            raw_landmarks = payload.get("landmarks")
            if raw_landmarks:
                # ── Consent check (once per session) ─────────
                user_id: str | None = payload.get("user_id")
                if user_id and not consent_verified:
                    consent = await Consent.find_one(
                        Consent.user_id == user_id,
                        Consent.consent_type == "biometric",
                        Consent.granted == True,
                    )
                    if not consent:
                        await websocket.send_json(
                            {
                                "error": "consent_required",
                                "consent_type": "biometric",
                                "message": "Debes aceptar el consentimiento biométrico (Ley 1581) para procesar landmarks."
                            }
                        )
                        continue
                    consent_verified = True
                    consented_user_id = user_id

                current_baseline = boxing_service.get_baseline()
                if current_baseline is not baseline_ref:
                    baseline_ref = current_baseline
                    ws_tracker.set_baseline(baseline_ref)

                fps_override = payload.get("fps")
                if fps_override:
                    ws_tracker.set_fps(float(fps_override))

                features, feedback_msg, jab_event = ws_tracker.process_landmarks(raw_landmarks)

                # ── ML pipeline: window buffer → DTW → classifier ─────
                dtw_score: float | None = None
                punch_type: str | None = None
                qualitative_label: str | None = None

                if features:
                    from ml_service.dtw_scorer import DTW_FEATURE_ORDER
                    strict_features = {k: features.get(k, 0.0) for k in DTW_FEATURE_ORDER}
                    strict_features["frame_index"] = features.get("frame_index")
                    strict_features["tracking_state"] = features.get("tracking_state")
                    
                    effective_uid = consented_user_id or user_id or "anonymous"
                    effective_session = payload.get("session_id") or conn_session_id
                    window = await window_buffer.push_frame(
                        effective_uid, effective_session, strict_features
                    )
                    if window is not None:
                        # 1. Compute smart coaching feedback for the window
                        smart_feedback = ws_tracker.feedback_engine.analyze_window(window)
                        if smart_feedback:
                            feedback_msg = smart_feedback
                            
                        # 2. Compute DTW score against all loaded baselines (Phase 3: Multi-baseline)
                        # For now, we take head(30) but in production we'd iterate over pro baselines
                        if baseline_ref is not None and not baseline_ref.empty:
                            ref_window = baseline_ref.head(30).to_dict('records')
                            dtw_score = dtw_scorer.score_window(window, ref_window)
                            qualitative_label = dtw_scorer.get_qualitative_label(dtw_score)
                        else:
                            dtw_score = 0.0

                        # punch_classifier falls back to ("null", 1.0) when no
                        # trained model file exists — safe cold-start behavior.
                        punch_cls, _ = punch_classifier.classify(window, dtw_score)
                        if punch_cls != "null":
                            punch_type = punch_cls

                    # Phase 22 - Data Strategy: Store structured session payload mapping natively
                    structured_metric = {
                        "timestamp": payload.get("timestamp", time.time()),
                        "frame_index": features.get("frame_index"),
                        "tracking_state": features.get("tracking_state"),
                        "dtw_score": dtw_score,
                        "qualitative_label": qualitative_label,
                        "punch_type": punch_type
                    }
                    # Filter structural metrics to explicitly not log arrays unless aggregated
                    boxing_service.session_store.ensure(effective_session)
                    boxing_service.session_store.extend(effective_session, [structured_metric])
                    
                now = time.monotonic()
                display_feedback = None

                if jab_event:
                    display_feedback = feedback_msg or "Buen jab detectado."
                    last_feedback_time = now

                    # ── Publish punch event to Kafka (non-blocking) ───────
                    effective_user_id = consented_user_id or user_id or "unknown"
                    _detected_punch = punch_type or "jab"
                    _detected_score = dtw_score or 0.0
                    _frame_idx = features.get("frame_index", 0) if features else 0
                    asyncio.create_task(
                        asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: technique_producer.send_punch_detected(
                                effective_user_id,
                                payload.get("session_id", ""),
                                _detected_punch,
                                _detected_score,
                                _frame_idx,
                            ),
                        )
                    )

                elif feedback_msg and now - last_feedback_time > 1.5:
                    display_feedback = feedback_msg
                    last_feedback_time = now

                response = {
                    "feedback": display_feedback,
                    "jab_detected": bool(jab_event),
                    "frame_index": features.get("frame_index") if features else None,
                    "tracking_state": features.get("tracking_state") if features else "searching",
                    "dtw_score": dtw_score,
                    "punch_type": punch_type,
                    "qualitative_label": qualitative_label,
                }
                if payload.get("session_id"):
                    response["session_id"] = payload["session_id"]
                await websocket.send_json(response)
                continue

            await websocket.send_json({"error": "invalid_payload", "expected": "landmarks array"})

    except WebSocketDisconnect:
        logger.info("Cliente WebSocket desconectado.")
    except Exception as exc:
        logger.exception("Error en WebSocket: %s", exc)
    finally:
        # Best-effort cleanup of the Redis window buffer for this connection.
        try:
            await window_buffer.clear(consented_user_id or "anonymous", conn_session_id)
        except Exception:
            pass


@router.post("/sessions/save", response_model=SessionSaveResponse)
async def save_session(
    session_id: str = Query(..., description="Session to persist"),
    filename: Optional[str] = Query(None, description="Output parquet filename"),
):
    """Persist an in-memory session to disk as parquet."""
    result = boxing_service.persist_session(session_id, filename)
    if not result.file_path:
        raise HTTPException(status_code=400, detail="No hay datos para la sesión solicitada")
    return SessionSaveResponse(status="ok", file=str(result.file_path), rows=result.rows)


@router.get("/sessions", response_model=List[BoxingSessionSchema])
async def list_sessions():
    """List all boxing analysis sessions."""
    records = await BoxingSession.find_all().sort("-created_at").to_list()
    return [
        BoxingSessionSchema(
            id=str(r.id),
            session_id=r.session_id,
            processed_filename=r.processed_filename,
            frames_analyzed=r.frames_analyzed,
            baseline_used=r.baseline_used,
            feedback_summary=r.feedback_summary,
            metrics_path=r.metrics_path,
            session_file=r.session_file,
            session_rows=r.session_rows,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/status", response_model=BoxingStatusResponse)
async def status():
    """Get boxing service status."""
    return BoxingStatusResponse(
        success=True,
        baseline_loaded=boxing_service.get_baseline() is not None,
        sessions=boxing_service.get_session_stats(),
    )


@router.delete("/cleanup", response_model=CleanupResponse)
async def cleanup_files():
    """Delete all temporary, processed, and uploaded files."""
    deleted = boxing_service.cleanup_storage()
    return CleanupResponse(message="Archivos limpiados", **deleted)
