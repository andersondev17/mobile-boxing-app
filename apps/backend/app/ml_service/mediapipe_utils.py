"""
Shared MediaPipe import helper.

Encapsulates the multi-path fallback needed across different MediaPipe
versions (``mp.solutions.*`` vs ``mediapipe.python.solutions.*``).

Usage::

    from ml_service.mediapipe_utils import mp_pose, mp_drawing, mp_drawing_styles

Raises ``RuntimeError`` (with the original exception chained) when MediaPipe
is not installed or the expected symbols cannot be found.
"""

try:
    import mediapipe as mp

    # ── pose ──────────────────────────────────────────────────────────────
    try:
        mp_pose = mp.solutions.pose
    except AttributeError:
        try:
            from mediapipe.python.solutions import pose as mp_pose  # type: ignore[no-redef]
        except ImportError:
            import mediapipe.python.solutions.pose as mp_pose  # type: ignore[no-redef]

    # ── drawing_utils ─────────────────────────────────────────────────────
    try:
        mp_drawing = mp.solutions.drawing_utils
    except AttributeError:
        try:
            from mediapipe.python.solutions import drawing_utils as mp_drawing  # type: ignore[no-redef]
        except ImportError:
            import mediapipe.python.solutions.drawing_utils as mp_drawing  # type: ignore[no-redef]

    # ── drawing_styles ────────────────────────────────────────────────────
    try:
        mp_drawing_styles = mp.solutions.drawing_styles
    except AttributeError:
        try:
            from mediapipe.python.solutions import drawing_styles as mp_drawing_styles  # type: ignore[no-redef]
        except ImportError:
            import mediapipe.python.solutions.drawing_styles as mp_drawing_styles  # type: ignore[no-redef]

except (ImportError, AttributeError) as _exc:
    raise RuntimeError(
        f"MediaPipe is not available or its API has changed: {_exc}"
    ) from _exc

__all__ = ["mp_pose", "mp_drawing", "mp_drawing_styles"]
