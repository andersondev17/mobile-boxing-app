import cv2
import mediapipe as mp
import numpy as np
from dataclasses import dataclass

from .feature_extractor import extract_features
from .feedback_engine import FeedbackEngine


@dataclass
class JabEvent:
    frame_idx: int
    hand_speed: float = 0.0
    extension: float = 0.0
    retraction_speed: float = 0.0
    result: str = "jab_detected"


class JabTracker:
    def __init__(self, threshold_extension=0.22, threshold_speed=2.5):
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

        ext = features.get("forward_extent", 0.0)
        speed = features.get("hand_speed", 0.0)
        retract = features.get("retraction_speed", 0.0)

        if self.state == "idle":
            if ext > self.threshold_extension and speed > self.threshold_speed:
                self.state = "extended"
            return None

        if self.state == "extended":
            if retract > 1.5 and ext < 0.15:
                self.state = "idle"
                jab_event = JabEvent(frame_idx, speed, ext, retract)
                self.jabs.append(jab_event)
                return jab_event

        return None


class BoxingJabTracker:
    DEFAULT_FPS = 30.0

    def __init__(self, baseline=None, fps=DEFAULT_FPS):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
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
        self.prev_wrist = None
        self.prev_forward_extent = None
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
            return annotated, None, None, None

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
            return annotated, None, None, None

        features = self._augment_with_motion(landmarks, features)
        jab_event = self.jab_tracker.update(features, self.frame_idx)
        if jab_event:
            self.last_jab_event = jab_event

        feedback_msg = self.feedback_engine.compare(features)
        if feedback_msg is None:
            feedback_msg = self._heuristic_feedback(features, jab_event)

        self.frame_idx += 1
        return annotated, features, feedback_msg, jab_event

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

            annotated, features, feedback, _ = self.process_frame(frame)

            if return_frames:
                annotated_frames.append(annotated)

            feature_list.append(features)
            feedback_list.append(feedback)

        cap.release()

        if not return_frames:
            annotated_frames = []

        return annotated_frames, feature_list, feedback_list

    def _augment_with_motion(self, landmarks, features):
        wrist = np.array(
            [landmarks[15].x, landmarks[15].y, landmarks[15].z],
            dtype=float,
        )

        hand_speed = 0.0
        if self.prev_wrist is not None:
            hand_speed = float(np.linalg.norm(wrist - self.prev_wrist) / self.dt)

        retraction_speed = 0.0
        if self.prev_forward_extent is not None:
            delta_extent = features["forward_extent"] - self.prev_forward_extent
            if delta_extent < 0:
                retraction_speed = float(abs(delta_extent) / self.dt)

        augmented = dict(features)
        augmented["hand_speed"] = hand_speed
        augmented["retraction_speed"] = retraction_speed
        augmented["frame_index"] = self.frame_idx

        self.prev_wrist = wrist
        self.prev_forward_extent = features["forward_extent"]

        return augmented

    @staticmethod
    def _heuristic_feedback(features, jab_event):
        if jab_event:
            return "Buen jab detectado."

        extent = features.get("forward_extent", 0.0)
        speed = features.get("hand_speed", 0.0)

        if extent < 0.15:
            return "Lleva la mano mas adelante."
        if speed < 0.8:
            return "Ejecuta el jab con mayor velocidad."
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
