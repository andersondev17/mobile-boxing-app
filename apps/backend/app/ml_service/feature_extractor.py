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
    # Need at least up to index 24 (right hip).
    if landmarks is None or len(landmarks) < 25:
        return None

    # Unpack the eight landmarks used across all features.
    shoulder_l = landmarks[11]   # left shoulder
    shoulder_r = landmarks[12]   # right shoulder
    elbow_l    = landmarks[13]   # left elbow
    elbow_r    = landmarks[14]   # right elbow
    wrist_l    = landmarks[15]   # left wrist
    wrist_r    = landmarks[16]   # right wrist
    hip_l      = landmarks[23]   # left hip
    hip_r      = landmarks[24]   # right hip

    # ── elbow_angle_left ─────────────────────────────────────────────────
    if _vis_ok(shoulder_l) and _vis_ok(elbow_l) and _vis_ok(wrist_l):
        elbow_angle_left = extract_angle(shoulder_l, elbow_l, wrist_l)
    else:
        elbow_angle_left = 0.0

    # ── elbow_angle_right ────────────────────────────────────────────────
    if _vis_ok(shoulder_r) and _vis_ok(elbow_r) and _vis_ok(wrist_r):
        elbow_angle_right = extract_angle(shoulder_r, elbow_r, wrist_r)
    else:
        elbow_angle_right = 0.0

    # ── forward_extent_left ──────────────────────────────────────────────
    # Positive value = wrist is in front of (to the right of) the shoulder.
    if _vis_ok(wrist_l) and _vis_ok(shoulder_l):
        forward_extent_left = float(wrist_l.x - shoulder_l.x)
    else:
        forward_extent_left = 0.0

    # ── forward_extent_right ─────────────────────────────────────────────
    # Sign reversed: right cross extends to the *left* in MediaPipe coords.
    if _vis_ok(wrist_r) and _vis_ok(shoulder_r):
        forward_extent_right = float(shoulder_r.x - wrist_r.x)
    else:
        forward_extent_right = 0.0

    # ── shoulder_rotation ────────────────────────────────────────────────
    # Depth difference between the two shoulders captures axial rotation.
    if _vis_ok(shoulder_r) and _vis_ok(shoulder_l):
        raw_shoulder_rot = abs(float(shoulder_r.z) - float(shoulder_l.z))
    else:
        raw_shoulder_rot = 0.0

    if prev_features is not None and "shoulder_rotation" in prev_features:
        shoulder_rotation = 0.7 * raw_shoulder_rot + 0.3 * float(prev_features["shoulder_rotation"])
    else:
        shoulder_rotation = raw_shoulder_rot

    # ── hip_rotation ─────────────────────────────────────────────────────
    if _vis_ok(hip_r) and _vis_ok(hip_l):
        raw_hip_rot = abs(float(hip_r.z) - float(hip_l.z))
    else:
        raw_hip_rot = 0.0

    if prev_features is not None and "hip_rotation" in prev_features:
        hip_rotation = 0.7 * raw_hip_rot + 0.3 * float(prev_features["hip_rotation"])
    else:
        hip_rotation = raw_hip_rot

    # ── guard_distance ───────────────────────────────────────────────────
    # 3-D Euclidean distance between the two wrists (how wide the guard is).
    if _vis_ok(wrist_l) and _vis_ok(wrist_r):
        guard_distance = float(np.sqrt(
            (wrist_l.x - wrist_r.x) ** 2
            + (wrist_l.y - wrist_r.y) ** 2
            + (wrist_l.z - wrist_r.z) ** 2
        ))
    else:
        guard_distance = 0.0

    # ── wrist_lateral_displacement ───────────────────────────────────────
    # Absolute vertical (y) offset of left wrist from left shoulder.
    # In MediaPipe coords y increases downward, so a raised elbow/wrist gives
    # a small (or negative) difference — useful for hook detection.
    if _vis_ok(wrist_l) and _vis_ok(shoulder_l):
        wrist_lateral_displacement = abs(float(wrist_l.y) - float(shoulder_l.y))
    else:
        wrist_lateral_displacement = 0.0

    return {
        "elbow_angle_left": float(elbow_angle_left),
        "elbow_angle_right": float(elbow_angle_right),
        "forward_extent_left": float(forward_extent_left),
        "forward_extent_right": float(forward_extent_right),
        "shoulder_rotation": float(shoulder_rotation),
        "hip_rotation": float(hip_rotation),
        "guard_distance": float(guard_distance),
        "wrist_lateral_displacement": float(wrist_lateral_displacement),
    }
