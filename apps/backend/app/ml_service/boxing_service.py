import base64
import json
import logging
import shutil
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd

from .boxing_jab_tracker import BoxingJabTracker

logger = logging.getLogger(__name__)


@dataclass
class BaselineLoadResult:
    status: str
    rows: int


@dataclass
class SessionPersistResult:
    file_path: Optional[Path]
    rows: int


@dataclass
class VideoProcessingResult:
    processed_path: Path
    processed_filename: str
    session_id: str
    frame_count: int
    baseline_used: bool
    summary_lines: List[str]
    metrics_path: Optional[Path]
    session_file: Optional[Path]
    session_rows: int

    def headers(self) -> Dict[str, str]:
        headers = {
            "X-Frames-Analyzed": str(self.frame_count),
            "X-Baseline-Used": str(self.baseline_used),
            "X-Session-Id": self.session_id,
            "X-Feedback-Summary": json.dumps(self.summary_lines),
        }
        if self.metrics_path:
            headers["X-Metrics-File"] = str(self.metrics_path)
        if self.session_file:
            headers["X-Session-File"] = str(self.session_file)
            headers["X-Session-Rows"] = str(self.session_rows)
        return headers


class SessionStore:
    """Stores in-memory metrics per session, used before persisting to disk."""

    def __init__(self):
        self._sessions: Dict[str, List[dict]] = {}

    def ensure(self, session_id: Optional[str] = None) -> str:
        session_id = session_id or uuid.uuid4().hex
        self._sessions.setdefault(session_id, [])
        return session_id

    def extend(self, session_id: str, rows: List[dict]) -> None:
        if not rows:
            return
        bucket = self._sessions.setdefault(session_id, [])
        bucket.extend(rows)

    def get(self, session_id: str) -> List[dict]:
        return list(self._sessions.get(session_id, []))

    def stats(self) -> Dict[str, int]:
        return {sid: len(rows) for sid, rows in self._sessions.items()}


class BoxingAnalyticsService:
    """High-level orchestration layer around boxing analysis utilities."""

    def __init__(
        self,
        temp_dir: Path | str = Path("videos/temp"),
        output_dir: Path | str = Path("videos/output"),
        processed_dir: Path | str = Path("processed_videos"),
        upload_dir: Path | str = Path("uploads"),
        baseline_path: Path | str = Path("baseline.parquet"),
    ):
        self.temp_dir = Path(temp_dir)
        self.output_dir = Path(output_dir)
        self.processed_dir = Path(processed_dir)
        self.upload_dir = Path(upload_dir)
        self.default_baseline_path = Path(baseline_path)

        self.session_store = SessionStore()
        self.tracker = BoxingJabTracker(baseline=None)
        self.baseline_data: Optional[pd.DataFrame] = None

        self._ensure_directories()
        self._load_initial_baseline()

    def _ensure_directories(self) -> None:
        for folder in (self.temp_dir, self.output_dir, self.processed_dir, self.upload_dir):
            folder.mkdir(parents=True, exist_ok=True)

    def _load_initial_baseline(self) -> None:
        if not self.default_baseline_path.exists():
            logger.info("No se encontro baseline inicial en %s", self.default_baseline_path)
            return

        try:
            df = pd.read_parquet(self.default_baseline_path)
            self.baseline_data = df
            self.tracker.set_baseline(df)
            logger.info("Baseline cargado automaticamente desde %s", self.default_baseline_path)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("No se pudo cargar el baseline inicial: %s", exc)

    # ------------------------------------------------------------------
    # Baseline management
    # ------------------------------------------------------------------
    def load_baseline(self, filename: str, data_stream) -> BaselineLoadResult:
        """Persist an uploaded baseline to disk and load it into memory."""
        target_path = self.upload_dir / filename
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(data_stream, buffer)

        try:
            df = pd.read_parquet(target_path)
            self.baseline_data = df
            self.tracker.set_baseline(df)
            return BaselineLoadResult(status="baseline_loaded", rows=len(df))
        finally:
            if target_path.exists():
                target_path.unlink()

    def get_baseline(self) -> Optional[pd.DataFrame]:
        return self.baseline_data

    # ------------------------------------------------------------------
    # Video processing
    # ------------------------------------------------------------------
    def process_video_file(
        self,
        video_path: Path,
        original_filename: str,
        session_id: Optional[str] = None,
    ) -> VideoProcessingResult:
        session_id = self.session_store.ensure(session_id)
        processed_filename = f"processed_{Path(original_filename).stem}.mp4"
        processed_path = self.output_dir / processed_filename

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError("No se pudo abrir el video")

        tracker = BoxingJabTracker(baseline=self.baseline_data)
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

        metrics_buffer: List[dict] = []
        feedback_log: List[str] = []
        frame_id = 0
        last_frame = None
        summary_lines: List[str] = []

        try:
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
                    enriched["baseline_used"] = self.baseline_data is not None
                    metrics_buffer.append(enriched)

                if tracker_feedback:
                    feedback_log.append(tracker_feedback)

                frame_id += 1

            summary_lines = self._summarize_feedback(feedback_log)
            summary_frame = self._render_summary_frame(last_frame, summary_lines)
            summary_repeat = max(1, int(fps))
            for _ in range(summary_repeat):
                writer.write(summary_frame)
        finally:
            cap.release()
            writer.release()
            if video_path.exists():
                video_path.unlink()

        self.session_store.extend(session_id, metrics_buffer)
        metrics_path = self._write_metrics(session_id, metrics_buffer)
        session_file, session_rows = self._persist_session_file(session_id)

        return VideoProcessingResult(
            processed_path=processed_path,
            processed_filename=processed_filename,
            session_id=session_id,
            frame_count=frame_id,
            baseline_used=self.baseline_data is not None,
            summary_lines=summary_lines,
            metrics_path=metrics_path,
            session_file=session_file,
            session_rows=session_rows,
        )

    def get_session_stats(self) -> Dict[str, int]:
        return self.session_store.stats()

    def persist_session(self, session_id: str, filename: Optional[str] = None) -> SessionPersistResult:
        session_file, rows = self._persist_session_file(session_id, filename)
        return SessionPersistResult(file_path=session_file, rows=rows)

    def cleanup_storage(self) -> Dict[str, int]:
        deleted = {
            "temp_files_deleted": self._cleanup_folder(self.temp_dir),
            "output_files_deleted": self._cleanup_folder(self.output_dir),
            "uploads_deleted": self._cleanup_folder(self.upload_dir),
            "metrics_deleted": self._cleanup_folder(self.processed_dir),
        }
        return deleted

    def create_realtime_tracker(self) -> BoxingJabTracker:
        tracker = BoxingJabTracker(baseline=self.baseline_data)
        tracker.reset_state()
        return tracker

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _write_metrics(self, session_id: str, rows: List[dict]) -> Optional[Path]:
        if not rows:
            return None

        df = pd.DataFrame(rows)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        output_file = self.processed_dir / f"{session_id}_{timestamp}.parquet"
        df.to_parquet(output_file, index=False)
        return output_file

    @staticmethod
    def _summarize_feedback(feedback_log: List[str]) -> List[str]:
        if not feedback_log:
            return ["Sin observaciones relevantes. Buen trabajo."]

        counter = Counter(msg for msg in feedback_log if msg)
        top = counter.most_common(5)
        return [f"{msg} (x{count})" for msg, count in top]

    @staticmethod
    def _render_summary_frame(base_frame, summary_lines: List[str]):
        if base_frame is None or base_frame.size == 0:
            base_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        summary_frame = base_frame.copy()
        overlay = summary_frame.copy()
        cv2.rectangle(
            overlay,
            (10, 10),
            (summary_frame.shape[1] - 10, summary_frame.shape[0] - 10),
            (0, 0, 0),
            -1,
        )
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

    def encode_frame_to_base64(self, frame) -> Optional[str]:
        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            return None
        return base64.b64encode(buffer.tobytes()).decode("utf-8")

    def _persist_session_file(self, session_id: str, filename: Optional[str] = None) -> Tuple[Optional[Path], int]:
        rows = self.session_store.get(session_id)
        if not rows:
            return None, 0

        if filename:
            safe_name = Path(filename).name
            target = self.processed_dir / safe_name
        else:
            target = self.processed_dir / f"{session_id}_session.parquet"

        pd.DataFrame(rows).to_parquet(target, index=False)
        return target, len(rows)

    @staticmethod
    def _cleanup_folder(folder: Path) -> int:
        count = 0
        for entry in folder.glob("*"):
            if entry.is_file():
                entry.unlink()
                count += 1
        return count

    def decode_frame_payload(self, payload: str) -> Optional[np.ndarray]:
        try:
            frame_bytes = base64.b64decode(payload)
            np_frame = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
            return frame
        except Exception:  # pragma: no cover - defensive
            return None

    def annotate_feedback_on_frame(self, frame, feedback: str) -> None:
        cv2.putText(
            frame,
            feedback,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )


# Singleton-like instance reused across routers
boxing_service = BoxingAnalyticsService()
