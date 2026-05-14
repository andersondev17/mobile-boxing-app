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
from pathlib import Path
from typing import List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

from services.events.technique_producer import TechniqueProducer
from services.ml import WindowBuffer, punch_classifier
from services.ml.core.dtw_scorer import score_window, get_qualitative_label
from services.ml.orchestrator import boxing_service
from models import BoxingSession
from models.postgres import Consent as PostgresConsent
from sqlalchemy import select

from app.config.database import pg_session
from app.schemas import (
    BaselineResponse,
    BoxingSessionSchema,
    BoxingStatusResponse,
    CleanupResponse,
    SessionSaveResponse,
    MultiBaselineRequest,
    MultiBaselineResponse,
)

def _clerk_id_to_uuid(clerk_id: str) -> uuid.UUID:
    """Convert Clerk user ID (user_1234567890abcdef) to UUID format."""
    logger.info(f"[DEBUG] _clerk_id_to_uuid called with: '{clerk_id}' (type: {type(clerk_id)})")
    
    # Handle None or empty values
    if not clerk_id:
        logger.error("[DEBUG] Empty or None user_id provided")
        raise ValueError("user_id cannot be empty")
    
    # If it's already a UUID, return as-is
    try:
        result = uuid.UUID(clerk_id)
        logger.info(f"[DEBUG] Successfully parsed as UUID: {result}")
        return result
    except ValueError:
        logger.info(f"[DEBUG] Not a valid UUID format, trying Clerk conversion...")
        pass
    
    # Convert Clerk user ID (user_1234567890abcdef) to UUID format
    # Remove 'user_' prefix and pad/truncate to create a valid UUID
    clean_id = clerk_id.replace('user_', '')
    logger.info(f"[DEBUG] After removing 'user_' prefix: '{clean_id}'")
    
    # Handle various formats
    if len(clean_id) < 32:
        padded_id = clean_id.ljust(32, '0')[:32]
        logger.info(f"[DEBUG] Padded to 32 chars: '{padded_id}'")
    else:
        padded_id = clean_id[:32]
        logger.info(f"[DEBUG] Truncated to 32 chars: '{padded_id}'")
    
    formatted_uuid = f"{padded_id[0:8]}-{padded_id[8:12]}-{padded_id[12:16]}-{padded_id[16:20]}-{padded_id[20:32]}"
    logger.info(f"[DEBUG] Formatted UUID: '{formatted_uuid}'")
    
    try:
        result = uuid.UUID(formatted_uuid)
        logger.info(f"[DEBUG] Successfully created UUID: {result}")
        return result
    except Exception as e:
        logger.error(f"[DEBUG] Failed to create UUID: {e}")
        raise ValueError(f"Cannot convert user_id '{clerk_id}' to UUID: {e}")

# Module-level singletons — created once, reused across all WS connections.
technique_producer = TechniqueProducer()

_async_redis: aioredis.Redis | None = None
_window_buffer: WindowBuffer | None = None

# Holds references to fire-and-forget asyncio Tasks so they are not GC'd
# before completion.  Each task removes itself via a done-callback.
_pending_tasks: set[asyncio.Task] = set()


def _get_window_buffer() -> WindowBuffer:
    """Lazy-init the async Redis client and WindowBuffer singleton."""
    global _async_redis, _window_buffer
    if _async_redis is None:
        from app.schemas import settings
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

# Schema for punch type confirmation
class ConfirmPunchTypeRequest(BaseModel):
    session_id: str
    confirmed_type: str  # "jab" | "cross" | "hook" | "uppercut"
    user_id: Optional[str] = None

router = APIRouter(prefix="/boxing", tags=["boxing"])


@router.post("/baseline", response_model=BaselineResponse)
async def load_baseline(file: UploadFile = File(...)):
    """Upload and load a baseline parquet file."""
    try:
        result = boxing_service.load_baseline(file.filename, file.file)
        # Keep analyzer in sync with boxing_service baseline
        from services.ml.core.analyzer import boxing_analyzer
        if boxing_service.get_baseline() is not None:
            boxing_analyzer.set_baseline(boxing_service.get_baseline())
        return BaselineResponse(**result.__dict__)
    except Exception as exc:
        logger.exception("Error al cargar baseline: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


def detect_punch_type(filename: str) -> str:
    """Detect punch type from filename."""
    if not filename:
        return "jab"  # default
    
    filename_lower = filename.lower()
    if "jab" in filename_lower:
        return "jab"
    elif "cross" in filename_lower:
        return "cross"
    elif "gancho" in filename_lower or "hook" in filename_lower:
        return "hook"
    elif "uppercut" in filename_lower:
        return "uppercut"
    else:
        return "jab"  # default


@router.websocket("/ws/jab")
async def jab_websocket(websocket: WebSocket):
    """Real-time jab analysis via WebSocket.

    Accepts landmarks (not images) from mobile client and
    returns technique feedback and jab detection events.

    Consent is verified once per session on first frame that carries a
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

    If ``session_id`` is present in payload it will be echoed back
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

    # Stable session key for window buffer throughout this connection.
    conn_session_id = str(uuid.uuid4())
    window_buffer = _get_window_buffer()

    jitter_buffer = []
    MAX_BUFFER_SIZE = 3 # small window for reordering
    MAX_QUEUE_SIZE = 10 # hard limit to avoid runaway latency
    
    # Backpressure state
    is_slowed_down = False
    last_backpressure_time = 0.0
    BACKPRESSURE_COOLDOWN = 5.0 # seconds between signaling
    
    # Connection management for proper cleanup
    connection_start_time = time.time()
    is_connected = True
    
    try:
        while True:
            # Receive next message
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break

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
            
            # --- Backpressure & Congestion Control ---
            queue_len = len(jitter_buffer)
            now_time = time.time()
            
            # 1. Signal Slow Down if queue is growing
            if queue_len > (MAX_QUEUE_SIZE // 2) and not is_slowed_down:
                if now_time - last_backpressure_time > BACKPRESSURE_COOLDOWN:
                    await websocket.send_json({"type": "slow_down"})
                    is_slowed_down = True
                    last_backpressure_time = now_time
                    logger.warning("Backpressure: Sent SLOW_DOWN to client (queue=%d)", queue_len)
            
            # 2. Hard Drop if queue is critically full
            if queue_len > MAX_QUEUE_SIZE:
                # Keep only the newest frame to recover real-time state
                jitter_buffer = jitter_buffer[-1:]
                logger.warning("Congestion: Dropped %d old frames to recover latency", queue_len - 1)
                # BUG-3 FIX: Do NOT continue — fall through to process the surviving frame
                # immediately instead of waiting for MAX_BUFFER_SIZE frames (2-3s stall).
            elif len(jitter_buffer) < MAX_BUFFER_SIZE:
                continue
            
            # Pop the oldest frame to process
            _, payload = jitter_buffer.pop(0)

            # 3. Signal Speed Up if queue is empty and we were slowed down
            if is_slowed_down and len(jitter_buffer) == 0:
                 if now_time - last_backpressure_time > BACKPRESSURE_COOLDOWN:
                    await websocket.send_json({"type": "speed_up"})
                    is_slowed_down = False
                    last_backpressure_time = now_time
                    logger.info("Backpressure: Sent SPEED_UP to client (queue empty)")

            # ── Reset ────────────────────────────────────────
            msg_type = payload.get("type")
            action = payload.get("action")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "ts": payload.get("ts")})
                continue

            if action == "reset":
                ws_tracker.reset_state()
                await websocket.send_json({"status": "reset"})
                continue

            # ── Consent granted via WS ────────────────────────
            if action == "consent_granted":
                ws_user_id = payload.get("user_id")
                ws_consent_type = payload.get("consent_type", "biometric")
                logger.info(f"[DEBUG] Consent received - user_id: {ws_user_id}, consent_type: {ws_consent_type}")
                if ws_user_id:
                    try:
                        logger.info(f"[DEBUG] Converting user_id: {ws_user_id}")
                        ws_user_uuid = _clerk_id_to_uuid(ws_user_id)
                        logger.info(f"[DEBUG] Converted to UUID: {ws_user_uuid}")
                    except Exception as e:
                        logger.error(f"[DEBUG] Conversion failed: {e}, user_id: {ws_user_id}")
                        await websocket.send_json({"error": "consent_invalid_user_id", "message": "Invalid user_id format"})
                        continue
                    async with pg_session() as db:
                        stmt = select(PostgresConsent).where(
                            PostgresConsent.user_id == ws_user_uuid,
                            PostgresConsent.consent_type == ws_consent_type,
                        )
                        result = await db.execute(stmt)
                        existing_consent = result.scalar_one_or_none()
                        if existing_consent:
                            existing_consent.granted = True
                            existing_consent.revoked_at = None
                        else:
                            db.add(PostgresConsent(
                                user_id=ws_user_uuid,
                                consent_type=ws_consent_type,
                                granted=True,
                            ))
                        await db.commit()
                    consent_verified = True
                    consented_user_id = ws_user_id
                    logger.info("Consent granted via WS for user=%s type=%s", ws_user_id, ws_consent_type)
                    await websocket.send_json({"status": "consent_accepted", "consent_type": ws_consent_type})
                else:
                    await websocket.send_json({"error": "consent_missing_user_id", "message": "user_id is required for consent"})
                continue

            # ── Frame extraction (fallback) ──────────────────
            raw_frame = payload.get("frame")
            raw_landmarks = payload.get("landmarks")
            
            if raw_frame and not raw_landmarks:
                import base64
                import cv2
                import numpy as np
                try:
                    if "," in raw_frame:
                        raw_frame = raw_frame.split(",")[1]
                    img_data = base64.b64decode(raw_frame)
                    np_arr = np.frombuffer(img_data, np.uint8)
                    frame_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    if frame_img is not None:
                        rgb = cv2.cvtColor(frame_img, cv2.COLOR_BGR2RGB)
                        # BUG-4 FIX: Run MediaPipe inference off the event loop to avoid
                        # blocking all other WebSocket clients for 50-150ms per frame.
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(None, ws_tracker.pose.process, rgb)
                        if result.pose_landmarks:
                            # BUG-2 FIX: Use named dict (same format as process_frame()) instead
                            # of an indexed list. PoseOverlay accesses landmarks.right_shoulder —
                            # indexing a list by a string key returns undefined on the client.
                            # Extract ALL landmarks that feature_extractor.py needs:
                            # nose(0), shoulders(11-12), elbows(13-14), wrists(15-16),
                            # hips(23-24), knees(25-26), ankles(27-28).
                            # Missing any of these causes features to be 0.0 → jab never triggers.
                            TARGET_INDICES = {
                                'nose': 0,
                                'left_shoulder': 11, 'right_shoulder': 12,
                                'left_elbow': 13, 'right_elbow': 14,
                                'left_wrist': 15, 'right_wrist': 16,
                                'left_hip': 23, 'right_hip': 24,
                                'left_knee': 25, 'right_knee': 26,
                                'left_ankle': 27, 'right_ankle': 28,
                            }
                            named_landmarks: dict = {}
                            for name, idx in TARGET_INDICES.items():
                                lm = result.pose_landmarks.landmark[idx]
                                named_landmarks[name] = [lm.x, lm.y, lm.z, lm.visibility]
                            raw_landmarks = named_landmarks
                except Exception as e:
                    logger.warning("Frame decode error: %s", e)

            # ── Landmarks path (preferred) ───────────────────
            if raw_landmarks:
                # ── Consent check (once per session) ─────────
                user_id: str | None = payload.get("user_id")
                logger.info(f"[DEBUG] Frame received - user_id: {user_id} (type: {type(user_id)}), consent_verified: {consent_verified}")
                
                # TEMPORARY BYPASS: Allow anonymous sessions for debugging landmarks
                # TODO: Remove this bypass once user_id format is understood
                if user_id and not consent_verified:
                    logger.warning(f"[TEMP-BYPASS] Allowing anonymous session for user_id: {user_id}")
                    consent_verified = True
                    consented_user_id = "anonymous_debug"
                    
                    # Try to convert user_id for logging purposes but don't fail
                    try:
                        logger.info(f"[DEBUG] Attempting to convert user_id: {user_id}")
                        user_uuid = _clerk_id_to_uuid(user_id)
                        logger.info(f"[DEBUG] Successfully converted to UUID: {user_uuid}")
                    except Exception as e:
                        logger.error(f"[DEBUG] User_id conversion failed (but continuing): {e}, user_id: {user_id}")
                        # Don't send error response, just continue with anonymous session
                        pass
                    
                    # Skip database consent check for now
                    logger.info("[TEMP-BYPASS] Skipping database consent check")

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
                    from services.ml.core.dtw_scorer import DTW_FEATURE_ORDER
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
                            dtw_score = score_window(window, ref_window)
                            qualitative_label = get_qualitative_label(dtw_score)
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
                    _task = asyncio.ensure_future(
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
                    _pending_tasks.add(_task)
                    _task.add_done_callback(_pending_tasks.discard)

                elif feedback_msg and now - last_feedback_time > 1.5:
                    display_feedback = feedback_msg
                    last_feedback_time = now

                response = {
                    "feedback": display_feedback,
                    "jab_detected": bool(jab_event),
                    "landmarks": raw_landmarks,
                    "frame_index": features.get("frame_index") if features else None,
                    "tracking_state": features.get("tracking_state") if features else "searching",
                }
                if payload.get("session_id"):
                    response["session_id"] = payload["session_id"]
                await websocket.send_json(response)
                continue

            if not raw_landmarks and not raw_frame:
                logger.debug("Received unknown or empty payload: %s", payload)
                continue

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
