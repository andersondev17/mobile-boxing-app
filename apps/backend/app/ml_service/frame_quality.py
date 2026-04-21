"""Frame quality validator and jitter smoother for the ML pipeline.

Rules (hard, non-negotiable):
  1. Any required landmark with visibility < VIS_THRESHOLD  → frame discarded.
  2. Frames where fewer than MIN_LANDMARKS are present       → frame discarded.
  3. Jitter: exponential moving average (α=0.7) applied to all numeric features.

This module is stateless. State (prev_features) is owned by the tracker.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Landmarks required for core biomechanical computation
REQUIRED_LANDMARK_INDICES: frozenset[int] = frozenset({
    11, 12,  # shoulders
    13, 14,  # elbows
    15, 16,  # wrists
    23, 24,  # hips
})

VIS_THRESHOLD: float = 0.65
SMOOTH_ALPHA: float = 0.7   # weight for current frame; (1-α) for previous


def validate_frame(
    landmarks: list,
    *,
    required: frozenset[int] = REQUIRED_LANDMARK_INDICES,
    threshold: float = VIS_THRESHOLD,
) -> bool:
    """Return True only when ALL required landmarks meet the visibility threshold.

    Args:
        landmarks: 33-slot list of landmark proxy objects (may contain None).
        required:  Set of landmark indices that must pass visibility check.
        threshold: Minimum visibility score (inclusive).

    Returns:
        True → frame is usable; False → frame must be discarded.
    """
    for idx in required:
        if idx >= len(landmarks):
            logger.debug("Frame rejected: landmark index %d out of range (len=%d)", idx, len(landmarks))
            return False
        lm = landmarks[idx]
        if lm is None:
            logger.debug("Frame rejected: landmark %d is None", idx)
            return False
        vis = float(getattr(lm, "visibility", 0.0))
        if vis < threshold:
            logger.debug("Frame rejected: landmark %d visibility=%.3f < %.2f", idx, vis, threshold)
            return False
    return True


def smooth_features(
    current: dict,
    previous: Optional[dict],
    *,
    alpha: float = SMOOTH_ALPHA,
) -> dict:
    """Apply exponential moving average to reduce inter-frame jitter.

    Only numeric (float/int) values are smoothed. Non-numeric keys
    (e.g., 'tracking_state', 'frame_index') are left untouched.

    Formula: smoothed = alpha * current + (1 - alpha) * previous

    Args:
        current:  Feature dict for the current frame.
        previous: Feature dict for the immediately preceding frame, or None.
        alpha:    Weight for the current frame. Default 0.7 (70% current).

    Returns:
        New dict with smoothed numeric values.
    """
    if previous is None:
        return dict(current)

    smoothed = {}
    for key, val in current.items():
        if isinstance(val, (int, float)) and key in previous:
            prev_val = previous[key]
            if isinstance(prev_val, (int, float)):
                smoothed[key] = alpha * float(val) + (1.0 - alpha) * float(prev_val)
                continue
        # Non-numeric or key not in previous → pass through unchanged
        smoothed[key] = val

    return smoothed
