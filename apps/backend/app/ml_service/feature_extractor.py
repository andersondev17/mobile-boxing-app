import numpy as np

EPS = 1e-6


def extract_angle(a, b, c):
    """Return the angle (in degrees) at point b between points a-b-c."""
    a = np.array([a.x, a.y, a.z], dtype=float)
    b = np.array([b.x, b.y, b.z], dtype=float)
    c = np.array([c.x, c.y, c.z], dtype=float)

    ba = a - b
    bc = c - b

    denom = (np.linalg.norm(ba) * np.linalg.norm(bc)) + EPS
    cosang = np.dot(ba, bc) / denom
    angle = np.degrees(np.arccos(np.clip(cosang, -1.0, 1.0)))
    return float(angle)


def extract_features(landmarks):
    """
    Compute per-frame static measurements that feed the jab tracker.

    Returns a dict with elbow flexion and forward reach (normalized Mediapipe coords).
    """
    if len(landmarks) <= 15:
        return None

    shoulder = landmarks[11]
    elbow = landmarks[13]
    wrist = landmarks[15]

    elbow_angle = extract_angle(shoulder, elbow, wrist)
    forward_extent = wrist.x - shoulder.x

    return {
        "elbow_angle": float(elbow_angle),
        "forward_extent": float(forward_extent),
    }
