import numpy as np

# Lazy MediaPipe import
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

# Mapeo de nombres a IDs de Mediapipe
LANDMARK_INDEX = {
    "nose": 0,
    "left_eye": 2,
    "right_eye": 5,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
}

def get_landmark_xy(landmarks, name):
    idx = LANDMARK_INDEX.get(name)
    if idx is None:
        return None

    lm = landmarks[idx]
    return np.array([lm.x, lm.y])


def distance(a, b):
    return float(np.linalg.norm(a - b))


def angle(a, b, c):
    ba = a - b
    bc = c - b
    cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    ang = np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))
    return float(ang)

