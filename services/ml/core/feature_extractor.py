import numpy as np

EPS = 1e-6

# Minimum visibility threshold — features that depend on a landmark below
# this value are zeroed out instead of being computed from noisy data.
_VIS_THRESHOLD = 0.65


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


def _vis_ok(landmark) -> bool:
    """Return True when the landmark has sufficient visibility."""
    return landmark is not None and float(getattr(landmark, "visibility", 0.0)) >= _VIS_THRESHOLD


def extract_features(landmarks, prev_features: dict | None = None) -> dict | None:
    """Compute per-frame biomechanical features for boxing technique analysis.

    Requires at least 25 landmarks (indices 0-24) to be present in the list.
    Any feature whose contributing landmark(s) have visibility < 0.65 is set
    to 0.0 rather than being computed from unreliable data.

    Args:
        landmarks: Sequence of landmark objects that expose ``.x``, ``.y``,
            ``.z``, and ``.visibility`` attributes.  Compatible with both
            MediaPipe ``NormalizedLandmarkList`` and ``_LandmarkProxy``.
        prev_features: Feature dict returned for the immediately preceding
            frame.  Used to apply lightweight temporal smoothing (2-frame
            approximation) to ``shoulder_rotation`` and ``hip_rotation``.
            Pass ``None`` (default) when no previous frame is available.

    Returns:
        Dict with 8 float features, or ``None`` if the landmarks list is too
        short to extract any meaningful data.
    """
    # Need at least up to index 28 (right knee).
    if landmarks is None or len(landmarks) < 29:
        return None

    # Unpack landmarks
    nose       = landmarks[0]
    shoulder_l = landmarks[11]   # left shoulder
    shoulder_r = landmarks[12]   # right shoulder
    elbow_l    = landmarks[13]   # left elbow
    elbow_r    = landmarks[14]   # right elbow
    wrist_l    = landmarks[15]   # left wrist
    wrist_r    = landmarks[16]   # right wrist
    hip_l      = landmarks[23]   # left hip
    hip_r      = landmarks[24]   # right hip
    knee_l     = landmarks[25]   # left knee
    knee_r     = landmarks[26]   # right knee
    ankle_l    = landmarks[27]   # left ankle
    ankle_r    = landmarks[28]   # right ankle

    # ── elbow_angle_left/right (existing) ────────────────────────────────
    elbow_angle_left = extract_angle(shoulder_l, elbow_l, wrist_l) if _vis_ok(shoulder_l) and _vis_ok(elbow_l) and _vis_ok(wrist_l) else 0.0
    elbow_angle_right = extract_angle(shoulder_r, elbow_r, wrist_r) if _vis_ok(shoulder_r) and _vis_ok(elbow_r) and _vis_ok(wrist_r) else 0.0

    # ── forward_extent_left/right (existing) ──────────────────────────────
    forward_extent_left = float(wrist_l.x - shoulder_l.x) if _vis_ok(wrist_l) and _vis_ok(shoulder_l) else 0.0
    forward_extent_right = float(shoulder_r.x - wrist_r.x) if _vis_ok(wrist_r) and _vis_ok(shoulder_r) else 0.0

    # ── torso_rotation (CRITICAL) ─────────────────────────────────────────
    # Relative rotation between shoulder line and hip line in the Z-plane.
    if all(map(_vis_ok, [shoulder_l, shoulder_r, hip_l, hip_r])):
        shoulder_z = float(shoulder_r.z - shoulder_l.z)
        hip_z = float(hip_r.z - hip_l.z)
        torso_rotation = abs(shoulder_z - hip_z)
    else:
        torso_rotation = 0.0

    # ── vertical_displacement ────────────────────────────────────────────
    # Tracking the height (y) of the head relative to the start or hips.
    if _vis_ok(nose) and _vis_ok(hip_l) and _vis_ok(hip_r):
        hip_center_y = (hip_l.y + hip_r.y) / 2.0
        vertical_displacement = float(hip_center_y - nose.y)
    else:
        vertical_displacement = 0.0

    # ── knee_flexion (left) ──────────────────────────────────────────────
    if all(map(_vis_ok, [hip_l, knee_l, ankle_l])):
        knee_flexion = extract_angle(hip_l, knee_l, ankle_l)
    else:
        knee_flexion = 180.0 # fully extended default

    # ── weight_transfer ──────────────────────────────────────────────────
    # Horizontal (x) offset of hip center relative to the midpoint of ankles.
    if all(map(_vis_ok, [hip_l, hip_r, ankle_l, ankle_r])):
        hip_cx = (hip_l.x + hip_r.x) / 2.0
        ankle_cx = (ankle_l.x + ankle_r.x) / 2.0
        weight_transfer = float(hip_cx - ankle_cx)
    else:
        weight_transfer = 0.0

    # ── Temporal Smoothing ───────────────────────────────────────────────
    def _smooth(val, key):
        if prev_features and key in prev_features:
            return 0.7 * val + 0.3 * float(prev_features[key])
        return val

    features = {
        "elbow_angle_left": float(elbow_angle_left),
        "elbow_angle_right": float(elbow_angle_right),
        "forward_extent_left": float(forward_extent_left),
        "forward_extent_right": float(forward_extent_right),
        "torso_rotation": _smooth(float(torso_rotation), "torso_rotation"),
        "vertical_displacement": _smooth(float(vertical_displacement), "vertical_displacement"),
        "knee_flexion": _smooth(float(knee_flexion), "knee_flexion"),
        "weight_transfer": _smooth(float(weight_transfer), "weight_transfer"),
    }

    return features







