import cv2
import numpy as np

# Lazy MediaPipe import - solutions may not be available in all MediaPipe versions
try:
    import mediapipe as mp
    # Try multiple import paths for different MediaPipe versions
    try:
        mp_pose = mp.solutions.pose
    except AttributeError:
        try:
            from mediapipe.python.solutions import pose as mp_pose
        except ImportError:
            import mediapipe.python.solutions.pose as mp_pose
except (ImportError, AttributeError):
    mp_pose = None
from dataclasses import dataclass
from typing import Union

from .feature_extractor import extract_features
from .feedback_engine import FeedbackEngine
from .frame_quality import validate_frame, smooth_features

# Named landmark keys expected by the dict-based input path.
_NAMED_TO_INDEX: dict[str, int] = {
    "nose": 0,
    "left_eye_inner": 1,
    "left_eye": 2,
    "left_eye_outer": 3,
    "right_eye_inner": 4,
    "right_eye": 5,
    "right_eye_outer": 6,
    "left_ear": 7,
    "right_ear": 8,
    "mouth_left": 9,
    "mouth_right": 10,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_pinky": 17,
    "right_pinky": 18,
    "left_index": 19,
    "right_index": 20,
    "left_thumb": 21,
    "right_thumb": 22,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
    "left_heel": 29,
    "right_heel": 30,
    "left_foot_index": 31,
    "right_foot_index": 32,
}


class _LandmarkProxy:
    """Thin proxy that exposes .x, .y, .z, .visibility from a plain dict.

    This allows landmarks received over the WebSocket (as dicts) to be passed
    directly into ``extract_features``, which expects objects with attribute
    access (matching the MediaPipe landmark interface).

    Args:
        data: Dict with at least the keys ``"x"``, ``"y"``, ``"z"``.
            An optional ``"v"`` or ``"visibility"`` key is mapped to
            ``.visibility``.  Missing keys default to ``0.0``.
    """

    __slots__ = ("x", "y", "z", "visibility")

    def __init__(self, data: dict) -> None:
        self.x: float = float(data.get("x", 0.0))
        self.y: float = float(data.get("y", 0.0))
        self.z: float = float(data.get("z", 0.0))
        # Support both "v" (mobile compact format) and "visibility" keys.
        self.visibility: float = float(
            data.get("visibility", data.get("v", 0.0))
        )


@dataclass
class JabEvent:
    frame_idx: int
    hand_speed: float = 0.0
    extension: float = 0.0
    retraction_speed: float = 0.0
    result: str = "jab_detected"


class JabTracker:
    """State-machine punch detector that works with both side-view and
    front-facing (selfie) cameras.

    Uses two complementary extension metrics:
      * **X-displacement** (``forward_extent_left/right``) — effective when the
        camera is perpendicular to the punch direction (side view).
      * **Elbow-angle extension** — camera-angle invariant; maps the elbow
        angle to a 0-1 scale where 90° (bent) → 0.0 and 180° (straight) → 1.0.
        A typical guard position reads ~0.33 (120°); a full punch reads ~0.83
        (165°).

    The detector picks whichever metric gives the stronger signal, so it
    works regardless of camera placement.
    """

    # Extension threshold: 0.65 ≈ elbow > 148° (clearly extending).
    # Speed threshold: lowered to 0.4 to accommodate lower mobile FPS.
    def __init__(self, threshold_extension=0.65, threshold_speed=0.4):
        self.threshold_extension = threshold_extension
        self.threshold_speed = threshold_speed
        self.state = "idle"
        self.jabs = []

    def reset(self):
        self.state = "idle"
        self.jabs.clear()

    def update(self, features, frame_idx):
        if not features:
            return None

        # ── Best extension across BOTH hands ──────────────────────────
        fwd_l = features.get("forward_extent_left", 0.0)
        fwd_r = features.get("forward_extent_right", 0.0)

        # Elbow-angle extension (camera-angle invariant):
        # 90° → 0.0, 180° → 1.0.  Guard ≈ 0.33, punch ≈ 0.83.
        elbow_l = features.get("elbow_angle_left", 90.0)
        elbow_r = features.get("elbow_angle_right", 90.0)
        arm_ext_l = max(0.0, (elbow_l - 90.0)) / 90.0
        arm_ext_r = max(0.0, (elbow_r - 90.0)) / 90.0

        ext = max(fwd_l, fwd_r, arm_ext_l, arm_ext_r)

        speed = features.get("hand_speed", 0.0)
        retract = features.get("retraction_speed", 0.0)

        if self.state == "idle":
            if ext > self.threshold_extension and speed > self.threshold_speed:
                self.state = "extended"
            return None

        if self.state == "extended":
            # Retraction: arm returns to guard position (ext < 0.40 ≈ elbow < 126°)
            if ext < 0.40:
                self.state = "idle"
                jab_event = JabEvent(frame_idx, speed, ext, retract)
                self.jabs.append(jab_event)
                return jab_event

        return None


class BoxingJabTracker:
    DEFAULT_FPS = 30.0

    def __init__(self, baseline=None, fps=DEFAULT_FPS):
        # Initialize MediaPipe Pose (lazy import)
        if mp_pose is None:
            raise RuntimeError("MediaPipe pose solutions not available. Please install mediapipe with: pip install mediapipe")
        self.mp_pose = mp_pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.feedback_engine = FeedbackEngine(baseline)
        self.baseline = baseline
        self.jab_tracker = JabTracker()
        self.last_jab_event = None
        self.set_fps(fps)
        self.reset_state()

    def set_baseline(self, baseline):
        self.baseline = baseline
        self.feedback_engine.set_baseline(baseline)

    def set_fps(self, fps):
        self.fps = fps if fps and fps > 0 else self.DEFAULT_FPS
        self.dt = 1.0 / self.fps

    def reset_state(self):
        self.prev_wrist_l = None
        self.prev_wrist_r = None
        self.prev_max_extent = None
        self.prev_features: dict | None = None
        self.frame_idx = 0
        self.last_jab_event = None
        self.jab_tracker.reset()

    def process_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)
        annotated = frame.copy()

        if not result.pose_landmarks:
            self.frame_idx += 1
            self.last_jab_event = None
            return annotated, None, None, None, None

        mp.solutions.drawing_utils.draw_landmarks(
            annotated,
            result.pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
        )

        landmarks = result.pose_landmarks.landmark
        features = extract_features(landmarks)

        if not features:
            self.frame_idx += 1
            self.last_jab_event = None
            return annotated, None, None, None, None

        features = self._augment_with_motion(landmarks, features)
        jab_event = self.jab_tracker.update(features, self.frame_idx)
        if jab_event:
            self.last_jab_event = jab_event

        feedback_msg = self.feedback_engine.compare_realtime(features)
        if feedback_msg is None:
            feedback_msg = self._heuristic_feedback(features, jab_event)

        # Convert landmarks to serializable list for mobile SVG
        raw_landmarks = {}
        target_indices = {
            'right_shoulder': 12, 'right_elbow': 14, 'right_wrist': 16,
            'left_shoulder': 11, 'left_elbow': 13, 'left_wrist': 15,
            'right_hip': 24, 'left_hip': 23
        }

        torso_indices = [11, 12, 23, 24]
        is_tracking_locked = all(landmarks[idx].visibility > 0.65 for idx in torso_indices)

        for name, idx in target_indices.items():
            lm = landmarks[idx]
            # MediaPipe landmarks are normalized [0, 1]. Adding visibility to index 3.
            raw_landmarks[name] = [lm.x, lm.y, lm.z, lm.visibility]

        if not is_tracking_locked:
            feedback_msg = "UBICA TU CUERPO EN EL CUADRO"
            jab_event = None

        features["tracking_state"] = "tracking" if is_tracking_locked else "searching"

        self.frame_idx += 1
        return annotated, features, feedback_msg, jab_event, raw_landmarks

    def process_landmarks(
        self,
        raw_landmarks: Union[dict, list],
    ) -> tuple[dict | None, str | None, bool]:
        """Process a single frame of landmarks received from the mobile client.

        Converts the incoming landmark payload (either a named-key dict or an
        indexed list of dicts) into proxy objects compatible with
        ``feature_extractor.extract_features``, then runs the full analysis
        pipeline: feature extraction, motion augmentation, jab tracking, and
        feedback generation.

        This method is the preferred entry point for the WebSocket handler
        because it avoids all OpenCV/MediaPipe video-capture overhead.

        Args:
            raw_landmarks: Landmark payload in one of two formats:

                * **Dict** (named keys) — e.g.::

                      {
                          "right_shoulder": [x, y, z, v],
                          "left_elbow":     [x, y, z, v],
                          ...
                      }

                  Values may be a 3- or 4-element list ``[x, y, z]`` /
                  ``[x, y, z, v]``, or a dict ``{"x": …, "y": …, "z": …}``.

                * **List** (indexed, length 33) — e.g.::

                      [{"x": 0.5, "y": 0.3, "z": -0.1}, ...]

        Returns:
            A 3-tuple ``(features, feedback_message, jab_detected)`` where:

            * ``features`` – dict of computed metrics (including
              ``"tracking_state"`` and ``"frame_index"``), or ``None`` if
              the landmarks were insufficient.
            * ``feedback_message`` – human-readable coaching cue, or ``None``.
            * ``jab_detected`` – ``True`` when a complete jab cycle was
              recognised in this frame.
        """
        # ── 1. Build a 33-slot list of _LandmarkProxy objects ──────────
        proxies: list[_LandmarkProxy | None] = [None] * 33

        if isinstance(raw_landmarks, dict):
            for name, value in raw_landmarks.items():
                idx = _NAMED_TO_INDEX.get(name)
                if idx is None:
                    continue
                if isinstance(value, (list, tuple)):
                    x = float(value[0]) if len(value) > 0 else 0.0
                    y = float(value[1]) if len(value) > 1 else 0.0
                    z = float(value[2]) if len(value) > 2 else 0.0
                    v = float(value[3]) if len(value) > 3 else 0.0
                    proxies[idx] = _LandmarkProxy({"x": x, "y": y, "z": z, "v": v})
                elif isinstance(value, dict):
                    proxies[idx] = _LandmarkProxy(value)

        elif isinstance(raw_landmarks, list):
            for i, item in enumerate(raw_landmarks[:33]):
                if isinstance(item, dict):
                    proxies[i] = _LandmarkProxy(item)

        else:
            # Unknown format — treat as invalid.
            self.frame_idx += 1
            return None, None, False

        # ── 2. Quality gate ──────────────────────────────────
        # Hard discard: any required landmark below visibility threshold
        if not validate_frame(proxies):
            self.frame_idx += 1
            return None, "UBICA TU CUERPO EN EL CUADRO", False

        # ── 3. Feature extraction ───────────────────────────────────────
        features = extract_features(proxies, prev_features=self.prev_features)
        if not features:
            self.frame_idx += 1
            return None, None, False

        # ── 4. Jitter smoothing + motion augmentation ──────────────────
        # Smooth raw features before augmentation so velocities are stable
        features = smooth_features(features, self.prev_features)
        self.prev_features = features
        features = self._augment_with_motion(proxies, features)

        # ── 5. Jab tracking ─────────────────────────────────────────────
        jab_event = self.jab_tracker.update(features, self.frame_idx)
        if jab_event:
            self.last_jab_event = jab_event

        # ── 6. Feedback ──────────────────────────────────────────────────
        feedback_msg = self.feedback_engine.compare_realtime(features)
        if feedback_msg is None:
            feedback_msg = self._heuristic_feedback(features, jab_event)

        # ── 7. Tracking-lock check ───────────────────────────────────────
        torso_indices = [11, 12, 23, 24]
        is_tracking_locked = all(
            proxies[i] is not None and proxies[i].visibility > 0.65
            for i in torso_indices
        )

        if not is_tracking_locked:
            feedback_msg = "UBICA TU CUERPO EN EL CUADRO"
            jab_event = None

        features["tracking_state"] = "tracking" if is_tracking_locked else "searching"

        self.frame_idx += 1
        return features, feedback_msg, bool(jab_event)

    def process_video(self, video_path, return_frames=False):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError("No se pudo abrir el video.")

        self.reset_state()
        fps = cap.get(cv2.CAP_PROP_FPS)
        self.set_fps(fps if fps and fps > 0 else None)

        annotated_frames = []
        feature_list = []
        feedback_list = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Using 5 values now
            annotated, features, feedback, _, _ = self.process_frame(frame)

            if return_frames:
                annotated_frames.append(annotated)

            feature_list.append(features)
            feedback_list.append(feedback)

        cap.release()

        if not return_frames:
            annotated_frames = []

        return annotated_frames, feature_list, feedback_list

    def _augment_with_motion(self, landmarks, features):
        # Track BOTH wrists — pick the faster one as "hand_speed".
        wrist_l = np.array(
            [landmarks[15].x, landmarks[15].y, landmarks[15].z], dtype=float,
        )
        wrist_r = np.array(
            [landmarks[16].x, landmarks[16].y, landmarks[16].z], dtype=float,
        )

        speed_l = 0.0
        speed_r = 0.0
        if self.prev_wrist_l is not None:
            speed_l = float(np.linalg.norm(wrist_l - self.prev_wrist_l) / self.dt)
        if self.prev_wrist_r is not None:
            speed_r = float(np.linalg.norm(wrist_r - self.prev_wrist_r) / self.dt)
        hand_speed = max(speed_l, speed_r)

        # Retraction speed — track best extension across both hands.
        ext_left = features["forward_extent_left"]
        ext_right = features["forward_extent_right"]
        # Also include elbow-angle extension so retraction works for front-cam.
        elbow_l = features.get("elbow_angle_left", 90.0)
        elbow_r = features.get("elbow_angle_right", 90.0)
        arm_ext_l = max(0.0, (elbow_l - 90.0)) / 90.0
        arm_ext_r = max(0.0, (elbow_r - 90.0)) / 90.0
        current_ext = max(ext_left, ext_right, arm_ext_l, arm_ext_r)

        retraction_speed = 0.0
        if self.prev_max_extent is not None:
            delta = current_ext - self.prev_max_extent
            if delta < 0:
                retraction_speed = float(abs(delta) / self.dt)

        augmented = dict(features)
        augmented["hand_speed"] = hand_speed
        augmented["retraction_speed"] = retraction_speed
        augmented["frame_index"] = self.frame_idx

        self.prev_wrist_l = wrist_l
        self.prev_wrist_r = wrist_r
        self.prev_max_extent = current_ext

        return augmented

    @staticmethod
    def _heuristic_feedback(features, jab_event):
        if jab_event:
            return "Buen golpe detectado."

        # Use best extension across both hands (X-displacement + elbow angle)
        fwd = max(
            features.get("forward_extent_left", 0.0),
            features.get("forward_extent_right", 0.0),
        )
        elbow_l = features.get("elbow_angle_left", 90.0)
        elbow_r = features.get("elbow_angle_right", 90.0)
        arm_ext = max(
            max(0.0, (elbow_l - 90.0)) / 90.0,
            max(0.0, (elbow_r - 90.0)) / 90.0,
        )
        extent = max(fwd, arm_ext)
        speed = features.get("hand_speed", 0.0)

        if extent < 0.35:
            return "Extiende el brazo con más fuerza."
        if speed < 0.4:
            return "Ejecuta el golpe con mayor velocidad."
        return None


class BoxingJabAnalyzer:
    """Contenedor retrocompatible que usa BoxingJabTracker internamente."""

    def __init__(self, baseline=None):
        self.tracker = BoxingJabTracker(baseline=baseline)

    def process_frame(self, frame, frame_idx=None):
        return self.tracker.process_frame(frame)

    def process_video(self, video_path):
        frames, features_list, feedback_list = self.tracker.process_video(
            video_path,
            return_frames=True,
        )
        return {
            "frames": frames,
            "features": features_list,
            "feedback": feedback_list,
            "jabs": self.tracker.jab_tracker.jabs,
        }
